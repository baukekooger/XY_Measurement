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
    measurement_done_multiple = pyqtSignal()
    digitizer_parameters = pyqtSignal(list, list, int, int)

    def __init__(self):
        CAENlib.Digitizer.__init__(self)
        QObject.__init__(self)
        self.mutex = QMutex()
        self.connected = False
        self.measuring = False
        self.timeout = None
        self.number_of_pulses = 10

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
    def set_active_channels(self, channels):
        self.active_channels = channels
        self.check_settings()

    @pyqtSlot(int)
    def set_offset_channel_single(self, offset):
        # only works when a single channel is active
        offset = int(offset)
        channel = list(self.active_channels)[0]
        self.set_dc_offset(channel, offset)
        self.check_settings()

    @pyqtSlot(int)
    def set_samples(self, samples):
        self.record_length = samples
        self.check_settings()

    @pyqtSlot(int)
    def set_post_trigger_size(self, size):
        self.post_trigger_size = size
        self.check_settings()

    @pyqtSlot()
    def check_settings(self):
        available_channels = [str(channel) for channel in range(self.number_of_channels)]
        active_channels = list(self.active_channels)
        samples = int(self.record_length)
        post_trigger_size = int(self.post_trigger_size)
        self.digitizer_parameters.emit(available_channels, active_channels, samples, post_trigger_size)

