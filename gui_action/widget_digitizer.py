from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QTimer, QMutex, QMutexLocker
from gui_design.digitizer import Ui_Form
from instruments.CAEN.Qdigitizer import QDigitizer
from instruments.CAEN.definitions import TIMERANGES, COMPRESSIONFACTORS
import time
import logging


class DigitizerWidget(QtWidgets.QWidget):
    """
    Control class for the digitizer widget

    Connects all the ui signals to actions on the digitizer.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger_widget = logging.getLogger('gui.Digitizer')
        self.logger_widget.info('init digitizer widget ui')
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.digitizer = QDigitizer()

    def connect_signals_slots(self):
        """ Connect all ui signals"""
        self.logger_widget.info('connecting all signals digitizerwidget')
        self.digitizer.parameters.connect(self.init_ui)
        self.digitizer.check_parameters() # direct calling to make sure function is executed before continuing
        time.sleep(0.01)
        self.ui.comboBox_measurement_mode_alignment.currentTextChanged.connect(self.digitizer.set_measurement_mode)
        self.ui.comboBox_measurement_mode_alignment.currentTextChanged.connect(self.logmode)
        self.ui.comboBox_data_channel_alignment.currentTextChanged.connect(self.set_data_channel)
        self.ui.comboBox_data_channel_experiment.currentTextChanged.connect(self.set_data_channel)
        self.ui.comboBox_time_range_alignment.currentTextChanged.connect(self.set_time_range)
        self.ui.spinBox_dc_offset_alignment.valueChanged.connect(self.digitizer.set_dc_offset_data_channel)
        self.ui.spinBox_post_trigger_size_alignment.valueChanged.connect(self.digitizer.set_post_trigger_size)
        self.ui.comboBox_jitter_channel_alignment.currentTextChanged.connect(self.set_jitter_channel)
        self.ui.checkBox_jitter_correction_alignment.stateChanged.connect(self.jitter_correction)
        self.ui.comboBox_single_photon_compression_alignment.currentTextChanged.connect(
            self.set_single_photon_compression)
        self.ui.pushButton_single_photon_clear_alignment.clicked.connect(self.digitizer.clear_measurement)
        self.ui.spinBox_single_photon_treshold_alignment.valueChanged.connect(
            self.digitizer.set_single_photon_counting_treshold)
        self.ui.pushButton_clear_averageing_alignment.clicked.connect(self.digitizer.clear_measurement)
        self.set_data_channel(self.ui.comboBox_data_channel_alignment.currentText())

    def disconnect_signals_slots(self):
        """ Disconnect all ui signals """
        self.logger_widget.info('disconnecting all signals digitizerwidget')
        self.ui.comboBox_measurement_mode_alignment.disconnect()
        self.ui.comboBox_data_channel_alignment.disconnect()
        self.ui.comboBox_data_channel_experiment.disconnect()
        self.ui.comboBox_time_range_alignment.disconnect()
        self.ui.spinBox_dc_offset_alignment.disconnect()
        self.ui.spinBox_post_trigger_size_alignment.disconnect()
        self.ui.comboBox_jitter_channel_alignment.disconnect()
        self.ui.comboBox_single_photon_compression_alignment.disconnect()
        self.ui.checkBox_jitter_correction_alignment.disconnect()
        self.ui.pushButton_single_photon_clear_alignment.disconnect()
        self.ui.spinBox_single_photon_treshold_alignment.disconnect()
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
        self.ui.comboBox_single_photon_compression_alignment.addItems(compression_ranges)
        self.ui.spinBox_dc_offset_alignment.setValue(dc_offset)
        self.ui.spinBox_post_trigger_size_alignment.setValue(post_trigger_size)
        self.ui.checkBox_jitter_correction_alignment.setChecked(False)

    @pyqtSlot(str)
    def set_data_channel(self, channel):
        """
        Set the channel for the data (usually the channel connected to the PMT) after modifiying the allowed
        jitterchannels
        """
        self.modify_jitter_channels(channel)
        self.logger_widget.info(f'digitizerwidget: setting data channel to {channel}')
        self.digitizer.data_channel = int(channel)
        QTimer.singleShot(0, self.digitizer.set_active_channels)

    def modify_jitter_channels(self, datachannel: str):
        """
        Check if jitter correction is enabled and disable if it is.
        Note current jitter channel selection.
        Remove the newly selected datachannel from the available jitter channels and update the allowed jitter channels
        Reset jitter channel to initial value unless that was the new datachannel.
        """

        if self.ui.checkBox_jitter_correction_alignment.isChecked():
            self.logger_widget.debug('deselecting the jitter correction checkbox')
            self.ui.checkBox_jitter_correction_alignment.setChecked(False)

        old_jitter_channel_alignment = int(self.ui.comboBox_jitter_channel_alignment.currentText())
        old_jitter_channel_experiment = int(self.ui.comboBox_jitter_channel_experiment.currentText())
        self.logger_widget.debug(f'current jitter channels are {old_jitter_channel_alignment} and'
                                 f'{old_jitter_channel_experiment}')
        # temporarily deconnect signal to prevent choosing new jitterchannel in meantime
        self.ui.checkBox_jitter_correction_alignment.disconnect()

        # define new possible jitterchannels
        all_channels = set(range(self.digitizer.number_of_channels))
        datachannelset = {int(datachannel)}
        jitterchannelsint = list(all_channels.difference(datachannelset))
        jitterchannels = [str(channel) for channel in jitterchannelsint]

        self.ui.comboBox_jitter_channel_alignment.clear()
        self.ui.comboBox_jitter_channel_experiment.clear()
        self.ui.comboBox_jitter_channel_alignment.addItems(jitterchannels)
        self.ui.comboBox_jitter_channel_experiment.addItems(jitterchannels)

        if old_jitter_channel_alignment != int(datachannel):
            self.ui.comboBox_jitter_channel_alignment.setCurrentIndex(
                jitterchannelsint.index(old_jitter_channel_alignment))
        else:
            self.ui.comboBox_jitter_channel_alignment.setCurrentIndex(0)

        if old_jitter_channel_experiment != int(datachannel):
            self.ui.comboBox_jitter_channel_experiment.setCurrentIndex(
                jitterchannelsint.index(old_jitter_channel_experiment))
        else:
            self.ui.comboBox_jitter_channel_experiment.setCurrentIndex(0)

        # reconnect signals
        self.ui.checkBox_jitter_correction_alignment.stateChanged.connect(self.jitter_correction)

    @pyqtSlot(str)
    def set_jitter_channel(self, channel):
        if channel:
            self.logger_widget.info(f'setting digitizer jitter correction channel to {channel}')
            self.digitizer.jitter_channel = int(channel)
            QTimer.singleShot(0, self.digitizer.set_active_channels)

    @pyqtSlot()
    def jitter_correction(self):
        """
        Turn jitter correction on or off.

        Remove longest timerange for slow digitizer when jitter correction enabled. Digitizer can't measure this range
        for multiple channels without giving an error and crashing.
        """

        if self.ui.checkBox_jitter_correction_alignment.isChecked():
            self.logger_widget.info('enabling jitter correction for digitizer')
            # can't measure longest time with multiple channels on the slow digitizer bc of bug.
            if self.ui.comboBox_time_range_alignment.currentText() == '40 ms':
                self.ui.comboBox_time_range_alignment.setCurrentIndex(0)
                self.logger_widget.info('cannot measure longest time with multiple channels, '
                                        'reverting to shortest time range')
            index = self.ui.comboBox_time_range_alignment.findText('40 ms')
            if index != -1:
                self.logger_widget.info('removing longest timerange from digitizer timerange alignment')
                self.ui.comboBox_time_range_alignment.removeItem(index)
            self.digitizer.jitter_correction_enabled = True
            QTimer.singleShot(0, self.digitizer.set_active_channels)
            QTimer.singleShot(0, self.digitizer.clear_measurement)
        else:
            self.logger_widget.info('disabling jitter correction for digitizer')
            self.digitizer.jitter_correction_enabled = False
            self.digitizer.clear_measurement()
            if self.digitizer.model == 'DT5724F':
                if self.ui.comboBox_time_range_alignment.findText('40 ms') == -1:
                    self.logger_widget.info('adding longest timerange to digitizer')
                    self.ui.comboBox_time_range_alignment.addItem('40 ms')
        QTimer.singleShot(0, self.digitizer.set_active_channels)

    @pyqtSlot()
    def jitter_correction_experiment(self):
        """
        Remove largest time value for slowest digitizer from the selection box when jitter correction is turned on,
        digitizer gives error at this value when multiple channels are enabled.
        """

        if not self.ui.checkBox_jitter_correction_experiment.isChecked:
            if self.ui.comboBox_time_range_experiment.currentText() == '40 ms':
                self.ui.comboBox_time_range_experiment.setCurrentIndex(0)
                self.logger_widget.info('digitizerwidget: set chosen timerange to shortest')
            index = self.ui.comboBox_time_range_alignment.findText('40 ms')
            if index != -1:
                self.logger_widget.info('digitizerwidget: removing longest timerange from timerange experiment')
                self.ui.comboBox_time_range_alignment.removeItem(index)
        else:
            if self.digitizer.model == 'DT5724F':
                if self.ui.comboBox_time_range_experiment.findText('40 ms') == -1:
                    self.logger_widget.info('digitizerwidget: adding longest timerange to experiment')
                    self.ui.comboBox_time_range_alignment.addItem('40 ms')

    @pyqtSlot(str)
    def set_time_range(self, timerange):
        """ Parse the selected timerange to the digitizer """
        with(QMutexLocker(self.digitizer.mutex)):
            self.logger_widget.info(f'setting digitizer time range to {timerange}')
            value = TIMERANGES[self.digitizer.model].index(timerange)
            self.digitizer.record_length = value

    @pyqtSlot(str)
    def set_single_photon_compression(self, factor):
        """ Parse the selected time compression for single photon counting to the digitizer """
        self.logger_widget.info(f'digitizerwidget: selected compressionfactor {factor}')
        try:
            compressionfactor = COMPRESSIONFACTORS[self.digitizer.model][factor]
        except KeyError:
            self.logger_widget.error(
                f'digitizerwidget: compressionfactor {factor} not found in compressionfactors dict, setting'
                f'to no compression')
            compressionfactor = 1
            self.ui.comboBox_single_photon_compression_alignment.setCurrentIndex(0)
        self.digitizer.compression_factor = compressionfactor

    @pyqtSlot(str)
    def logmode(self, mode):
        self.logger_widget.info(f'picked mode {mode} from gui')


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers
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
