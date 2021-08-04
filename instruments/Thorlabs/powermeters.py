import csv
import time
import numpy as np
import pyvisa as visa
import logging
from PyQt5.QtCore import QObject, QMutexLocker, QMutex, pyqtSignal, pyqtSlot
logging.basicConfig(level=logging.INFO)


def list_available_devices():
    return visa.ResourceManager().list_resources()


class QPowermeter(QObject):
    """
    Python interface for the Thorlabs PM100A powermeter as a Qobject
    """

    measurement_complete = pyqtSignal(float)
    measurement_parameters = pyqtSignal(int, int)

    def __init__(self, name='USB0::0x1313::0x8079::P1002333::INSTR', integration_time=30,
                 timeout=5000, sensitivity_correction=None, parent=None):
        super().__init__(parent=parent)
        self.mutex = QMutex(QMutex.Recursive)
        self.name = name
        self.pm = None
        self.connected = False
        self._integration_time = integration_time
        self._timeout = timeout
        self.sensitivity_correction = self.set_sensitivity_correction(sensitivity_correction)
        self.measuring = False

    def connect(self):
        self.pm = visa.ResourceManager().open_resource(self.name)
        self.connected = True
        self.integration_time = self._integration_time
        self.timeout = self._timeout
        # Set spectrometer to power mode
        self.pm.write('conf:pow')

    @property
    def timeout(self):
        """Timeout [ms] of the powermeter """
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value
        if self.pm:
            self.pm.timeout = value

    @property
    def wavelength(self):
        """ Current wavelength the powermeter is scanning on [nm]"""
        wavelength = self.pm.query_ascii_values("sense:corr:wav?")[0]
        return wavelength

    @wavelength.setter
    def wavelength(self, value):
        self.pm.write(f'sense:corr:wav {value}')
        self.emit_parameters()

    @property
    def integration_time(self):
        """ Duration of integration time in [ms] """
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value):
        # sets integration time and adjusts timeout accordingly
        if value >= self.timeout - 100:
            self.timeout = value + 5000
        self._integration_time = value
        # One measurement takes ~ 1/3 ms
        averages = round(self._integration_time * 3)
        self.pm.write(f'sense:average:count {int(averages)}')
        self.emit_parameters()

    def measure(self):
        # performs mutex locked measurement
        self.measuring = True
        with(QMutexLocker(self.mutex)):
            self.pm.write('*CLS')
            power = self.pm.query_ascii_values('read?')[0]
            self.measurement_complete.emit(power)
        self.measuring = False
        return power

    def zero(self):
        self.measuring = True
        with(QMutexLocker(self.mutex)):
            self.pm.write('sens:corr:coll:zero:init')
        self.measuring = False

    def reset(self):
        # returns unit to default condition
        self.measuring = True
        with(QMutexLocker(self.mutex)):
            self.pm.write('*RST')
            self.pm.write('*CLS')
        self.measuring = False

    def emit_parameters(self):
        wavelength = int(self.wavelength)
        integration_time = int(self.integration_time)
        self.measurement_parameters.emit(wavelength, integration_time)

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

    def disconnect(self):
        self.pm.close()
        self.connected = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def __repr__(self):
        return self.pm.query('*IDN?')