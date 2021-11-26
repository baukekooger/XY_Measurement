import seabreeze.spectrometers as sb
import time
import numpy as np
from PyQt5.QtCore import QObject, QMutexLocker, QMutex, pyqtSignal, pyqtSlot
import logging


class QSpectrometer(QObject):
    """
    Spectrometer class for Ocean Optics spectrometers as a QObject subclass to use in threaded applications.
    """
    measurement_complete = pyqtSignal(np.ndarray)
    measurement_done = pyqtSignal()
    measurement_dark_complete = pyqtSignal(np.ndarray)
    measurement_lamp_complete = pyqtSignal(np.ndarray)
    measurement_parameters = pyqtSignal(int, int)
    cache_cleared = pyqtSignal()
    transmission_set = pyqtSignal()

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
        self.plotinfo = None

    @property
    def name(self):
        """Name of the Instrument"""
        return type(self).__name__

    def connect(self, spec=None):
        if not spec:
            try:
                self.spec = sb.Spectrometer(sb.list_devices()[0])
            except IndexError as e:
                raise ConnectionError('No spectrometer found, please check connection')
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
    def measurement(self):
        """
        Measure a spectrum with the spectrometer.

        Due to internal working of the spectrometer, it continuously acquires data and returns a spectrum when the
        buffer is full. Therefore the first result is awaited and timed. When the time is above a certain treshold,
        it measures again.
        """

        with(QMutexLocker(self.mutex)):
            cache_cleared = False
            while self.measuring and not cache_cleared:
                self.logger.info('spectrometer cache not cleared, requesting measurement')
                tstart = time.perf_counter()
                self.spec.intensities()
                tstop = time.perf_counter()
                self.logger.info(f'time first measurement {1000*(tstop-tstart):.1f} miliseconds')
                cache_cleared = self.integrationtime/1000 * 0.1 < tstop-tstart < self.integrationtime/1000 * 3
            self.logger.info('spectrometer cache cleared')
            self.cache_cleared.emit()
            t = []
            t1 = time.perf_counter()
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

        t2 = time.perf_counter()
        self.measurement_parameters.emit(self.integrationtime, self.average_measurements)
        self.logger.info(f'spectrometer done in {1000*(t2-t1):.1f} miliseconds')
        self.last_intensity = intensity
        self.last_times = t
        return intensity, t

    @pyqtSlot()
    def measure(self):
        """ Perform a regular measurement"""
        self.measuring = True
        self.logger.info('measuring a spectrum with the spectrometer')
        spectrum, t = self.measurement()
        self.measurement_complete.emit(spectrum)
        self.measurement_done.emit()
        self.measuring = False
        return self.dark, t

    @pyqtSlot()
    def measure_dark(self):
        """
        Perform a measurement and store the result in the dark spectrum attribute.
        """
        self.measuring = True
        self.logger.info('measuring a dark spectrum with the spectrometer')
        dark, t = self.measurement()
        self.measurement_dark_complete.emit(dark)
        self.measurement_done.emit()
        self.dark = dark
        self.measuring = False
        return self.dark, t

    @pyqtSlot()
    def clear_dark(self):
        self.dark = np.zeros(len(self.spec.wavelengths()))

    @pyqtSlot()
    def measure_lamp(self):
        """
        Perform a measurement and store the result in the lamp spectrum attribute.
        """
        self.measuring = True
        self.logger.info('measuring a lamp spectrum with the spectrometer')
        lamp, t = self.measurement()
        self.measurement_lamp_complete.emit(lamp)
        self.measurement_done.emit()
        self.lamp = lamp
        self.measuring = False
        return self.dark, t

    @pyqtSlot()
    def clear_lamp(self):
        self.lamp = np.zeros(len(self.spec.wavelengths()))

    @pyqtSlot()
    def set_transmission(self):
        """
        Set transmission attribute to true if unset, and emit a signal for the spectrometer widget
        that sets the button to checked.
        """
        if not self.transmission:
            self.transmission = True
            self.transmission_set.emit()


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