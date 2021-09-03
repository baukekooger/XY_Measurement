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
        self.connect_signals_slots()

    def connect_signals_slots(self):
        self.ui.comboBox_channel_alignment.currentTextChanged.connect(self.set_channel)
        self.ui.comboBox_samples_alignment.currentTextChanged.connect(self.set_samples)

    @pyqtSlot(str)
    def set_channel(self, channel):
        # channels need to be provided as a list
        channel = [int(channel)]
        QTimer.singleShot(0, lambda x=channel: self.digitizer.set_samples_channel_single(x))
        self.ui.label_channel_indicator.setText(channel)

    @pyqtSlot(str)
    def set_samples(self, samples):
        if samples == '4000':
            samples_int = 0
        elif samples == '8000':
            samples_int = 1
        QTimer.singleShot(0, lambda x=samples_int: self.digitizer.set_samples(x))
        self.ui.label_samples_indicator.setText(samples)

    @pyqtSlot(int)
    def set_post_trigger(self, size):
        QTimer.singleShot(0, lambda x=size: self.digitizer.set_post_trigger_size(x))
        self.ui.label_Post_trigger_size_indicator.setText(str(size))


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = DigitizerWidget()
    window.show()
    sys.exit(app.exec_())
