import seabreeze.spectrometers as sb
import time
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)


class Instrument:
    """Base class for all Instruments.

    Attributes:
        polltime (float): time in [s] between each call to an instrument if a measurement has completed.
        timeout (float): time in [s] before measurement is aborted and an error is returned.
    """

    def __init__(self, polltime=0.01, timeout=30):
        self.measuring = False
        self.polltime = polltime
        self.timeout = timeout

    @property
    def name(self):
        """Name of the Instrument"""
        return type(self).__name__

    def connect(self):
        raise NotImplementedError(
            'Instrument {} has not defined a connect method'.format(
                type(self).__name__))

    def disconnect(self):
        raise NotImplementedError(
            'Instrument {} has not defined a disconnect method'.format(
                type(self).__name__))

    def measure(self):
        raise NotImplementedError(
            'Instrument {} has not defined a measure method'.format(
                type(self).__name__))

    @classmethod
    def disconnect_all(cls):
        """Disconnects all connected Instruments"""
        for instrument in cls.objs:
            try:
                instrument.disconnect()
            except NotImplementedError:
                pass


class Spectrometer(Instrument):
    """Ocean Optics Spectrometer python interface

    Controls an Ocean Optics spectrometer using the pyseabreeze API.
    All times used internally are in [ms]. For interaction with the seabreeze
    library, these have to be converted to [us].

    Args:
        integrationtime_ms (int): integration time in milliseconds
        average_measurements (int): times to average over
    """

    def __init__(self, integrationtime=100, average_measurements=10):
        super().__init__()
        # Spectrometer
        self.spec = None
        self.connected = False
        self.measuring = False
        self.correct_dark_counts = False
        self.correct_nonlinearity = False
        self._integrationtime = integrationtime
        self._average_measurements = average_measurements
        self.dark = []
        self.min_integrationtime = None

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
            logging.warning(f'{float(v)/1000} ms is lower than the minimal '
                            'allowed integration time' )
            logging.warning('Integration time set to mimimal value')
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

    def measure(self):
        """Measures light intensities.
        If a dark measurement is done, it will be substracted.

        Returns:
           | list: intensities [counts]
           | list: times measured over as
               [ [tstart0, tstart1,...], [tstop0, tstop1, ...] ]
        """
        # TODO include Timeout

        # Perform 'fake' measurement if the integration times don't match
        # This clears the Spectrometer's cache
        cache_cleared = False
        self.measuring = True
        while self.measuring and not cache_cleared:
            t = [time.time()]
            intensity = (self.spec.intensities(
                self.correct_dark_counts,
                self.correct_nonlinearity) / self.average_measurements)
            t.append(time.time())
            mm = self._integrationtime / 1000
            cache_cleared = (mm * 0.9 < np.diff(t)[0] < mm * 1.1)
            # Cannot measure less than 30 ms time difference
            if mm * 1000 < 30:
                cache_cleared = True
            logging.info('Cache cleared? {}'.format(cache_cleared))

        n = 1
        while self.measuring and n < self.average_measurements:
            t.append(time.time())
            intensity += (1. / self.average_measurements *
                          self.spec.intensities(self.correct_dark_counts,
                                                self.correct_nonlinearity))
            t.append(time.time())
            n += 1

        if self.dark:
            intensity = intensity - self.dark

        self.measuring = False
        return intensity.tolist(), t

    def measure_dark(self):
        """Internally sets the dark spectrum
        """
        self.clear_dark()
        self.dark, t = self.measure()
        return self.dark, t

    def clear_dark(self):
        self.dark = []

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


# list_available_devices = seabreeze.spectrometers.list_devices

