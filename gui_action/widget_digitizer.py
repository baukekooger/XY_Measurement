from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QTimer, QMutex, QMutexLocker
from gui_design.digitizer import Ui_Form
from instruments.CAEN.Qdigitizer import QDigitizer
from instruments.CAEN.definitions import TIMERANGES, COMPRESSIONFACTORS
import logging


class DigitizerWidget(QtWidgets.QWidget):
    """
    Control class for the digitizer widget

    Connects all the ui signals to actions on the digitizer.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('gui.Digitizer')
        self.logger.info('init digitizer widget ui')
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.digitizer = QDigitizer()

    def connect_signals_slots(self):
        """ Connect all ui signals"""
        self.logger.info('connecting all signals digitizerwidget')
        self.digitizer.parameters.connect(self.init_ui)
        self.digitizer.check_parameters()  # direct calling to make sure function is executed before continuing
        self.ui.comboBox_measurement_mode_alignment.currentTextChanged.connect(self.set_measurement_mode)
        self.ui.comboBox_data_channel_alignment.currentTextChanged.connect(self.set_data_channel)
        self.ui.comboBox_time_range_alignment.currentTextChanged.connect(self.set_time_range)
        self.ui.spinBox_dc_offset_alignment.valueChanged.connect(self.digitizer.set_dc_offset_data_channel)
        self.ui.spinBox_post_trigger_size_alignment.valueChanged.connect(self.digitizer.set_post_trigger_size)
        self.ui.comboBox_jitter_channel_alignment.currentTextChanged.connect(self.set_jitter_channel)
        self.ui.checkBox_jitter_correction_alignment.stateChanged.connect(self.jitter_correction_alignment)
        self.ui.checkBox_jitter_correction_experiment.stateChanged.connect(self.jitter_correction_experiment)
        self.ui.comboBox_single_photon_compression_alignment.currentTextChanged.connect(
            self.set_single_photon_compression)
        self.ui.pushButton_single_photon_clear_alignment.clicked.connect(self.digitizer.clear_measurement)
        self.ui.spinBox_single_photon_treshold_alignment.valueChanged.connect(
            self.digitizer.set_single_photon_counting_treshold)
        self.ui.pushButton_clear_averageing_alignment.clicked.connect(self.digitizer.clear_measurement)

    def disconnect_signals_slots(self):
        """ Disconnect all ui signals """
        self.logger.info('disconnecting all signals digitizerwidget')
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

    @pyqtSlot(list, list, list, int, int)
    def init_ui(self, available_channels, time_ranges, compression_ranges, dc_offset, post_trigger_size):
        """
        Populate the digitizer ui based on the digitizer model and settings.

        :param available_channels: channels available on the digitizer
        :param time_ranges: available time ranges corresponding to number of samples
        :param compression_ranges: different ranges for compressing the single photon count data
        :param dc_offset: dc offset of the PMT channel
        :param post_trigger_size: size of part of the signal after the trigger in percent
        """
        self.ui.comboBox_data_channel_alignment.clear()
        self.ui.comboBox_jitter_channel_alignment.clear()
        self.ui.comboBox_data_channel_experiment.clear()
        self.ui.comboBox_jitter_channel_experiment.clear()
        self.ui.comboBox_data_channel_alignment.addItems(available_channels)
        self.ui.comboBox_jitter_channel_alignment.addItems(available_channels)
        self.ui.comboBox_data_channel_experiment.addItems(available_channels)
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

    @pyqtSlot(str)
    def set_measurement_mode(self, mode):
        """ Set the measurement mode of the digitizer """
        self.logger.info(f'changing digitizer measuring mode to {mode}')
        self.digitizer.measuring_mode = mode

    @pyqtSlot(str)
    def set_data_channel(self, channel):
        """ Set the channel for the data (usually the channel connected to the PMT) """
        self.logger.info(f'digitizerwidget: setting data channel to {channel}')
        self.digitizer.data_channel = int(channel)
        QTimer.singleShot(0, self.digitizer.set_active_channels)

    @pyqtSlot(str)
    def set_jitter_channel(self, channel):
        self.logger.info(f'setting digitizer jitter correction channel to {channel}')
        self.digitizer.jitter_channel = int(channel)
        QTimer.singleShot(0, self.digitizer.set_active_channels)

    @pyqtSlot()
    def jitter_correction_alignment(self):
        """
        Turn jitter correction on or off.

        Remove longest timerange for slow digitizer when jitter correction enabled. Digitizer can't measure this range
        for multiple channels without giving an error and crashing.
        """

        if not self.ui.checkBox_jitter_correction_alignment.isChecked:
            self.logger.info('enabling jitter correction for digitizer')
            # can't measure longest time with multiple channels on the slow digitizer bc of bug.
            if self.ui.comboBox_time_range_alignment.currentText() == '40 ms':
                self.ui.comboBox_time_range_alignment.setCurrentIndex(0)
                self.logger.info('cannot measure longest time with multiple channels, reverting to shortest time range')
            index = self.ui.comboBox_time_range_alignment.findText('40 ms')
            if index != -1:
                self.logger.info('removing longest timerange from digitizer timerange alignment')
                self.ui.comboBox_time_range_alignment.removeItem(index)
            self.digitizer.jitter_correction_enabled = True
            self.digitizer.clear_measurement()
        else:
            self.logger.info('disabling jitter correction for digitizer')
            self.digitizer.jitter_correction_enabled = False
            self.digitizer.clear_measurement()
            if self.digitizer.model == 'DT5724F':
                if self.ui.comboBox_time_range_alignment.findText('40 ms') == -1:
                    self.logger.info('adding longest timerange to digitizer')
                    self.ui.comboBox_time_range_alignment.addItem('40 ms')
        QTimer.singleShot(0, self.digitizer.set_active_channels)

    @pyqtSlot()
    def jitter_correction_experiment(self):
        """
        Remove largest time value for slowest digitizer from the selection box when jitter correction is turned on,
        digitizer gives error at this value when multiple channels are enabled.
        """

        if not self.ui.checkBox_jitter_correction_experment.isChecked:
            if self.ui.comboBox_time_range_experiment.currentText() == '40 ms':
                self.ui.comboBox_time_range_experiment.setCurrentIndex(0)
                self.logger.info('digitizerwidget: set chosen timerange to shortest')
            index = self.ui.comboBox_time_range_alignment.findText('40 ms')
            if index != -1:
                self.logger.info('digitizerwidget: removing longest timerange from timerange experiment')
                self.ui.comboBox_time_range_alignment.removeItem(index)
        else:
            if self.digitizer.model == 'DT5724F':
                if self.ui.comboBox_time_range_experiment.findText('40 ms') == -1:
                    self.logger.info('digitizerwidget: adding longest timerange to experiment')
                    self.ui.comboBox_time_range_alignment.addItem('40 ms')

    @pyqtSlot(str)
    def set_time_range(self, timerange):
        """ Parse the selected timerange to the digitizer """
        with(QMutexLocker(self.digitizer.mutex)):
            self.logger.info(f'setting digitizer time range to {timerange}')
            value = TIMERANGES[self.digitizer.model].index(timerange)
            self.digitizer.record_length = value

    @pyqtSlot(str)
    def set_single_photon_compression(self, factor):
        """ Parse the selected time compression for single photon counting to the digitizer """
        self.logger.info(f'digitizerwidget: selected compressionfactor {factor}')
        try:
            compressionfactor = COMPRESSIONFACTORS[self.digitizer.model][factor]
        except KeyError:
            self.logger.error(
                f'digitizerwidget: compressionfactor {factor} not found in compressionfactors dict, setting'
                f'to no compression')
            compressionfactor = 1
            self.ui.comboBox_single_photon_compression_alignment.setCurrentIndex(0)
        self.digitizer.compression_factor = compressionfactor


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config

    pathlogging = Path(__file__).parent.parent / 'loggingconfig.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    # setup pyqt app
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = DigitizerWidget()
    window.show()
    sys.exit(app.exec_())
