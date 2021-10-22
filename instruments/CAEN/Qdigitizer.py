import instruments.CAEN as CAENlib
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

    measurement_complete_multiple = pyqtSignal(np.ndarray)
    measurement_done_multiple = pyqtSignal()
    single_photon_counting_signal = pyqtSignal()
    parameters = pyqtSignal(list, list, list, int, int)
    redraw_plot = pyqtSignal()

    def __init__(self):
        CAENlib.Digitizer.__init__(self)
        QObject.__init__(self)
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
        self.single_photon_counts = np.empty(0)
        self.pulse_counter = 0
        self.compression_factor = 1
        self.jitter_correction_enabled = False
        self.jitter_channel = 1
        self.max_plot_points = 2e5

    def init_device(self):
        self.record_length = 0
        self.max_num_events_blt = 1
        self.post_trigger_size = 90
        self.set_active_channels()
        self.acquisition_mode = CAENlib.AcqMode.SW_CONTROLLED
        self.external_trigger_mode = CAENlib.TriggerMode.ACQ_ONLY
        self.external_trigger_level = CAENlib.IOLevel.TTL

    @pyqtSlot()
    def connect(self):
        self.connect_device()
        self.connected = True
        self.init_device()

    @pyqtSlot()
    def disconnect(self):
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
        self.measuring = True
        if not pulses:
            pulses_per_measurement = self.pulses_per_measurement
        else:
            pulses_per_measurement = pulses
        tstart = time.time()
        logging.info(f'digitizer started measuring {pulses_per_measurement} pulse(s)')
        with(QMutexLocker(self.mutex)):
            for pulse in range(pulses_per_measurement):
                data = self.measurement_single_event()
                if self.jitter_correction_enabled:
                    self._jitter_correction(data)
                if self.measuring_mode == 'single photon counting':
                    self._single_photon_counting(data)
                tcurrent = time.time()
                if self.polltime_enabled and (tcurrent - tstart) > self.polltime_measurement:
                    logging.info(f'QDigitizer measurement past polltime, finishing after {pulse + 1} pulses')
                    break
            logging.info(f'QDigitizer measurement finishing after {pulse + 1} pulses')

        if self.measuring_mode == 'single pulse':
            times, data, plotinfo = self._plot_single_pulse(data)
            self.measurement_complete.emit(times, data, plotinfo)
        elif self.measuring_mode == 'single photon counting':
            self.pulse_counter += self.pulses_per_measurement
            times, data = self._compress_single_photon_counts()
            plotinfo = f'{self.pulse_counter} pulses'
            self.measurement_complete.emit(times, data, plotinfo)

        self.measuring = False
        return data

    def _jitter_correction(self, data):
        """
        Corrects for the jitter in the signal which is present with regards to the trigger input.
        :param data: single event measurement [channels][samples]
        :type data: np.ndarray
        """
        pass

    def _plot_single_pulse(self, data):
        """
        Select only the datachannel from the data and make a corresponding timevector to emit to plotwindow.
        Compress the data if number of samples is above a set value (avoid plotting extremely lengthy data)
        :param data: single event measurement [channels][samples]
        :returns: times (time array), data (data array), plotinfo (string)
        """
        logging.info('QDigitizer: selecting plotdata single pulse')
        if not self.jitter_correction_enabled:
            data = data[0]
        else:
            data = data[0] if self.data_channel < self.jitter_channel else data[1]
        samples = len(data)
        if samples > self.max_plot_points:
            times, data, plotinfo = self._compress_single_pulse(data, samples)
        else:
            plotinfo = 'uncompressed data'
            times = np.linspace(0, (samples - 1) / self.sample_rate, samples)

        return times, data, plotinfo

    def _compress_single_pulse(self, data, samples):
        """
        Compress the data to a length close to the max number of datapoints for plotting purposes
        :param data: data to compress
        :param samples: number of samples in the data
        :returns data: compressed data
        """

        logging.info('QDigitizer: compressing samples single pulse plot')
        maindivision = samples // self.max_plot_points
        if maindivision == 1:
            compfactor = 2
        else:
            # the number of samples can always be divided by two for the implemented timeranges
            compfactor = maindivision + 1 if maindivision % 2 != 0 else maindivision

        data = np.reshape(data, (samples // compfactor, compfactor))
        data = np.mean(data, axis=1)
        times = np.linspace(0, (samples - 1) / self.sample_rate, samples // compfactor)
        plotinfo = f'data compressed with factor {compfactor}'
        return times, data, plotinfo

    def _single_photon_counting(self, data):
        """
        Register single photon counts by counting the data which is higher than the user-set treshold value.
        Only registers a count when previous value is below treshold. A scipy filter is used for this operation as
        it is much faster than a loop.

        It adds all the counts to the single photon counts attribute which grows with each measurement until it is reset
        :param data: single event measurement [channels][samples]
        :type data: np.ndarray
        :returns: single photon counts array
        """
        if not any(self.single_photon_counts):
            self.single_photon_counts = np.zeros(len(data[0]), dtype=np.int32)

        channel_index = list(self.active_channels).index(self.data_channel)
        data_over_treshold = data[channel_index] > self.single_photon_counting_treshold
        filter_doublecounts = np.array([1, 0])
        data_corrected = data_over_treshold > sp.maximum_filter(
            data_over_treshold, footprint=filter_doublecounts, mode='constant', cval=-np.inf)
        try:
            self.single_photon_counts += data_corrected
        except ValueError as e:
            logging.warning(f'number of samples changed, resetting single photon counts and pulse counter. '
                            f'full error message: {e}')
            self.pulse_counter = 0
            self.single_photon_counts = data_corrected

    def set_compression_factor(self, factor: str):
        """ Sets the compression factor """
        logging.info(f'setting single photon compression factor to {factor}')
        try:
            self.compression_factor = CAENlib.COMPRESSIONFACTORS[self.model][factor]
        except KeyError:
            self.compression_factor = CAENlib.COMPRESSIONFACTORS[self.model].values()[0]
            raise Warning(f'Incorrect compression factor key, set compression '
                          f'factor to lowest value of {self.compression_factor}')

    def _compress_single_photon_counts(self):
        """ Compress single photon counts by the compression factor """

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
            channels = [self.data_channel, self.jitter_channel]
        else:
            channels = [self.data_channel]

        self.active_channels = channels

    @pyqtSlot(int)
    def set_dc_offset_data_channel(self, offset):
        """ Set the dc offset of the data channel """
        logging.info(f'setting the DC offset of the data channel to {offset}')
        offset = int(offset)
        channel = self.data_channel
        self.set_dc_offset(channel, offset)

    @pyqtSlot(int)
    def set_post_trigger_size(self, size: int):
        """ Parse the post trigger size as a function call """
        logging.info(f'setting post trigger size to {size}')
        self.post_trigger_size = size

    @pyqtSlot()
    def check_parameters(self):
        """ Emit parameters/settings for initialization of digitizer gui """
        logging.info('reading digitizer parameters, emitting to ui')
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
        logging.info('Qdigitizer: clearing measurements')
        self.single_photon_counts = np.empty(0)
        self.pulse_counter = 0

    @pyqtSlot(int)
    def set_single_photon_counting_treshold(self, treshold):
        """ Set the value at which a spike in the data is counted as a photon """
        logging.info(f'QDigitizer: setting single photon treshold to {treshold}')
        self.single_photon_counting_treshold = treshold


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
