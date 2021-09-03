import instruments.CAEN as CAENlib
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QMutex, QMutexLocker
import time
import logging
import numpy as np
logging.basicConfig(level=logging.INFO)


class QDigitizer(CAENlib.Digitizer, QObject):
    # Subclassing the digitizer as a QObject to enable threading as a QThread and including
    # custom measuring functions and signals

    measurement_complete = pyqtSignal(np.ndarray)
    measurement_complete_multiple = pyqtSignal(np.ndarray)
    digitizer_parameters = pyqtSignal(list, int, int)

    def __init__(self, digitizer_handle=CAENlib.list_available_devices()[0]):
        CAENlib.Digitizer.__init__(self, digitizer_handle)
        QObject.__init__(self)
        self.mutex = QMutex()
        self.connected = False
        self.measuring = False
        self.timeout = None

    def init_device(self):
        self.record_length = 0
        self.max_num_events = 1
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

    @pyqtSlot(int)
    def measure_multiple(self, number_of_pulses):
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
        self.measuring = False
        return data

    @pyqtSlot()
    def measure(self):
        self.measuring = True
        t1 = time.time()
        logging.info(f'digitizer started at {t1}')
        active_channels = list(self.active_channels)
        with(QMutexLocker(self.mutex)):
            data = self.read_data()[active_channels]
        data = data[:, 0, :]
        t2 = time.time()
        logging.info(f'digitizer measured single pulse in {t2-t1:.3f} seconds')
        self.measurement_complete.emit(data)
        self.measuring = False
        return data

    @pyqtSlot(list)
    def set_active_channel_single(self, channel):
        channel = [int(channel)]
        self.active_channels = channel

    @pyqtSlot(int)
    def set_offset_channel_single(self, offset):
        # only works when a single channel is active
        offset = int(offset)
        channel = list(self.active_channels)[0]
        self.set_dc_offset(channel, offset)

    @pyqtSlot(int)
    def set_samples(self, samples):
        self.record_length = samples

    @pyqtSlot(int)
    def set_post_trigger_size(self, size):
        self.post_trigger_size = size

    @pyqtSlot()
    def check_settings(self):
        active_channels = list(self.active_channels)
        samples = int(self.record_length)
        post_trigger_size = int(self.post_trigger_size)
        self.digitizer_parameters.emit(active_channels, samples, post_trigger_size)
