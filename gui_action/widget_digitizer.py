from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QTimer
from gui_design.digitizer import Ui_Form
from instruments.CAEN.Qdigitizer import QDigitizer


class DigitizerWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.digitizer = QDigitizer()
        self.sample_rate = None
        # maximum number that was found to never give errors in reading the data

    def connect_signals_slots(self):
        self.digitizer.digitizer_parameters.connect(self.update_params)
        self.digitizer.check_settings()  # direct calling to make sure function is executed before continuing
        self.ui.comboBox_measurement_mode_alignment.currentTextChanged.connect(self.set_measurement_mode)
        self.ui.comboBox_data_channel_alignment.currentTextChanged.connect(self.set_data_channel)
        self.ui.comboBox_time_range_alignment.currentTextChanged.connect(self.set_time_range)
        self.ui.spinBox_dc_offset_alignment.valueChanged.connect(self.set_dc_offset)
        self.ui.spinBox_post_trigger_size_alignment.valueChanged.connect(self.set_post_trigger)
        self.ui.comboBox_jitter_channel_alignment.currentTextChanged.connect(self.set_jitter_channel)
        self.ui.checkBox_jitter_correction_alignment.isChecked.connect(self.enable_jitter_correction)
        self.ui.comboBox_single_photon_compression_alignment.currentTextChanged.connect(
            self.set_single_photon_compression)
        self.ui.pushButton_single_photon_clear_alignment.clicked.connect(self.clear_single_photon)
        self.ui.spinBox_single_photon_treshold_alignment.valueChanged.connect(self.set_treshold_single_photon)

    def disconnect_signals_slots(self):
        self.ui.comboBox_measurement_mode_alignment.currentTextChanged.disconnect()
        self.ui.comboBox_data_channel_alignment.currentTextChanged.disconnect()
        self.ui.comboBox_time_range_alignment.currentTextChanged.disconnect()
        self.ui.spinBox_dc_offset_alignment.valueChanged.disconnect()
        self.ui.spinBox_post_trigger_size_alignment.valueChanged.disconnect()
        self.ui.comboBox_jitter_channel_alignment.currentTextChanged.disconnect()
        self.ui.checkBox_jitter_correction_alignment.isChecked.disconnect()
        self.ui.comboBox_single_photon_compression_alignment.currentTextChanged.disconnect()
        self.ui.pushButton_single_photon_clear_alignment.clicked.disconnect()
        self.ui.spinBox_single_photon_treshold_alignment.valueChanged.disconnect()
        self.digitizer.digitizer_parameters.disconnect()

    @pyqtSlot()
    def set_measurement_mode(self, mode):
        """ Set the measurement mode of the digitizer """
        self.digitizer.measuring_mode = mode

    @pyqtSlot()
    def set_data_channel(self, channel):
        self.digitizer.data_channel = int(channel)
        QTimer.singleShot(0, self.digitizer.set_active_channels)

    @pyqtSlot()
    def set_jitter_channel(self, channel):
        self.digitizer.jitter_channel = int(channel)
        QTimer.singleShot(0, self.digitizer.set_active_channels)


    @pyqtSlot()
    def set_time_range(self, range):
        pass

    @pyqtSlot()
    def set_channels(self):
        """ parses the selected channels from the listitem to the digitizer """

        items = self.ui.listWidget_channels_alignment.selectedItems()
        if any(items):
            channels = [item.text() for item in items]
            channels_int = [int(string) for string in channels]
            if len(channels) > 1:
                channel_str = ', '.join(channels)
            else:
                channel_str = channels[0]
            QTimer.singleShot(0, lambda x=channels_int: self.digitizer.set_active_channels(x))
            self.ui.label_channel_indicator.setText(channel_str)

    @pyqtSlot()
    def set_integration_time(self):
        """ sets number of samples to be taken by digitizer from given integration time, checks for maximum """
        inttime = self.ui.spinBox_integration_time_alignment.value()
        samples = inttime/1e9 * self.sample_rate if \
            inttime/1e9 * self.sample_rate <= self.max_samples else self.max_samples
        samples = int(samples)
        QTimer.singleShot(0, lambda x=samples: self.digitizer.set_samples(x))
        self.ui.label_integration_time_indicator.setText(str(samples))

    @pyqtSlot()
    def set_post_trigger(self):
        size = self.ui.spinBox_post_trigger_size_alignment.value()
        QTimer.singleShot(0, lambda x=size: self.digitizer.set_post_trigger_size(x))
        self.ui.label_Post_trigger_size_indicator.setText(str(size))

    @pyqtSlot(list, list, list, int, int)
    def init_ui(self, available_channels, time_ranges, compression_ranges, dc_offset, post_trigger_size):
        """
        Populate the digitizer ui at based on the digitizer model and settings.

        :param available_channels: channels available on the digitizer
        :param time_ranges: available time ranges corresponding to number of samples
        :param compression_ranges: different ranges for compressing the single photon count data
        :param dc_offset: dc offset of the PMT channel
        :param post_trigger_size: size of part of the signal after the trigger in percent
        """
        self.ui.comboBox_pmt_channel_alignment.clear()
        self.ui.comboBox_jitter_channel_alignment.clear()
        self.ui.comboBox_pmt_channel_experiment.clear()
        self.ui.comboBox_jitter_channel_experiment.clear()
        self.ui.comboBox_pmt_channel_alignment.addItems(available_channels)
        self.ui.comboBox_jitter_channel_alignment.addItems(available_channels)
        self.ui.comboBox_pmt_channel_experiment.addItems(available_channels)
        self.ui.comboBox_jitter_channel_experiment.addItems(available_channels)
        self.ui.comboBox_time_range_alignment.clear()
        self.ui.comboBox_time_range_experiment.clear()
        self.ui.comboBox_time_range_alignment.addItems(time_ranges)
        self.ui.comboBox_time_range_experiment.addItems(time_ranges)
        self.ui.comboBox_single_photon_compression_alignment.clear()
        self.ui.comboBox_single_photon_compression_experiment.clear()
        self.ui.comboBox_single_photon_compression_alignment.addItems(compression_ranges)
        self.ui.comboBox_single_photon_compression_experiment.addItems(compression_ranges)
        self.ui.spinBox_dc_offset_alignment.setValue(dc_offset)
        self.ui.spinBox_post_trigger_size_alignment.setValue(post_trigger_size)
        self.ui.checkBox_jitter_correction_alignment.setChecked(False)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = DigitizerWidget()
    window.show()
    sys.exit(app.exec_())
