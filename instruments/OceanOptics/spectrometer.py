import seabreeze.spectrometers as sb
import time
import numpy as np
from PyQt5.QtCore import QObject, QMutexLocker, QMutex, pyqtSignal, pyqtSlot
import logging


class QSpectrometer(QObject):
    """PyQt5 implementation of Spectrometer Instrument

    pyqtSignals:
        measurement_complete (list, list)
            the intensities and the times of the spectromter measurement
    """
    measurement_complete = pyqtSignal(np.ndarray, list)
    measurement_done = pyqtSignal()
    measurement_dark_complete = pyqtSignal()
    measurement_lamp_complete = pyqtSignal()
    measurement_parameters = pyqtSignal(int, int)
    cache_cleared = pyqtSignal()

    def __init__(self, integrationtime=500, average_measurements=1, polltime=0.01, timeout=30, parent=None):
        super().__init__(parent=parent)
        self.logger = logging.getLogger('QInstrument.QSpectrometer')
        self.logger.info('init QSpectrometer')
        self.mutex = QMutex(QMutex.Recursive)
        self.measuring = False
        self.polltime = polltime
        self.timeout = timeout
        # Spectrometer
        self.spec = None
        self.connected = False
        self.measuring = False
        self.correct_dark_counts = False
        self.correct_nonlinearity = False
        self._integrationtime = integrationtime
        self._average_measurements = average_measurements
        self.dark = []
        self.lamp = []
        self.min_integrationtime = None
        self.last_intensity = []
        self.last_times = []
        self.transmission = False

    @property
    def name(self):
        """Name of the Instrument"""
        return type(self).__name__

    def connect(self, spec=None):
        if not spec:
            try:
                self.spec = sb.Spectrometer(sb.list_devices()[0])
            except IndexError as e:
                raise ConnectionError('No spectrometer found!')
        else:
            self.spec = spec
        self.min_integrationtime = self.spec.minimum_integration_time_micros / 1000
        self.integrationtime = self._integrationtime
        self.connected = True

    def disconnect(self):
        if not self.connected:
            return
        self.spec.close()
        self.connected = False

    @property
    def wavelengths(self):
        """The wavelengths this spectrometer can measure (Read-only) """
        wls = self.spec.wavelengths()
        return wls.tolist()

    @property
    def integrationtime(self):
        """ The spectrometer's integration time in [ms] """
        return self._integrationtime

    @integrationtime.setter
    def integrationtime(self, value):
        v = value * 1000
        min_v = self.min_integrationtime * 1000
        if v < min_v:
            self.logger.warning(f'{float(v) / 1000} ms is lower than the minimal '
                            'allowed integration time')
            self.logger.warning('Integration time set to mimimal value')
            v = min_v
        self.spec.integration_time_micros(v)
        self._integrationtime = v / 1000

    @property
    def average_measurements(self):
        """Average number of measurements. Stops any measurement upon setting."""
        return self._average_measurements

    @average_measurements.setter
    def average_measurements(self, value):
        self.measuring = False
        self._average_measurements = value

    @pyqtSlot()
    @pyqtSlot(list, list)
    def measure(self, *args):
        """Performs a mutex-locked measurement.

        Returns:
           | list: intensities [counts]
           | list: times measured over as
               [ [tstart0, tstart1,...], [tstop0, tstop1, ...] ]
        Emits:
            measurement_complete (list, list):
                | intensities [counts],
                | times measured over as
                    [ [tstart0, tstart1,...], [tstop0, tstop1, ...] ]
        """
        with(QMutexLocker(self.mutex)):
            self.measuring = True
            cache_cleared = False
            while self.measuring and not cache_cleared:
                self.logger.info('spectrometer cache not cleared, requesting measurement')
                tstart = time.time()
                self.spec.intensities()
                tstop = time.time()
                cache_cleared = self.integrationtime/1000 * 0.9 < tstop-tstart < self.integrationtime/1000 * 1.1
            self.logger.info('spectrometer cache cleared')
            self.cache_cleared.emit()
            t = []
            t1 = time.time()
            self.logger.info(f'spectrometer measurment started')
            intensity = np.zeros(len(self.spec.wavelengths()))
            n = 1
            while self.measuring and n <= self.average_measurements:
                t.append(time.time())
                intensity += (1. / self.average_measurements *
                              self.spec.intensities(self.correct_dark_counts,
                                                    self.correct_nonlinearity))
                t.append(time.time())
                n += 1
            # if any(self.dark):
            #     intensity = intensity - self.dark
            # if self.transmission and all(self.lamp):
            #     intensity = intensity/self.lamp
        t2 = time.time()
        self.measuring = False
        self.logger.info(f'spectrometer done in {t2-t1:.3f} seconds')
        self.last_intensity = intensity
        self.last_times = t
        self.measurement_complete.emit(intensity, t)
        self.measurement_done.emit()
        self.measurement_parameters.emit(int(self.integrationtime), int(self.average_measurements))
        return intensity, t

    @pyqtSlot()
    def measure_dark(self):
        """ Performs a mutex-locked dark measurement.
        The result will be stored and emitted.
        """
        with(QMutexLocker(self.mutex)):
            self.dark, t = self.measure()
        self.measurement_complete.emit(self.dark, t)
        self.last_intensity = self.dark
        self.last_times = t
        self.measurement_dark_complete.emit()
        return self.dark, t

    @pyqtSlot()
    def clear_dark(self):
        self.dark = np.zeros(len(self.spec.wavelengths()))

    @pyqtSlot()
    def measure_lamp(self):
        """Performs a mutex-locked lamp measurement.
        The result will be stored and emitted.
        """
        with(QMutexLocker(self.mutex)):
            self.lamp, t = self.measure()
        self.measurement_complete.emit(self.lamp, t)

        self.last_intensity = self.lamp
        self.last_times = t
        self.measurement_lamp_complete.emit()
        return self.dark, t

    @pyqtSlot()
    def clear_lamp(self):
        self.lamp = np.zeros(len(self.spec.wavelengths()))


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