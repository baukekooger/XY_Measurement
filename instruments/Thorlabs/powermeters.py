import csv
import time

import numpy as np
import visa
import logging


def list_available_devices():
    return visa.ResourceManager().list_resources(query='?*P0013932::INSTR')


class PM100D:
    """
    Thorlabs PM100D Powermeter python interface

    Note that the _minimal_ value for the integration time is around 10 ms
    As 1 measurement takes ~1/3 ms. This will yield 300 averages.

    Directly controls the PM100D Powermeter through a VISA interface
    """
    def __init__(self, name='USB0::0x1313::0x8078::P0013932::INSTR', average_time=500, integration_time=30,
                 timeout=1, sensitivity_correction=None):
        self.handle = visa.ResourceManager().open_resource(name)  # visa handle to the actual powermeter
        # Set spectrometer to power mode
        self.handle.write('conf:pow')
        self.average_time = average_time
        self._integration_time = integration_time
        self.integration_time = integration_time
        self._timeout = timeout
        self.timeout = timeout
        self.sensitivity_correction = self.set_sensitivity_correction(sensitivity_correction)

        self.measuring = False

    @property
    def timeout(self):
        """Timeout [s] of the powermeter """
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value
        if self.handle:
            self.handle.timeout = value * 1000

    @property
    def wavelength(self):
        """ Current wavelength the powermeter is scanning on """
        wavelength = self.query_value("sense:corr:wav?")
        return wavelength

    @wavelength.setter
    def wavelength(self, value):
        self.write_value("sense:corr:wav", value)

    @property
    def integration_time(self):
        """ Duration of integration time in [ms] """
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value):
        self._integration_time = value
        # One measurement takes ~ 1/3 ms
        averages = round(self._integration_time * 3)
        self.write_value('sense:average:count', averages)

    def measure(self):
        """Measures incident power over the specified averaging time, with
        separate measurements stored for each integration time.

        Returns:
            dict: Dictionary as {'interval':   [list of times],
                                 'value':   [list of powers [W/s] ] }
        """
        if self.measuring:
            logging.warning('Measurement in progress, please wait.')
            return -1
        self.measuring = True
        self.handle.write('*CLS')  # Clear event queue
        measurement = {'times': [], 'power': []}
        start = time.time()
        while self.measuring:
            measurement['times'].extend([time.time()])
            measurement['power'].append(self.query_value("read?"))
            measurement['times'][-1].append(time.time())
            last = time.time()
            if (last - start) * 1000 >= self.average_time:
                self.measuring = False
        if self.sensitivity_correction:
            power = np.array(measurement['power'])
            correction = np.interp(self.wavelength, self.sensitivity_correction['wavelength'],
                                   self.sensitivity_correction['intensity'])
            measurement['power'] = list(power / correction)
        return measurement

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
        self.sensitivity_correction = sensitivity_correction
        return sensitivity_correction

    def query_value(self, command):
        if not self.connected:
            raise ConnectionError('Powermeter not connected, please connect first')
        v = None
        v = self.handle.query_ascii_values(command)[0]
        return v

    def write_value(self, command, value):
        if type(value) is int:
            self.handle.write(command + ' %d' % value)
        if type(value) is float:
            self.handle.write(command + ' %.2f' % value)
        else:
            self.handle.write(command + ' %s' % value)

    def close(self):
        self.handle.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        return self.handle.read('IDN?')