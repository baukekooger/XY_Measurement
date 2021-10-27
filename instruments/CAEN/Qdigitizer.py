import instruments.CAEN as CAENlib
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QMutex, QMutexLocker
import time
import logging
import numpy as np
import scipy.ndimage as sp


def _find_next_power_two(n):
    """
    Find the (positive) power of two closes to n. For example, input n = 17 returns 32.
    Smallest output is 2^1 or 1. All values smaller or equal to one (also negative) return 2.

    :param n: input value
    :type n: int
    :returns: closest power of two to input value n
    """
    # return values outside of range to 1
    n = 1 if n <= 1 else n

    # decrement `n` (to handle cases when `n` itself
    # is a power of 2)
    n = n - 1

    # do till only one bit is left
    while n & n - 1:
        n = n & n - 1  # unset rightmost bit

    # `n` is now a power of two (less than `n`)

    # increase n by one if n is 0
    n = 1 if n == 0 else n
    # return next power of 2
    return n << 1


class QDigitizer(CAENlib.Digitizer, QObject):
    """
    Control class for the Digitizer, subclassed as a QObject to enable using the Digitizer in threaded pyQt
    applications.

    Also includes extended functionality such as jitter correction, single photon counting and data compression
    """

    measurement_complete = pyqtSignal(np.ndarray, np.ndarray, str)
    measurement_complete_multiple = pyqtSignal(np.ndarray)
    measurement_done_multiple = pyqtSignal()
    single_photon_counting_signal = pyqtSignal()
    parameters = pyqtSignal(list, list, list, int, int)
    redraw_plot = pyqtSignal()

    def __init__(self):
        CAENlib.Digitizer.__init__(self)
        QObject.__init__(self)
        self.logger = logging.getLogger('Qinstrument.Qdigitizer')
        self.logger.info('init QDigitizer')
        self.mutex = QMutex()
        self.polltime_enabled = False
        self.polltime_measurement = 1
        self.connected = False
        self.measuring = False
        self.pulses_per_measurement = 1
        self.last_pulses = []
        self.measuring_mode = 'single pulse'
        self.data_channel = 0
        self.single_photon_counting_treshold = 0
        self.added_pulses = np.empty(0)
        self.average_pulses = np.empty(0)
        self.single_photon_counts = np.empty(0)
        self.pulse_counter = 0
        self.compression_factor = 1
        self.jitter_correction_enabled = False
        self.jitter_channel = 1
        self.max_plot_points = 2e4

    def init_device(self):
        """ Provide some commom initial settings """
        self.record_length = 0
        self.max_num_events_blt = 1
        self.post_trigger_size = 90
        self.set_active_channels()
        self.set_dc_offset_data_channel(10)
        self.acquisition_mode = CAENlib.AcqMode.SW_CONTROLLED
        self.external_trigger_mode = CAENlib.TriggerMode.ACQ_ONLY
        self.external_trigger_level = CAENlib.IOLevel.TTL

    @pyqtSlot()
    def connect(self):
        """ Open the digitizer, then apply common initial settings """
        self.connect_device()
        self.connected = True
        self.init_device()

    @pyqtSlot()
    def disconnect(self):
        """ Disconnect the digitizer """
        self.close()
        self.connected = False

    @pyqtSlot()
    @pyqtSlot(int)
    def measure(self, *pulses: int):
        """
        Performs repeated single-event measurements with the number of measurements set by the pulses per
        measurement attribute or by the input value. Can also read single measurement.

        If a maximum measuring polltime is set
        """
        with(QMutexLocker(self.mutex)):
            self.measuring = True
            if not pulses:
                pulses_per_measurement = self.pulses_per_measurement
            else:
                pulses_per_measurement = pulses
            tstart = time.time()
            self.logger.info(f'started measuring {pulses_per_measurement} pulse(s)')

            for pulse in range(pulses_per_measurement):
                data = self.measurement_single_event()
                data = self._invert_data(data)
                data = self._jitter_correction(data)
                if self.measuring_mode == 'single photon counting':
                    self._single_photon_counting(data)
                elif self.measuring_mode == 'averageing':
                    self._average_pulses(data)
                tcurrent = time.time()
                if self.polltime_enabled and (tcurrent - tstart) > (0.8 * self.polltime_measurement):
                    self.logger.info(f'measurement past polltime, finishing after {pulse + 1} pulses')
                    break
            self.logger.info(f'measurement finishing after {pulse + 1} pulses')

        if self.measuring_mode == 'single pulse':
            times, data, plotinfo = self._plot_single_pulse(data)
            self.measurement_complete.emit(times, data, plotinfo)
        elif self.measuring_mode == 'averageing':
            times, data, compressioninfo = self._compress_average_pulses()
            plotinfo = f'{self.pulse_counter} pulses, {compressioninfo}'
            self.measurement_complete.emit(times, data, plotinfo)
        elif self.measuring_mode == 'single photon counting':
            times, data = self._compress_single_photon_counts()
            plotinfo = f'{self.pulse_counter} pulses'
            self.measurement_complete.emit(times, data, plotinfo)

        self.measuring = False
        return data

    def _invert_data(self, data: np.ndarray):
        """ Invert the data """
        self.logger.info('inverting data')
        max_counts = pow(2, self.adc_number_of_bits) - 1
        data = -(data - max_counts)
        return data

    def _jitter_correction(self, data):
        """
        Corrects for the jitter in the signal which is present with regards to the trigger input.
        :param data: single event measurement [channels][samples]
        :type data: np.ndarray
        """
        if not self.jitter_correction_enabled:
            data = data[0]
        else:
            data = data[0] if self.data_channel < self.jitter_channel else data[1]
        return data

    def _plot_single_pulse(self, data):
        """
        Select only the datachannel from the data and make a corresponding timevector to emit to plotwindow.
        Compress the data if number of samples is above a set value (avoid plotting extremely lengthy data)
        :param data: single event measurement [channels][samples]
        :returns: times (time array), data (data array), plotinfo (string)
        """
        self.logger.info('selecting plotdata single pulse')
        samples = len(data)
        if samples > self.max_plot_points:
            times, data, plotinfo = self._compress_long_data(data, samples)
        else:
            plotinfo = 'uncompressed data'
            times = np.linspace(0, (samples - 1) / self.sample_rate, samples)

        return times, data, plotinfo

    def _compress_long_data(self, data, samples):
        """
        Compress the data with a factor which is the smallest power of two to make the number of datapoints smaller
        than the maximum set number of datapoints to plot.

        :param data: data to compress
        :param samples: number of samples in the data
        :returns data: compressed data
        """

        self.logger.info('compressing long data for plotting')
        maindivision = int(samples // self.max_plot_points)
        compressionfactor = _find_next_power_two(maindivision)

        data = np.reshape(data, (int(samples // compressionfactor), int(compressionfactor)))
        data = np.mean(data, axis=1)
        times = np.linspace(0, (samples - 1) / self.sample_rate, int(samples // compressionfactor))
        plotinfo = f'data compressed with factor {compressionfactor}'
        return times, data, plotinfo

    def _average_pulses(self, data):
        """
        Take the average of multiple pulses. To take the average, the pulses need to be normalized.

        :param data: [samples]
        :type data: np.ndarray
        """
        self.pulse_counter += 1
        # subtract the average of the first 20 datapoints.
        data = data - np.mean(data[0:30])
        data = data / np.max(data)
        try:
            self.logger.debug('adding pulse')
            self.average_pulses = (self.average_pulses * (self.pulse_counter - 1) + data) / self.pulse_counter
        except ValueError as e:
            self.logger.info(f'could not add pulse to added pulses, resetting added pulses {e}')
            self.pulse_counter = 1
            self.average_pulses = data

    def _compress_average_pulses(self):
        """ Compress the averaged pulses for plotting if the length exceeds the maximum plot length """
        samples = len(self.average_pulses)
        if samples > self.max_plot_points:
            times, data, compinfo = self._compress_long_data(self.average_pulses, samples)
        else:
            data = self.average_pulses
            compinfo = 'uncompressed data'
            times = np.linspace(0, (samples - 1) / self.sample_rate, samples)

        return times, data, compinfo

    def _single_photon_counting(self, data):
        """
        Register single photon counts by counting the data which is higher than the user-set treshold value.
        Only registers a count when previous value is below treshold. A scipy filter is used for this operation as
        it is much faster than a loop.

        Add all the counts to the single photon counts attribute which grows with each measurement until it is reset
        :param data: single event measurement [samples]
        :type data: np.ndarray
        :returns: single photon counts array
        """
        self.logger.info('counting single photon counts over treshold')
        self.pulse_counter += 1

        data_over_treshold = data > self.single_photon_counting_treshold
        filter_doublecounts = np.array([1, 0])
        data_corrected = data_over_treshold > sp.maximum_filter(
            data_over_treshold, footprint=filter_doublecounts, mode='constant', cval=-np.inf)
        try:
            self.logger.debug('adding pulse single photon counts')
            self.single_photon_counts += data_corrected
        except ValueError as e:
            self.logger.info(f'number of samples changed, resetting single photon counts and pulse counter. '
                         f'full error message: {e}')
            self.pulse_counter = 1
            self.single_photon_counts = data_corrected

    def set_compression_factor(self, factor: str):
        """ Sets the compression factor for single photon counting """
        self.logger.info(f'setting single photon compression factor to {factor}')
        try:
            self.compression_factor = CAENlib.COMPRESSIONFACTORS[self.model][factor]
        except KeyError:
            self.compression_factor = CAENlib.COMPRESSIONFACTORS[self.model].values()[0]
            raise Warning(f'Incorrect compression factor key, set compression '
                          f'factor to lowest value of {self.compression_factor}')

    def _compress_single_photon_counts(self):
        """ Compress single photon counts by the compression factor """

        self.logger.debug(f'compressing single photon counts with {self.compression_factor}')
        # factors are chosen such that this has 0 remainder
        samples = len(self.single_photon_counts)
        bins = samples // self.compression_factor
        data = np.reshape(self.single_photon_counts, (bins, self.compression_factor))
        data = np.sum(data, axis=1)
        times = np.linspace(0, (samples - 1) // self.sample_rate, samples // self.compression_factor)

        return times, data

    @pyqtSlot()
    def set_active_channels(self):
        """ set the channel mask to the data channel and the jitter channel if enabled """
        if self.jitter_correction_enabled:
            self.logger.info(f'setting data channel to {self.data_channel}, jitter channel to {self.jitter_channel}')
            channels = [self.data_channel, self.jitter_channel]
        else:
            self.logger.info(f'setting data channel to {self.data_channel}, no jitter channel')
            channels = [self.data_channel]

        self.active_channels = channels

    @pyqtSlot(int)
    def set_dc_offset_data_channel(self, offset):
        """ Set the dc offset of the data channel """
        self.logger.info(f'setting the DC offset of the data channel to {offset}')
        offset = int(offset)
        channel = self.data_channel
        self.set_dc_offset(channel, offset)

    @pyqtSlot(int)
    def set_post_trigger_size(self, size: int):
        """ Parse the post trigger size as a function call """
        self.logger.info(f'setting post trigger size to {size}')
        self.post_trigger_size = size

    @pyqtSlot()
    def check_parameters(self):
        """ Emit parameters/settings for initialization of digitizer gui """
        self.logger.info('reading digitizer parameters, emitting to ui')
        available_channels = [str(channel) for channel in range(self.number_of_channels)]
        time_ranges = CAENlib.TIMERANGES[self.model]
        compression_ranges = list(CAENlib.COMPRESSIONFACTORS[self.model].keys())
        dc_offset = self.get_dc_offset(0)
        post_trigger_size = self.post_trigger_size
        self.parameters.emit(available_channels, time_ranges,
                             compression_ranges, dc_offset, post_trigger_size)

    @pyqtSlot()
    def clear_measurement(self):
        """ Clear the registered single photon counts and multiple measurements average. Set pulse counter to 0 """
        self.logger.info('clearing measurements')
        self.single_photon_counts = np.empty(0)
        self.average_pulses = np.empty(0)
        self.pulse_counter = 0

    @pyqtSlot(int)
    def set_single_photon_counting_treshold(self, treshold):
        """ Set the value at which a spike in the data is counted as a photon """
        self.logger.info(f'setting single photon treshold to {treshold}')
        self.single_photon_counting_treshold = treshold


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    pathlogging = Path(__file__).parent.parent.parent / 'loggingconfig.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
