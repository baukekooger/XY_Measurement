from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
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
        self.ui.spinBox_integration_time_alignment.editingFinished.connect(self.handle_integrationtime)
        self.ui.spinBox_averageing_alignment.editingFinished.connect(self.handle_averageing)
        self.ui.pushButton_dark.clicked.connect(
            self.handle_darkspectrum)
        self.ui.pushButton_reset.clicked.connect(self.handle_reset)
        self.ui.pushButton_lamp.clicked.connect(self.handle_lampspectrum)
        self.ui.pushButton_transmission.clicked.connect(self.handle_transmission)

    @pyqtSlot(int, int)
    def update_parameters(self, integrationtime, average_measurements):
        self.ui.label_integration_time_alignment_value.setText(f'{integrationtime} ms')
        self.ui.label_averageing_alignment_value.setText(f'{average_measurements}')

    def handle_darkspectrum(self):
        if not any(self.spectrometer.dark):
            self.spectrometer.measure_dark()
            self.ui.pushButton_dark.setChecked(True)
        else:
            self.spectrometer.clear_dark()
            self.ui.pushButton_dark.setChecked(False)

    def handle_lampspectrum(self):
        if not any(self.spectrometer.dark):
            QtWidgets.QMessageBox.information(self, 'No dark spectrum', 'Please first take dark spectrum')
            self.ui.pushButton_lamp.setChecked(False)
        if not any(self.spectrometer.lamp):
            self.spectrometer.measure_lamp()
            self.ui.pushButton_lamp.setChecked(True)
        elif self.spectrometer.transmission:
            self.spectrometer.transmission = False
            self.ui.pushButton_transmission.setChecked(False)
            self.transmission_set.emit(False)
            self.spectrometer.clear_lamp()
            self.ui.pushButton_lamp.setChecked(False)
        else:
            self.spectrometer.clear_lamp()
            self.ui.pushButton_lamp.setChecked(False)

    def handle_transmission(self):
        if not any(self.spectrometer.lamp):
            QtWidgets.QMessageBox.information(self, 'No lamp spectrum', 'Please first take lamp spectrum')
            self.ui.pushButton_transmission.setChecked(False)
        elif self.spectrometer.transmission:
            self.spectrometer.transmission = False
            self.ui.pushButton_transmission.setChecked(False)
        else:
            self.spectrometer.transmission = True
            self.ui.pushButton_transmission.setChecked(True)

    def handle_reset(self):
        self.spectrometer.transmission = False
        self.ui.pushButton_transmission.setChecked(False)
        self.transmission_set.emit(False)
        self.spectrometer.clear_lamp()
        self.ui.pushButton_lamp.setChecked(False)
        self.spectrometer.clear_dark()
        self.ui.pushButton_dark.setChecked(False)

    def handle_integrationtime(self):
        self.spectrometer.integrationtime = self.ui.spinBox_integration_time_alignment.value()
        self.ui.spinBox_integration_time_alignment.clear()

    def handle_averageing(self):
        self.spectrometer.average_measurements = self.ui.spinBox_averageing_alignment.value()
        self.ui.spinBox_averageing_alignment.clear()


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = SpectrometerWidget()
    window.show()
    sys.exit(app.exec_())

