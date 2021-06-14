from PyQt5 import QtWidgets
from gui_design.spectrometer import Ui_Form
from instruments.OceanOptics.spectrometer_pyqt import QSpectrometer


class SpectrometerWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.spectrometer = QSpectrometer()

    def connect_signals_slots(self):
        self.ui.doubleSpinBox_integration_time_alignment.editingFinished.connect(
            lambda: setattr(self.spectrometer, 'integrationtime',
                            self.ui.doubleSpinBox_integration_time_alignment.value()))
        self.ui.doubleSpinBox_averageing_alignment.editingFinished.connect(
            lambda: setattr(self.spectrometer, 'average_measurements',
                            self.ui.doubleSpinBox_averageing_alignment.value()))
        self.ui.pushButton_dark.clicked.connect(
            self.spectrometer.measure_dark)
        self.ui.pushButton_reset.clicked.connect(
            self.spectrometer.clear_dark)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = SpectrometerWidget()
    window.show()
    sys.exit(app.exec_())

