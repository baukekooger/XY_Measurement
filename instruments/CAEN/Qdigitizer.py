import unicodedata
import instruments.CAEN as CAENlib
import scipy.ndimage.interpolation as sp
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QMutex, QMutexLocker
import time
import logging
import numpy as np
import scipy.ndimage as sp


class QDigitizer(CAENlib.Digitizer, QObject):
    """
    Control class for the Digitizer, subclassed as a QObject to enable using the Digitizer in threaded pyQt
    applications.

    Also includes extended functionality such as jitter correction, single photon counting and data compression
    """

    measurement_complete = pyqtSignal(np.ndarray, np.ndarray, str)
    measurement_done = pyqtSignal()
    single_photon_counting_signal = pyqtSignal()
    parameters = pyqtSignal(list, list, list, int, int)
    redraw_plot = pyqtSignal()
    plotaxis_labels = pyqtSignal(dict)

    def __init__(self):
        CAENlib.Digitizer.__init__(self)
        QObject.__init__(self)
        self.logger_q_instrument = logging.getLogger('Qinstrument.QDigitizer')
        self.logger_q_instrument.info('init QDigitizer')
        self.mutex = QMutex()
        self.polltime_enabled = False
        self.polltime_measurement = 1
        self.connected = False
        self.measuring = False
        self.pulses_per_measurement = 1
        self.last_pulses = []
        self.measurement_mode = 'single pulse'
        self.data_channel = 0
        self.single_photon_counting_treshold = 0
        self.added_pulses = np.empty(0)
        self.average_pulses = np.empty(0)
        self.single_photon_counts = np.empty(0)
        self.pulse_counter = 0
        self.compression_factor = 1
        self.jitter_correction_enabled = False
        self.jitter_channel = 1
        self.jitter_startsample = 0
        self.max_plot_points = 2e4
        self.plotinfo = None

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
        try:
            self.connect_device()
            self.connected = True
            self.init_device()
        except IndexError:
            self.logger_q_instrument.error('Failed connecting to digitizer, could not find a digitizer')
            raise ConnectionError('Could not find a digitizer')

    @pyqtSlot()
    def disconnect(self):
        """ Disconnect the digitizer """
        if self.connected:
            self.close()
            self.connected = False

    @pyqtSlot()
    def measure(self):
        """
        Performs repeated single-event measurements with the number of measurements set by the pulses per
        measurement attribute or by the input value. Can also read single measurement.

        If a maximum measuring polltime is set
        """
        with(QMutexLocker(self.mutex)):
            self.measuring = True
            tstart = time.time()
            self.logger_q_instrument.info(f'started measuring {self.pulses_per_measurement} pulse(s)')
            for pulse in range(self.pulses_per_measurement):
                data = self.measurement_single_event()
                self.logger_q_instrument.debug(f'data = {data}')
                data = self._jitter_correction(data)
                data = self._invert_data(data)
                data = self._process_data(data)

                tcurrent = time.time()
                if self.polltime_enabled and (tcurrent - tstart) > (0.8 * self.polltime_measurement):
                    self.logger_q_instrument.info(f'measurement past polltime, finishing after {pulse + 1} pulses')
                    break
                elif (tcurrent - tstart) > (0.8 * self.polltime_measurement):
                    self.logger_q_instrument.debug(f'{pulse} out of {self.pulses_per_measurement}, emitting data')
                    self._emit_pulses_plotting(data)
                    tstart = time.time()

            self.logger_q_instrument.info(f'measurement finishing after {pulse + 1} pulses')

        self._emit_pulses_plotting(data)
        self.measurement_done.emit()
        self.measuring = False

        return data

    def _emit_pulses_plotting(self, data):
        """ Emit the data for plotting """
        if self.measurement_mode == 'single pulse':
            times, data, plotinfo = self._plot_single_pulse(data)
            self.measurement_complete.emit(times, data, plotinfo)
        elif self.measurement_mode == 'averageing':
            times, data, plotinfo = self._compress_average_pulses()
            plotinfo = f'{self.pulse_counter} pulses, {plotinfo}'
            plotinfo = plotinfo + '\n' + self.plotinfo if self.plotinfo else plotinfo
            self.measurement_complete.emit(times, data, plotinfo)
        elif self.measurement_mode == 'single photon counting':
            times, data, plotinfo = self._compress_single_photon_counts()
            plotinfo = plotinfo + '\n' + self.plotinfo if self.plotinfo else plotinfo
            self.logger_q_instrument.debug(f'times = {times*1000000}, data = {data}, plotinfo = {plotinfo}')
            self.logger_q_instrument.debug(f'len times = {len(times)}, len data = {len(data)}')
            self.logger_q_instrument.debug(f'max value counts unedited = {np.max(self.single_photon_counts)}')
            self.measurement_complete.emit(times, data, plotinfo)

    def _invert_data(self, data: np.ndarray):
        """ Invert the data """
        self.logger_q_instrument.debug('inverting data')
        max_counts = pow(2, self.adc_number_of_bits) - 1
        data = -(data - max_counts)
        return data

    def _process_data(self, data):
        """
        Send the data through average pulses or single photon counting routine if that measurement mode is enabled
        otherwise do nothing
        """
        if self.measurement_mode == 'single photon counting':
            self._single_photon_counting(data)
        elif self.measurement_mode == 'averageing':
            self._average_pulses(data)
        return data

    def _jitter_correction(self, data):
        """
        Correct for the jitter in the signal which is present with regards to the trigger input. Connect
        trigger TTL form laser via attenuator to input channel. Trigger will be registered taken when a treshold is
        passed on the input signal.
        :param data: single event measurement [channels][samples]
        :type data: np.ndarray
        """
        if not self.jitter_correction_enabled or len(data) == 1:
            self.logger_q_instrument.debug(f'no jitter correction, data shape = {np.shape(data)}, '
                                           f'channels = {self.active_channels}')
            return data[0]
        else:
            self.logger_q_instrument.debug(f'data for jitter correction = {np.shape(data)}')
            # get the correct channels. channel order based on channel index.
            data, jitter = (data[0], data[1]) if self.data_channel < self.jitter_channel else (data[1], data[0])
        # check if valid signal - jitter pulse through attenuator should have an amplitude of around 1500 counts
        if (jitterspread := np.max(jitter)-np.min(jitter)) < 100:
            self.logger_q_instrument.warning(f'jitter signal spread = {jitterspread} - no significant signal, '
                                             f'please check jitter signal connection. No correction applied')
            return data
        else:
            self.logger_q_instrument.debug(f'jittersignal spread = {jitterspread} - good signal - '
                                           f'correcting for jitter')
            # get indice of pulse start by comparing to treshold. trigger pulse is positive.
            treshold = np.min(jitter) + int(0.5 * jitterspread)
            self.logger_q_instrument.debug(f'treshold = {treshold}, max = {np.max(jitter)}, min = {np.min(jitter)}, '
                                           f'first value = {jitter[0]}')
            over_treshold = np.argmax(jitter > treshold)
            if not self.jitter_startsample:
                self.logger_q_instrument.debug(f'first jitter correction sigal, set startsample'
                                               f' indice at {over_treshold}')
                self.jitter_startsample = over_treshold
                return data
            else:
                shift = self.jitter_startsample - over_treshold
                self.logger_q_instrument.debug(f'shifting pulse with {shift} samples')
                if shift == 0:
                    return data
                # data is shifted, data outside boundary replaced with neighbour value. This is acceptable because
                # shift is maximum one sample
                elif shift > 0:
                    data = np.hstack((data[(shift-1):-1], np.ones(shift)*data[-1]))
                else:
                    shift = abs(shift)
                    data = np.hstack((np.ones(shift)*data[0], data[0:-shift]))

        return data

    def _plot_single_pulse(self, data):
        """
        Select only the datachannel from the data and make a corresponding timevector to emit to plotwindow.
        Compress the data if number of samples is above a set value (avoid plotting extremely lengthy data)
        :param data: single event measurement [channels][samples]
        :returns: times (time array), data (data array), plotinfo (string)
        """
        self.logger_q_instrument.info('selecting plotdata single pulse')
        samples = len(data)
        if samples > self.max_plot_points:
            times, data, plotinfo, _ = self._compress_long_data(data, samples)
        else:
            plotinfo = 'uncompressed data'
            times = np.linspace(0, (samples - 1) / self.sample_rate, samples)

        return times, data, plotinfo

    @staticmethod
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

    def _compress_long_data(self, data, samples):
        """
        Compress the data with a factor which is the smallest power of two to make the number of datapoints smaller
        than the maximum set number of datapoints to plot.

        :param data: data to compress
        :param samples: number of samples in the data
        :returns data: compressed data
        """

        self.logger_q_instrument.info('compressing long data for plotting')
        maindivision = int(samples // self.max_plot_points)
        compressionfactor = self._find_next_power_two(maindivision)

        data = np.reshape(data, (int(samples // compressionfactor), int(compressionfactor)))
        data = np.mean(data, axis=1)
        times = np.linspace(0, (samples - 1) / self.sample_rate, int(samples // compressionfactor))
        mu = unicodedata.lookup('greek small letter mu')
        plotinfo = f'data compressed for plotting in {compressionfactor * 1/self.sample_rate * 1e6} {mu}s timebins'
        return times, data, plotinfo, compressionfactor

    def _average_pulses(self, data):
        """
        Take the average of multiple pulses. To take the average, the pulses need to be normalized.

        :param data: [samples]
        :type data: np.ndarray
        """
        self.pulse_counter += 1
        # subtract the average of the first 30 datapoints.
        data = data - np.mean(data[0:30])
        data = data / np.max(data)
        self.logger_q_instrument.debug(f'tried to divide by {np.max(data)}')
        try:
            self.logger_q_instrument.debug('adding pulse')
            self.average_pulses = (self.average_pulses * (self.pulse_counter - 1) + data) / self.pulse_counter
        except ValueError as e:
            self.logger_q_instrument.info(f'could not add pulse to added pulses, resetting added pulses {e}')
            self.pulse_counter = 1
            self.average_pulses = data

    def _compress_average_pulses(self):
        """ Compress the averaged pulses for plotting if the length exceeds the maximum plot length """
        self.logger_q_instrument.info('creating time vector and plotinfo averageing')
        samples = len(self.average_pulses)
        if samples > self.max_plot_points:
            times, data, compinfo, _ = self._compress_long_data(self.average_pulses, samples)
        else:
            self.logger_q_instrument.debug('uncompressed data')
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
        self.logger_q_instrument.info('counting single photon counts over treshold')
        self.pulse_counter += 1

        data_over_treshold = data > self.single_photon_counting_treshold
        filter_doublecounts = np.array([1, 0])
        data_corrected = data_over_treshold > sp.maximum_filter(
            data_over_treshold, footprint=filter_doublecounts, mode='constant', cval=-np.inf)
        data_corrected = data_corrected.astype(int)
        self.logger_q_instrument.debug(f'single photon treshold = {self.single_photon_counting_treshold}')
        self.logger_q_instrument.debug(f'single photon over treshold = {data_over_treshold}')
        self.logger_q_instrument.debug(f'single photon counts: {data_corrected}')
        try:
            self.logger_q_instrument.debug('adding pulse single photon counts')
            self.single_photon_counts += data_corrected
        except ValueError as e:
            self.logger_q_instrument.info(f'number of samples changed, resetting single photon counts and pulse '
                                          f'counter. full error message: {e}')
            self.pulse_counter = 1
            self.single_photon_counts = data_corrected

    def set_compression_factor(self, factor: str):
        """ Sets the compression factor for single photon counting """
        self.logger_q_instrument.info(f'setting single photon compression factor to {factor}')
        try:
            self.compression_factor = CAENlib.COMPRESSIONFACTORS[self.model][factor]
        except KeyError:
            self.compression_factor = CAENlib.COMPRESSIONFACTORS[self.model].values()[0]
            raise Warning(f'Incorrect compression factor key, set compression '
                          f'factor to lowest value of {self.compression_factor}')

    def _compress_single_photon_counts(self):
        """
        Compress single photon counts by the set compression factor for plotting. Do check if chosen compression
        factor is enough.
        """

        self.logger_q_instrument.debug(f'compressing single photon counts with {self.compression_factor}')
        # factors are chosen such that this has 0 remainder
        samples = len(self.single_photon_counts)
        bins = samples // self.compression_factor
        data = np.reshape(self.single_photon_counts, (bins, self.compression_factor))
        data = np.mean(data, axis=1)
        data = data - np.min(data)
        # only divide by max data if not all zero
        if maxdata := np.max(data):
            data = data/maxdata
        # check length again to see if additional compression is needed
        if (samples := len(data)) > self.max_plot_points:
            self.logger_q_instrument.debug('additional compression single photon counts needed')
            times, data, _, additional_compressionfactor = self._compress_long_data(data, samples)
            totalfactor = self.compression_factor*additional_compressionfactor
            mu = unicodedata.lookup('greek small letter mu')
            plotinfo = f'{self.pulse_counter} pulses - for plotting, compression increased by' \
                       f' {additional_compressionfactor} to {totalfactor/self.sample_rate*1_000_000:.3f} {mu}s'
        else:
            self.logger_q_instrument.debug('no additional compression done')
            times = np.linspace(0, (samples - 1)*self.compression_factor / self.sample_rate, samples)
            plotinfo = f'{self.pulse_counter} pulses'

        return times, data, plotinfo

    @pyqtSlot()
    def set_active_channels(self):
        """ set the channel mask to the data channel and the jitter channel if enabled """
        if self.jitter_correction_enabled:
            self.logger_q_instrument.info(
                f'setting data channel to {self.data_channel}, jitter channel to {self.jitter_channel}')
            channels = [self.data_channel, self.jitter_channel]
        else:
            self.logger_q_instrument.info(f'setting data channel to {self.data_channel}, no jitter channel')
            channels = [self.data_channel]

        self.active_channels = channels

    @pyqtSlot(int)
    def set_dc_offset_data_channel(self, offset):
        """ Set the dc offset of the data channel """
        self.logger_q_instrument.info(f'setting the DC offset of the data channel to {offset}')
        offset = int(offset)
        channel = self.data_channel
        self.set_dc_offset(channel, offset)

    @pyqtSlot(int)
    def set_post_trigger_size(self, size: int):
        """ Parse the post trigger size as a function call """
        self.logger_q_instrument.info(f'setting post trigger size to {size}')
        self.post_trigger_size = size

    @pyqtSlot()
    def check_parameters(self):
        """ Emit parameters/settings for initialization of digitizer gui """
        self.logger_q_instrument.info('reading digitizer parameters, emitting to ui')
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
        self.logger_q_instrument.info('clearing measurements')
        self.single_photon_counts = np.empty(0)
        self.average_pulses = np.empty(0)
        self.jitter_startsample = np.empty(0)
        self.pulse_counter = 0

    @pyqtSlot(int)
    def set_single_photon_counting_treshold(self, treshold):
        """ Set the value at which a spike in the data is counted as a photon """
        self.logger_q_instrument.info(f'setting single photon treshold to {treshold}')
        self.single_photon_counting_treshold = treshold

    @pyqtSlot(str)
    def set_measurement_mode(self, *mode):
        """ 
        Clear the aggregated measurements, then set the measurement mode. Emit new plot axis settings to the 
        plotwindow 
        """

        measurement_mode = mode[0] if mode else self.measurement_mode
        self.logger_q_instrument.debug(f'set measurement mode gui to Qdigitizer = {mode[0]}')

        axisplotdict = {'single pulse': {
                            'title': 'digitizer single pulse',
                            'ylabel': 'adc counts'},
                        'averageing': {
                            'title': 'normalized pulse average',
                            'ylabel': 'normalized intensity'},
                        'single photon counting': {
                            'title': 'single photon counting',
                            'ylabel': 'normalized intensity'}
                        }   
        self.clear_measurement()
        self.measurement_mode = measurement_mode
        self.plotaxis_labels.emit(axisplotdict[measurement_mode])


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
