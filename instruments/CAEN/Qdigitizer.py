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

    # measurement_complete_multiple = pyqtSignal(np.ndarray)
    # measurement_done_multiple = pyqtSignal()
    # single_photon_counting_signal = pyqtSignal()
    digitizer_parameters = pyqtSignal(list, list, list, int, int)

    def __init__(self):
        CAENlib.Digitizer.__init__(self)
        QObject.__init__(self)
        self.mutex = QMutex()
        self.connected = False
        self.measuring = False
        self.timeout = None
        self.pulses_per_measurement = 1
        self.last_pulses = []
        self.measuring_mode = 'single pulse'
        self.data_channel = 0
        self.single_photon_counting_treshold = None
        self.single_photon_counting_channel = None
        self.single_photon_counts = None
        self.single_photon_counts_compressed = None
        self.compress_data = False
        self.compression_factor = None
        self.jitter_correction_enabled = False
        self.jitter_channel = None

    def init_device(self):
        self.record_length = 0
        self.max_num_events_blt = 1
        self.post_trigger_size = 90
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
    def measure_multiple(self, *pulses):
        if not pulses:
            number_of_pulses = self.number_of_pulses
        else:
            number_of_pulses = pulses[0]
        self.measuring = True
        t1 = time.time()
        logging.info(f'digitizer started at {t1}')
        active_channels = list(self.active_channels)
        data = np.empty((len(active_channels), number_of_pulses, self.record_length))
        with(QMutexLocker(self.mutex)):
            for i in range(number_of_pulses):
                data[:, i, :] = self.read_data()[active_channels, 0, :]
        t2 = time.time()
        logging.info(f'digitizer sampled {number_of_pulses} pulses in {t2-t1:.3f} seconds')
        self.measurement_complete_multiple.emit(data)
        self.measurement_done_multiple.emit()
        self.last_pulses = data
        self.measuring = False
        return data

    @pyqtSlot()
    @pyqtSlot(int)
    def measure(self, *pulses: int):
        """
        Performs repeated single-event measurements with the number of measurements set by the pulses per
        measurement attribute or by the input value. Can also read single measurement.
        """
        if not pulses:
            pulses_per_measurement = self.pulses_per_measurement
        else:
            pulses_per_measurement = pulses
        self.measuring = True
        t1 = time.time()
        logging.info(f'digitizer started measuring {pulses_per_measurement} pulses at {t1}')

        with(QMutexLocker(self.mutex)):
            for pulse in range(pulses_per_measurement):
                data = self.measurement_single_event()
                if self.jittercorrection_enabled:
                    self._jitter_correction(data)
                if self.single_photon_counting_enabled:
                    self._single_photon_counting(data)

        if self.single_photon_counting_enabled:
            self.single_photon_counting_signal.emit(self.single_photon_counts_compressed)
        else:
            self.measurement_complete.emit(data)
        self.measuring = False
        return data

    def _jitter_correction(self, data):
        """
        Corrects for the jitter in the signal which is present with regards to the trigger input.
        :param data: single event measurement [channels][samples]
        :type data: np.ndarray
        """
        pass

    def _single_photon_counting(self, data):
        """
        Register single photon counts by counting the data which is higher than the user-set treshold value.
        Only registers a count when previous value is below treshold. A scipy filter is used for this operation as
        it is much faster than a loop.

        It adds all the counts to the single photon counts attribute which grows with each measurement until it is reset
        :param data: single event measurement [channels][samples]
        :type data: np.ndarray
        :returns: single photon counts
        """
        if not self.single_photon_counts:
            self.single_photon_counts = np.zeros(len(data[0]), dtype=np.int32)

        channel_index = list(self.active_channels).index(self.single_photon_counting_channel)
        data_over_treshold = data[channel_index] > self.single_photon_counting_treshold
        filter_doublecounts = np.array([1, 0])
        data_corrected = data_over_treshold > sp.maximum_filter(
            data_over_treshold, footprint=filter_doublecounts, mode='constant', cval=-np.inf)
        self.single_photon_counts += data_corrected

    def set_compression_factor(self, factor: str):
        """ Sets the compression factor """
        try:
            self.compression_factor = CAENlib.COMPRESSIONFACTORS[self.model][factor]
        except KeyError:
            self.compression_factor = CAENlib.COMPRESSIONFACTORS[self.model].values()[0]
            raise Warning(f'Incorrect compression factor key, set compression '
                          f'factor to lowest value of {self.compression_factor}')

    def compress_single_photon_counts(self):
        """ Compresses the single photon counts into larger timebins to create a signal that has better readability """

        # factors are chosen such that this has 0 remainder
        bins = len(self.single_photon_counts)/self.compression_factor
        self.single_photon_counts_compressed = np.reshape(self.single_photon_counts, (bins, self.compression_factor))
        self.single_photon_counts_compressed = np.sum(self.single_photon_counts_compressed, axis=1)

    @pyqtSlot()
    def set_active_channels(self):
        """ set the channel mask to the data channel and the jitter channel if enabled"""
        if self.jitter_correction_enabled:
            channels = [self.data_channel, self.jitter_channel]
        else:
            channels = [self.data_channel]
        self.active_channels = channels

    @pyqtSlot(int)
    def set_offset_channel_single(self, offset):
        # only works when a single channel is active
        offset = int(offset)
        channel = list(self.active_channels)[0]
        self.set_dc_offset(channel, offset)
        self.check_settings()

    @pyqtSlot(int)
    def set_samples(self, samples):
        self.manual_record_length(samples)
        self.check_settings()

    @pyqtSlot(int)
    def set_post_trigger_size(self, size):
        self.post_trigger_size = size
        self.check_settings()

    @pyqtSlot()
    def check_settings(self):
        """ Emit settings for initialization of digitizer gui """

        available_channels = [str(channel) for channel in range(self.number_of_channels)]
        time_ranges = CAENlib.TIMERANGES[self.model]
        compression_ranges = list(CAENlib.COMPRESSIONFACTORS[self.model].keys())
        dc_offset = self.get_dc_offset(0)
        post_trigger_size = self.post_trigger_size
        self.digitizer_parameters.emit(available_channels, time_ranges,
                                       compression_ranges, dc_offset, post_trigger_size)







