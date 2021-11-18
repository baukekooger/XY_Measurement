import csv
import time
import numpy as np
import pyvisa as visa
import logging

import pyvisa.errors

from instruments.Thorlabs.powermeters import PowerMeter
from PyQt5.QtCore import QObject, QMutexLocker, QMutex, pyqtSignal, pyqtSlot
import math


def list_available_devices():
    return visa.ResourceManager().list_resources()


class QPowerMeter(PowerMeter, QObject):
    """
    Python interface for the Thorlabs PM100A powermeter as a QObject

    Includes additional measurement functions and signals.

    """
    measurement_complete = pyqtSignal(float)
    measurement_complete_multiple = pyqtSignal(list, list)
    measurement_done = pyqtSignal()
    measurement_parameters = pyqtSignal(int, int)
    zero_complete = pyqtSignal()

    def __init__(self, integration_time=200):
        PowerMeter.__init__(self, 'USB0::0x1313::0x8079::P1002333::INSTR')
        QObject.__init__(self)
        self.logger_q_instrument = logging.getLogger('Qinstrument.QPowerMeter')
        self.logger_q_instrument.info('init QPowerMeter')
        self.mutex = QMutex(QMutex.Recursive)
        self.integration_time = integration_time
        self.measurements_multiple = 40
        self.last_powers = []
        self.last_times = []

    @pyqtSlot()
    def connect(self):
        self.connect_device()
        if self.sensor['Model'] == 'no sensor':
            raise ConnectionError('No sensor connected to powermeter')
        self.averageing = 1
        self.integration_time = 200
        self.autorange = True

    @property
    def integration_time(self):
        """ Integration time in [ms] """
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value):
        """ sets the integration time and accompanying number of values for a multiple measurement """
        self.logger_q_instrument.info(f'setting integration time to {value} ms')
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
        """
        Single reading of the powermeter with averaging set close to integration time
        """
        self.measuring = True
        t1 = time.time()
        with(QMutexLocker(self.mutex)):
            self.pm.write('*CLS')
            power = self.read_power()
            self.measurement_complete.emit(power)
        t2 = time.time()
        self.logger_q_instrument.info(f'powermeter completed with internal averaging in {t2-t1:.3f} seconds')
        self.measuring = False
        return power

    @pyqtSlot()
    def measure(self):
        """
        Take multiple single measurements for the duration of integration time

        Interpolate these measurements with a fixed number of values based on integration time
        each reading takes approx 5 ms.
        """
        self.logger_q_instrument.info('measuring powermeter')
        self.measuring = True
        t1 = time.perf_counter()
        measurements = []
        t = []
        with(QMutexLocker(self.mutex)):
            self.pm.write('*CLS')
            time.sleep(0.002)
            while time.perf_counter() - t1 < self.integration_time/1000:
                power = self.read_power()
                measurements.append(power)
                t.append(time.perf_counter() - t1)
                time.sleep(0.002)
        t2 = time.perf_counter()
        self.logger_q_instrument.info(f'powermeter completed,  time with all measurements {t2-t1:.3f}, '
                     f'number of measurements = {len(measurements)}')
        self.last_times = list(np.linspace(0, t[-1], self.measurements_multiple))
        self.last_powers = list(np.interp(self.last_times, t, measurements))
        self.measurement_complete_multiple.emit(self.last_times, self.last_powers)
        self.measurement_done.emit()
        self.measuring = False
        self.emit_parameters()
        return self.last_times, self.last_powers

    @pyqtSlot()
    def zero(self):
        self.measuring = True
        with(QMutexLocker(self.mutex)):
            self.zero_device()
            self.zero_complete.emit()
        self.measuring = False

    @pyqtSlot()
    def reset(self):
        # returns unit to default condition
        self.measuring = True
        with(QMutexLocker(self.mutex)):
            self.reset_default()
        self.measuring = False

    @pyqtSlot()
    def emit_parameters(self):
        wavelength = int(self.wavelength)
        integration_time = int(self.integration_time)
        self.measurement_parameters.emit(wavelength, integration_time)

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
