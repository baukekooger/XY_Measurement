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

    def connect_signals_slots(self):
        self.ui.pushButton_channel_alignment.clicked.connect(self.set_channels)
        self.ui.pushButton_samples_alignment.clicked.connect(self.set_samples)
        self.ui.spinBox_post_trigger_size_alignment.editingFinished.connect(self.set_post_trigger)

    def disconnect_signals_slots(self):
        self.ui.pushButton_channel_alignment.clicked.disconnect()
        self.ui.pushButton_samples_alignment.clicked.disconnect()
        self.ui.spinBox_post_trigger_size_alignment.editingFinished.disconnect()

    @pyqtSlot()
    def set_channels(self):
        # channels need to be provided as a list of ints to the digitizer
        items = self.ui.listWidget_channel_alignment.selectedItems()
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
    def set_samples(self):
        samples = self.ui.comboBox_samples_alignment.currentText()
        if samples == '4000':
            samples_int = 0
        elif samples == '8000':
            samples_int = 1
        QTimer.singleShot(0, lambda x=samples_int: self.digitizer.set_samples(x))
        self.ui.label_samples_indicator.setText(samples)

    @pyqtSlot()
    def set_post_trigger(self):
        size = self.ui.spinBox_post_trigger_size_alignment.value()
        QTimer.singleShot(0, lambda x=size: self.digitizer.set_post_trigger_size(x))
        self.ui.label_Post_trigger_size_indicator.setText(str(size))


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = DigitizerWidget()
    window.show()
    sys.exit(app.exec_())
