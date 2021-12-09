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
    measurement_complete_multiple = pyqtSignal(list, list, str)
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
        self.plotinfo = None
        self.sensorinfo_plot = None
        self.modelinfo_plot = None

    @pyqtSlot()
    def connect(self):
        """ Connect powermeter and initialize. """
        self.logger_q_instrument.info('Attempt to connect powermeter.')
        self.connect_device()
        time.sleep(0.1)
        self.modelinfo_plot = self.device
        self.sensorinfo_plot = self.sensor
        if self.sensorinfo_plot['Model'] == 'no sensor':
            raise ConnectionError('No sensor connected to powermeter')
        self.averageing = 1
        self.integration_time = 200
        self.autorange = True

    @property
    def integration_time(self):
        """ Integration time in [ms] """
        self.logger_q_instrument.debug('Querying integration time')
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
        """
        Prepare a measurement where internal averaging is used by setting the internal averageging.

        Check if timeout needs to be adjusted based on set integration time
        """
        self.logger_q_instrument.info('Preparing measurement for internal averageing.')
        self.measuring = True
        if self.timeout < self.integration_time - 500:
            self.timeout = self.integration_time + 500
        averages = round(self.integration_time * 3)
        self.averageing = averages

    @pyqtSlot()
    def prepare_measurement_multiple(self):
        """
        Prepare powermeter for taking multiple measurements with external averageing, by setting the averageing to 1.
        """
        self.logger_q_instrument.info('Preparing powermeter for multiple measurements')
        self.averageing = 1

    @pyqtSlot()
    def measure_average(self):
        """
        Single reading of the powermeter with averaging set close to integration time.
        """
        self.logger_q_instrument.info('Measuring powermeter with internal averegeing.')
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
        self.measuring = True
        self.logger_q_instrument.info('Measuring powermeter with multiple measurements, external averageing.')
        plotinfo = self.plotinfo if self.plotinfo else ''
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
        self.measurement_complete_multiple.emit(self.last_times, self.last_powers, plotinfo)
        self.measurement_done.emit()
        self.measuring = False
        return self.last_times, self.last_powers

    @pyqtSlot()
    def zero(self):
        """ Zero the powermeter. """
        self.logger_q_instrument.info('Zeroing powermeter')
        self.measuring = True
        with(QMutexLocker(self.mutex)):
            self.zero_device()
            self.zero_complete.emit()
        self.measuring = False

    @pyqtSlot(int)
    def set_wavelength(self, value):
        """ Callable to set the wavelength. """
        self.logger_q_instrument.info(f'Setting the wavelength from callable to {value}')
        self.wavelength = value

    @pyqtSlot()
    def reset(self):
        """ Reset device to default condition. """
        self.logger_q_instrument.info('Setting powermeter to default. ')
        self.measuring = True
        with(QMutexLocker(self.mutex)):
            self.reset_default()
        self.measuring = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connected:
            self.disconnect()

    def __repr__(self):
        return self.pm.query('*IDN?')


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers
    pathlogging = Path(__file__).parent.parent.parent / 'logging/loggingconfig_testing.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
