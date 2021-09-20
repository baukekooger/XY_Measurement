import csv
import time
import numpy as np
import pyvisa as visa
import logging
from instruments.Thorlabs.powermeters import PowerMeter
from PyQt5.QtCore import QObject, QMutexLocker, QMutex, pyqtSignal, pyqtSlot
logging.basicConfig(level=logging.INFO)
import math


def list_available_devices():
    return visa.ResourceManager().list_resources()


class QPowerMeter(PowerMeter, QObject):
    """
    Python interface for the Thorlabs PM100A powermeter as a QObject

    Includes some different measurement functions and signals

    """
    measurement_complete = pyqtSignal(float)
    measurement_complete_multiple = pyqtSignal(np.ndarray, np.ndarray)
    measurement_parameters = pyqtSignal(int, int)
    zero_complete = pyqtSignal()

    def __init__(self, integration_time=200):
        PowerMeter.__init__(self, 'USB0::0x1313::0x8079::P1002333::INSTR')
        QObject.__init__(self)
        self.mutex = QMutex(QMutex.Recursive)
        self.integration_time = integration_time
        self.measurements_multiple = 40

    @pyqtSlot()
    def connect(self):
        self.connect_device()
        self.averageing = 1
        self.integration_time = 200

    @property
    def integration_time(self):
        """ Duration of integration time in [ms] """
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value):
        """ sets the integration time and accompanying number of values for a multiple measurement
            """
        self._integration_time = value
        # set number of multiple measurements to average over
        self.measurements_multiple = math.ceil(value/5)

    @pyqtSlot()
    def prepare_measurement_internal_averaging(self):
        """ prepare a measurement where internal averaging is used

            checks if timeout needs to be adjusted based on set integration time
            """
        self.measuring = True
        if self.timeout < self.integration_time - 500:
            self.timeout = self.integration_time + 500
        averages = round(self.integration_time * 3)
        self.averageing = averages

    @pyqtSlot()
    def prepare_measurement_multiple(self):
        """ sets the averageing back to 1 """
        self.averageing = 1

    @pyqtSlot()
    def measure_average(self):
        """ single reading of the powermeter with averaging set close to integration time"""
        self.measuring = True
        t1 = time.time()
        with(QMutexLocker(self.mutex)):
            self.pm.write('*CLS')
            power = self.read_power()
            self.measurement_complete.emit(power)
        t2 = time.time()
        logging.info(f'powermeter completed with internal averaging in {t2-t1:.3f} seconds')
        self.measuring = False
        return power

    @pyqtSlot()
    def measure(self):
        """ takes multiple single measurements for the duration of integration time

            interpolates these measurements with a fixed number of values based on integration time
            each reading takes approx 5 ms.
            """
        self.measuring = True
        t1 = time.perf_counter()
        measurements = []
        t = []
        self.pm.write('*CLS')
        time.sleep(0.002)
        with(QMutexLocker(self.mutex)):
            while time.perf_counter() - t1 < self.integration_time/1000:
                power = self.read_power()
                measurements.append(power)
                t.append(time.perf_counter() - t1)
                time.sleep(0.002)
        t2 = time.perf_counter()
        logging.info(f'powermeter completed,  time with all measurements {t2-t1:.3f}, '
                     f'number of measurements = {len(measurements)}')
        t_interp = np.linspace(0, t[-1], self.measurements_multiple)
        measurements_interp = np.interp(t_interp, t, measurements)
        self.measurement_complete_multiple.emit(t_interp, measurements_interp)
        return t_interp, measurements_interp

    def zero(self):
        self.measuring = True
        with(QMutexLocker(self.mutex)):
            self.zero_device()
            self.zero_complete.emit()
        self.measuring = False

    def reset(self):
        # returns unit to default condition
        self.measuring = True
        with(QMutexLocker(self.mutex)):
            self.reset_default()
        self.measuring = False

    def emit_parameters(self):
        wavelength = int(self.wavelength)
        integration_time = int(self.integration_time)
        self.measurement_parameters.emit(wavelength, integration_time)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def __repr__(self):
        return self.pm.query('*IDN?')