# class Spectrometer(seabreeze.spectrometers.Spectrometer):
#     def __init__(self, serial, integration_time=100, average_measurements=1, correct_dark_counts=True,
#                  correct_nonlinearity=True, sensitivity_correction=None):
#         super().from_serial_number(serial)
#         self._integration_time = integration_time
#         self.average_measurements = average_measurements
#         self._correct_dark_counts = correct_dark_counts
#         self._correct_nonlinearity = correct_nonlinearity
#         self.dark_spectrum = None
#         self.sensitivity_correction = self.set_sensitivity_correction(sensitivity_correction)
#         self.measuring = False
#
#     @property
#     def integration_time(self):
#         """
#         Integration time in [ms]
#         """
#         self.integration_time = self._integration_time
#         return self._integration_time
#
#     @integration_time.setter
#     def integration_time(self, value):
#         """
#         Sets the integration time to value [ms]
#         :param value: Desired integration time in [ms]
#         """
#         if value * 1000. < self.minimum_integration_time_micros:
#             logging.warning('The minimum integration time for {} is {} ms.'
#                             'Integration is set to this value.'.format(self.__repr__(),
#                                                                        self.minimum_integration_time_micros * 1000))
#             value = self.minimum_integration_time_micros / 1000.
#             self._integration_time = value
#         self.integration_time_micros(value * 1000.)
#
#     @property
#     def correct_dark_counts(self):
#         """
#         Enable or disable dark count correction (if possible)
#         """
#         self.correct_dark_counts = self._correct_dark_counts
#         return self._correct_dark_counts
#
#     @correct_dark_counts.setter
#     def correct_dark_counts(self, value):
#         if not self._has_dark_pixels:
#             logging.warning('Spectrometer {} has no dark pixels. No dark correction possible.'.format(self.__repr__()))
#         self._correct_dark_counts = value if self._has_dark_pixels else False
#
#     @property
#     def correct_nonlinearity(self):
#         """
#         Enable or disable non-linearity correction (if possible)
#         """
#         self.correct_nonlinearity = self._correct_nonlinearity
#         return self._correct_nonlinearity
#
#     @correct_nonlinearity.setter
#     def correct_nonlinearity(self, value):
#         if not self._has_nonlinearity_coeffs:
#             logging.warning('Spectrometer {} has no non-linearity coefficients. '
#                             'No non-linearity correction possible.'.format(self.__repr__()))
#         self._correct_nonlinearity = value if self._has_nonlinearity_coeffs else False
#
#     def set_sensitivity_correction(self, file):
#         """
#         Set the correction for the spectrometer sensitivity and all other optics within the used setup.
#         The sensitivity file (.csv) is formatted as following:
#         CREATION DATE: <<Date of calibration>>
#         Wavelength (nm), Intensity (a.u.)
#         wl_1, I_1
#         ..., ...
#
#         :param file: location of the correction file
#         :return: dict: {'wavelengths': [...], 'intensity': [...]} a dict of the correction file
#         """
#         if not file:
#             self.sensitivity_correction = None
#             return None
#         sensitivity_correction = {'wavelengths': [], 'intensity': []}
#         with open(file) as correction_file:
#             correction_reader = csv.reader(correction_file, delimiter=',')
#             for nrow, row in enumerate(correction_reader):
#                 if nrow in [0, 1]:
#                     continue
#                 sensitivity_correction['wavelengths'].append(row[0])
#                 sensitivity_correction['intensity'].append(row[1])
#         interpolated_sensitivity_correction = np.interp(self.wavelengths(),
#                                                         sensitivity_correction['wavelengths'],
#                                                         sensitivity_correction['intensity'])
#         self.sensitivity_correction = interpolated_sensitivity_correction
#         return interpolated_sensitivity_correction
#
#     def measure(self):
#         """
#         Measures light intensities.
#         If a dark measurement is done, it will be subtracted.
#         :return:
#             dict: {times: [[t_start, t_stop], ...],
#                    intensity: array[...],
#                    wavelengths: array[...],
#                    dark: array[...]}
#         """
#         intensity = None
#         t = None
#         # Keep measuring until the measurement duration matches the set duration
#         # All measurements shorter than the set duration were measurements already stored in the Spectrometer's buffer.
#         # Requesting the cached measurements clears the Spectrometer's cache
#         # TODO implement sbapi_data_buffer_clear from seabreeze API
#         cache_cleared = False
#         self.measuring = True
#         while not cache_cleared and self.measuring:
#             t = [[time.time()]]
#             intensity = (self.intensities(
#                 self.correct_dark_counts,
#                 self.correct_nonlinearity))
#             t[-1].append(time.time())
#             mm = self.integration_time / 1000
#             cache_cleared = (mm * 0.9 < np.diff(t)[0] < mm * 1.1)
#             # Cannot measure less than 30 ms time difference
#             if mm * 1000 < 30:
#                 cache_cleared = True
#             logging.info('Cache cleared: {}'.format(cache_cleared))
#
#         for _ in range(1, self.average_measurements):
#             if not self.measuring:
#                 break
#             t.extend([time.time()])
#             intensity += (self.intensities(self.correct_dark_counts,
#                                            self.correct_nonlinearity))
#             t[-1].append(time.time())
#         intensity = intensity / self.average_measurements
#
#         # Correct spectra
#         if self.dark_spectrum:
#             intensity = intensity - self.dark_spectrum
#         if self.sensitivity_correction:
#             intensity = intensity / self.sensitivity_correction
#
#         self.measuring = False
#         return {'times': t, 'intensity': intensity, 'dark': self.dark_spectrum, 'wavelengths': self.wavelengths()}
#
#     def measure_dark(self):
#         """Internally sets the dark spectrum
#         """
#         self.dark_spectrum = self.measure()['intensity']
#         return self.dark_spectrum
#
#     def clear_dark(self):
#         self.dark_spectrum = None
