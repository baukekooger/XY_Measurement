import csv
import time
import numpy as np
import pyvisa as visa
import logging
import pyvisa.errors


def list_available_devices():
    return visa.ResourceManager().list_resources()


class PowerMeter:
    """
    Python Class for the Thorlabs PM100A powermeter with basic functionalities
    """

    def __init__(self, name='USB0::0x1313::0x8079::P1002333::INSTR'):
        self.logger_instrument = logging.getLogger('ínstrument.PowerMeter')
        self.logger_instrument.info('init PowerMeter')
        self.name = name
        self.pm = None
        self.connected = False
        self.measuring = False

    def connect_device(self):
        try:
            self.pm = visa.ResourceManager().open_resource(self.name)
            self.connected = True
            # Set spectrometer to power mode
            self.pm.write('conf:pow')
        except pyvisa.errors.VisaIOError as error:
            self.logger_instrument.error('Could not connect powermeter')
            raise ConnectionError('No powermeter found')

    @property
    def wavelength(self):
        """ Current wavelength the powermeter is scanning on [nm]"""
        wavelength = self.pm.query_ascii_values("sense:corr:wav?")[0]
        return wavelength

    @wavelength.setter
    def wavelength(self, value):
        self.logger_instrument.info(f'setting the powermeter wavelength to {value}')
        self.pm.write(f'sense:corr:wav {value}')

    def set_wavelength(self, value):
        """ Callable to set the wavelength. """
        self.wavelength = value

    @property
    def averageing(self):
        """ returns the number of measurements being averaged over
            one measurement takes approximately 3 ms
            """
        averaging = int(self.pm.query('sens:aver:coun?').strip())
        return averaging

    @averageing.setter
    def averageing(self, value):
        """ sets the number of values being averaged over
            one measurement takes approximately 3 ms
            timeout not automatically adjusted
        """
        value = int(value)
        self.pm.write(f'sens:aver:coun {value}')

    @property
    def timeout(self):
        """ returns the timeout of the PM in ms """
        return self.pm.timeout

    @timeout.setter
    def timeout(self, value):
        """ sets the value of the timeout, value in seconds """
        value = int(value * 1000)
        self.pm.timeout = value

    @property
    def sensor(self):
        """ Return information about the connected sensor. """
        sensorinfo = self.pm.query('syst:sens:idn?').strip().split(',')
        model = sensorinfo[0]
        sn = sensorinfo[1]
        caldate = sensorinfo[2]
        sensor = {'Model': model, 'Serial_Number': sn, 'Calibration_Date': caldate}
        return sensor

    @property
    def device(self):
        """ Return the powermeter model. """
        info = self.pm.query('*IDN?').strip().split(',')
        brand = info[0]
        model = info[1]
        sn = info[2]
        firmware = info[3]
        device_info = {'Brand': brand, 'Model': model, 'Serial_Number': sn, 'Firmware_Version': firmware}
        return device_info

    def read_power(self):
        power = self.pm.query_ascii_values('read?')[0]
        return power

    def zero_device(self):
        """ initialises blocking procedure, returns when done """
        self.pm.write('sens:corr:coll:zero:init')
        while int(self.pm.query('sens:corr:coll:zero:stat?').strip()):
            time.sleep(0.2)

    def reset_default(self):
        # returns unit to default condition
        self.pm.write('*RST')
        self.pm.write('*CLS')

    @property
    def sensitivity_photodiode(self):
        """ queries the thermopile sensor sensitivity at the current wavelength """
        try:
            sensitivity = self.pm.query('sens:corr:pow:pdio:resp?').strip()
            return sensitivity
        except pyvisa.errors.VisaIOError:
            self.logger_instrument.info('Cannot read photodiode response, no thermopile connected')

    @property
    def sensitivity_thermopile(self):
        """ queries the thermopile sensor sensitivity at the current wavelength """
        try:
            sensitivity = self.pm.query('sens:corr:pow:ther:resp?').strip()
            return sensitivity
        except pyvisa.errors.VisaIOError:
            self.logger_instrument.info('Cannot read thermopile response, no thermopile connected')

    @property
    def autorange(self):
        """ reads if the autoranging is on in power mode"""
        autorange = int(self.pm.query('sens:pow:rang:auto?').strip())
        autorange = bool(autorange)
        return autorange

    @autorange.setter
    def autorange(self, value):
        """ turns autorange on or off, accepts boolean"""
        integervalue = int(value)
        self.pm.write(f'sens:pow:rang:auto {integervalue}')

    @property
    def accelerator(self):
        """ queries if the accelerator circuit is turned on """
        try:
            acceleratorstatus = self.pm.query('inp:ther:acc:state?').strip()
            return bool(int(acceleratorstatus))
        except pyvisa.errors.VisaIOError:
            self.logger_instrument.info('Cannot read accelerator status, no thermopile connected')

    @accelerator.setter
    def accelerator(self, value):
        """ turns the accelerator circuit of or on. accepts boolean value """
        intvalue = int(value)
        try:
            self.pm.write(f'inp:ther:acc:state {intvalue}')
        except pyvisa.errors.VisaIOError:
            self.logger_instrument.info('Cannot set accelerator, no thermopile connected')

    @property
    def thermopile_timeconstant(self):
        """ reads the thermopile time constant """
        try:
            tau = self.pm.query('inp:ther:acc:tau?').strip()
            return tau
        except pyvisa.errors.VisaIOError:
            self.logger_instrument.info('Cannot read timeconstant, no thermopile connected')

    def set_sensitivity_correction(self, file):
        """
        Set the correction for the spectrometer sensitivity and all other optics within the used setup.
        The sensitivity file (.csv) is formatted as following:
        CREATION DATE: <<Date of calibration>>
        Wavelength (nm), Intensity (a.u.)
        wl_1, I_1
        ..., ...

        :param file: location of the correction file
        :return: dict: {'wavelengths': [...], 'intensity': [...]} a dict of the correction file
        """
        if not file:
            self.sensitivity_correction = None
            return None
        sensitivity_correction = {'wavelengths': [], 'intensity': []}
        with open(file) as correction_file:
            correction_reader = csv.reader(correction_file, delimiter=',')
            for nrow, row in enumerate(correction_reader):
                if nrow in [0, 1]:
                    continue
                sensitivity_correction['wavelengths'].append(row[0])
                sensitivity_correction['intensity'].append(row[1])
        return sensitivity_correction

    def disconnect(self):
        self.pm.close()
        self.connected = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def __repr__(self):
        return self.pm.query('*IDN?')


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers
    pathlogging = Path(__file__).parent.parent.parent / 'loggingconfig.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)