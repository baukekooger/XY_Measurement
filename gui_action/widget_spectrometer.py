from PyQt5 import QtWidgets
from gui_design.spectrometer import Ui_Form
from instruments.OceanOptics.spectrometer import QSpectrometer
from PyQt5.QtCore import pyqtSlot


class SpectrometerWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.spectrometer = QSpectrometer()

    def connect_signals_slots(self):
        self.spectrometer.measurement_parameters.connect(self.update_parameters)
        self.ui.spinBox_integration_time_alignment.editingFinished.connect(
            lambda: setattr(self.spectrometer, 'integrationtime',
                            self.ui.spinBox_integration_time_alignment.value()))
        self.ui.spinBox_averageing_alignment.editingFinished.connect(
            lambda: setattr(self.spectrometer, 'average_measurements',
                            self.ui.spinBox_averageing_alignment.value()))
        self.ui.pushButton_dark.clicked.connect(
            self.spectrometer.measure_dark)
        self.ui.pushButton_reset.clicked.connect(
            self.spectrometer.clear_dark)

    @pyqtSlot(int, int)
    def update_parameters(self, integrationtime, average_measurements):
        self.ui.label_integration_time_alignment_value.setText(f'{integrationtime} ms')
        self.ui.label_averageing_alignment_value.setText(f'{average_measurements}')


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = SpectrometerWidget()
    window.show()
    sys.exit(app.exec_())

