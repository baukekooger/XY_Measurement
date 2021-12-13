from ctypes import c_int, c_double, c_char_p, byref, windll
import time
import logging.config
import numpy
import win32com.client
import re
import asyncio
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QMutexLocker
from pathlib import Path
import os

# Adds laser dll library path to environment path
path_lib = Path(__file__).parent / 'lib64'
os.environ['PATH'] += os.pathsep + str(path_lib)


# Constants
MINIMUM_WAVELENGTH = 190
MAXIMUM_WAVELENGTH = 2300


def list_available_devices():
    devices = []
    pattern = re.compile('USB\\\\.*\\\\(FTZ.*)')
    for device in win32com.client.GetObject("winmgmts:").InstancesOf("Win32_USBHub"):
        print(device.DeviceID)
        if pattern.match(device.DeviceID):
            devices.append(pattern.match(device.DeviceID).groups()[0])
    return devices


class QLaser(QObject):
    """
    Ekspla NT230 OPO Laser control class as a Qobject
    
    Interfaces to control the Ekspla NT230 OPO laser through the EKSPLA REMOTECONTROL library over USB
    """

    measurement_complete = pyqtSignal(float, str, float, bool, bool)
    wavelength_signal = pyqtSignal(int)
    laser_stable = pyqtSignal()

    def __init__(self, waittime=0.05, polltime=0.1, timeout=10, parent=None):
        super().__init__(parent=parent)
        # device_name='FT5AOAQM'
        self.logger = logging.getLogger('Qinstrument.Qlaser')
        self.logger.info('init laser')
        self.connected = False
        self.mutex = QMutex(QMutex.Recursive)
        self.measuring = False
        self.waittime = waittime
        self.polltime = polltime
        self.timeout = timeout
        self.measuring = False
        self.handle = c_int()
        self.setpoint_wavelength = None
        path_dll = str(Path(__file__).parent / 'lib64/REMOTECONTROL64.dll')
        self.rcdll = windll.LoadLibrary(path_dll)

    @property
    def wavelength(self):
        """
            get/set wavelength of the EKSPLA laser in nm
                RANGE 190-2600 nm
                set wavelength : NT230.wavelength = 250.00
                get wavelength : wl = NT230.wavelength
        """

        dev = "MidiOPG:31"
        reg = "WaveLength"
        wavelength = self._get_register_double(dev, reg)
        if wavelength:
            self.logger.info(f'laser wavelength = {wavelength}')
            wavelength = int(wavelength)
            self.wavelength_signal.emit(wavelength)
        return wavelength

    @wavelength.setter
    def wavelength(self, wl):
        """
        Sets the wavelength of the laser. 
        """
        self.logger.info(f'Attempting to set the laser wavelength to {wl}')
        if wl < MINIMUM_WAVELENGTH:
            wl = MINIMUM_WAVELENGTH
            self.logger.warning(f'Exceeded wavelength range when attempting to set wavelength to {wl:.2f} nm. '
                                f'Wavelength set to minimum of to {MINIMUM_WAVELENGTH:.2f} nm')
        if wl > MAXIMUM_WAVELENGTH:
            wl = MAXIMUM_WAVELENGTH
            self.logger.warning(f'Exceeded wavelength range when attempting to set wavelength to {wl:.2f} nm. '
                                f'Wavelength set to maximum of to {MAXIMUM_WAVELENGTH:.2f} nm')

        dev = "MidiOPG:31"
        reg = "WaveLength"
        self._set_register_double(dev, reg, wl)
        self.wavelength_signal.emit(wl)
        #        #TODO Set motor to calibrated position from maximal intensity
        #        dev = "PBP2:35"
        #        reg = "Motor position"
        #        mot_pos = np.interp(wl, self.ls_mot[:,0], self.ls_mot[:,1])
        #        try:
        #            self.set_register_double(dev, reg, mot_pos)
        #        except LaserError as e:
        #            self.logger.warning('Register {} not recognized'.format(reg))

    async def set_wavelength(self, wl):
        """
        This method will sleep for `waittime` to move laser components.
        """
        self.wavelength = wl
        # Wait for waittime to allow the laser to settle
        asyncio.sleep(self.waittime)

    @property
    def output(self):
        """
        get/set status of the output enable
        """
        dev = "CPU8000:16"
        reg = "Power"
        output_enabled = self._get_register_double(dev, reg)
        self.logger.info(f'laser output = {output_enabled}')
        return bool(output_enabled)

    @output.setter
    def output(self, status):
        """
        setter of the output, true for enabled
        """
        self.logger.info(f'setting laser output to {status}')
        dev = "CPU8000:16"
        reg = "Power"
        self._set_register_double(dev, reg, int(status))

    @property
    def use_spectral_cleaning_unit(self):
        """
        get/set status of the Spectrum Cleaning Unit
        """
        dev = "MidiOPG:31"
        reg = "Configuration"
        SCU = self._get_register_double(dev, reg)
        self.logger.info(f'spectral cleaning unit status = {SCU}')
        return bool(SCU)

    @use_spectral_cleaning_unit.setter
    def use_spectral_cleaning_unit(self, status):
        self.logger.info(f'setting spectral cleaning unit status to {status}')
        dev = "MidiOPG:31"
        reg = "Configuration"
        self._set_register_double(dev, reg, int(status))

    @property
    def energylevel(self):
        """
            get/set energy level of the laser 
                level           : OFF, Adjust or MAX
                set energylevel : NT2300.energylevel = OFF
                get energylevel : el = NT2300.energylevel
        """
        dev = "CPU8000:16"
        reg = "Output Energy level"
        k = ['Off', 'Adjust', 'Max']
        energylevel = k[int(self._get_register_double(dev, reg))]
        self.logger.info(f'energy level  = {energylevel}')
        return energylevel

    @energylevel.setter
    def energylevel(self, level):
        self.logger.info(f'setting energy level to {level}')
        dev = "CPU8000:16"
        reg = "Output Energy level"
        levels = ['Off', 'Adjust', 'Max']
        if level in levels:
            level = levels.index(level)
        else:
            level = 0
        self._set_register_double(dev, reg, level)

    @property
    def power(self):
        """
            get the power of laser in Watt
                pw = NT230.power
        """
        dev = "11PMK:56"
        reg = "Power"
        power = self._get_register_double(dev, reg)
        self.logger.info(f'laser pump power = {power}')
        return power

    @property
    def status(self):
        """
            get the status of laser 
                [Off,Initiation,Tuning...,Ok.]
        """

        dev = "MidiOPG:31"
        reg = "Status"
        status = ['Off', 'Initiation', 'Tuning...', 'OK']
        status = status[int(self._get_register_double(dev, reg))]
        self.logger.info(f'laser status = {status}')
        return status

    def _set_register_double(self, dev, reg, val):
        """ Set a register value. """

        self.logger.debug(f'setting laser register double, dev = {dev}, reg = {reg}, val = {val}')
        d = c_char_p(bytes(dev, 'utf-8'))
        r = c_char_p(bytes(reg, 'utf-8'))
        v = c_double(val)
        # Try, if we fail, try again
        e = self.rcdll.rcSetRegFromDoubleA2(self.handle, d, r, v, c_int(0))
        if not e == 0:
            self.logger.warning('An error occurred during Laser communication, reattempting...')
            time.sleep(self.polltime)
            e = self.rcdll.rcSetRegFromDoubleA2(self.handle, d, r, v, c_int(0))
        self._is_error(e)

    def _get_register_double(self, dev, reg):
        """ Retrieve a register value. """
        self.logger.debug(f'getting laser register double, dev = {dev}, reg = {reg}')
        d = c_char_p(bytes(dev, 'utf-8'))
        r = c_char_p(bytes(reg, 'utf-8'))
        resp = c_double()
        # Try, if we fail, try again
        e = self.rcdll.rcGetRegAsDouble2(self.handle, d, r, byref(resp),
                                   self.timeout, None)
        if not e == 0:
            self.logger.warning('An error occurred during Laser communication, reattempting...')
            time.sleep(self.polltime)
            e = self.rcdll.rcGetRegAsDouble2(self.handle, d, r, byref(resp),
                                       self.timeout, None)
        self._is_error(e)
        return resp.value

    def _is_error(self, e):
        """
        Check if e is a number associated with a laser error.
        Raise the appropriate error for each error value other than e==0 (no error).
        """
        message = f'Laser - {LaserError.errorcodes[e]}'
        if e == 0:
            return
        elif e in [7]:
            self.logger.error(f'{message}')
            raise ConnectionError(message)
        elif e in [17, 18]:
            self.logger.warning(f'Laser connection - {message}')
        elif e in [11, 12, 13]:
            self.logger.warning(f'{message}')
            raise ValueError(message)
        elif e == 8:
            self.logger.error(f'{message}')
            raise TimeoutError(message)
        else:
            self.logger.error(f'{message}')
            raise LaserError(e)

    @pyqtSlot()
    def connect(self, connection_type=0, device_name='FT5AOAQM'):
        """
        Connect to laser.
        """
        self.logger.info('connecting to laser')
        path_config = path_lib / 'REMOTECONTROL.CSV'
        c_path = c_char_p(bytes(str(path_config), 'utf-8'))
        c_devicename = c_char_p(bytes(device_name, 'utf-8'))
        self._is_error(self.rcdll.rcConnect2(byref(self.handle), connection_type, c_devicename, c_path))
        self.connected = True
        self.logger.info('laser connected')

    @pyqtSlot()
    def disconnect(self):
        """ Turns the laser off and disconnects """
        self.logger.info('disconnecting from laser')
        self.measuring = False
        self.energylevel = 'Off'
        self._is_error(self.rcdll.rcDisconnect2(self.handle))

    @pyqtSlot()
    def measure(self):
        """Measure the current values of the laser.
        A single measurement should last around 0.25 seconds.
        
        Returns: 
            | float: wavelength
            | str: energylevel
            | float: power
            | bool: stability of the laser
        """
        self.logger.info('Measuring laser parameters. ')
        self.measuring = True
        with(QMutexLocker(self.mutex)):
            self.logger.info('Measuring laser...')
            wavelength = self.wavelength
            energylevel = self.energylevel
            power = self.power
            stable = self.is_stable()
            output = self.output
        self.measuring = False
        self.measurement_complete.emit(wavelength, energylevel, power, stable, output)
        return wavelength, energylevel, power, stable, output

    @pyqtSlot()
    def is_stable(self):
        """ Returns True if no fluctuation in Power higher than 5% occurs
        between now and 5 polltimes
        
        Returns:
            (bool): True/False depending on stability
        """
        self.logger.debug('measuring if laser stable')
        p = []
        for _ in range(5):
            p.append(self.power)
            time.sleep(self.polltime)
        return numpy.std(p) / numpy.mean(p) < 0.05

    @pyqtSlot()
    def set_wavelength_to_setpoint(self):
        """
        Set the wavelength to the setpoint. Setpoint must be defined before calling the function.

        Return only when the laser has reached a stable state, emit a signal when ready.
        """
        self.wavelength = self.setpoint_wavelength
        time.sleep(0.1)
        while not self.is_stable():
            time.sleep(0.1)
        self.logger.info(f'laser stable at {self.setpoint_wavelength}')
        self.laser_stable.emit()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connected:
            self.disconnect()

    def __repr__(self):
        if self.connected:
            """
                get serial number + model number and configuration file creation date
            """
            dev = "id()"
            ID = self._get_register_double(dev, "")
            return ID


class LaserError(Exception):
    """Exception raised for errors caused within Laser communication

        Attributes:
            errorcode -- errorcode provided by laser
    """
    errorcodes = ["Comunication succeeded, no error",
                  "End of registers list",
                  "No config file found",
                  "Wrong CSV file",
                  "Application provided return buffer is too short",
                  "No such device name",
                  "No such register name",
                  "Failed to connect",
                  "Timeout waiting for device answer",
                  "Register is read only",
                  "Register is not NV",
                  "Attempt to set value above upper limit",
                  "Attempt to set value below bottom limit",
                  "Attempt to set not allowed value",
                  "Register is not being logged",
                  "Not enough memory",
                  "No data in the queue yet",
                  "Already connected, please disconnect first",
                  "Not connected, please connect first"]

    def __init__(self, errorcode):
        Exception.__init__(self, self.errorcodes[errorcode])


class RangeError(LaserError):
    """ Exception raised for errors caused within Laser communication """
    pass


if __name__ == '__main__':
    import yaml
    import logging.config
    import logging.handlers
    pathlogging = Path(__file__).parent.parent.parent / 'logging/loggingconfig_testing.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)