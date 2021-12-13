from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from gui_design.spectrometer import Ui_Form
from instruments.OceanOptics.spectrometer import QSpectrometer
from PyQt5.QtCore import pyqtSlot, QTimer
import logging
import numpy as np


class SpectrometerWidget(QtWidgets.QWidget):
    """
    PyQt Widget for controlling the spectrometer.
    Check the corresponding gui design file in pyqt designer for detailed info.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger_widget = logging.getLogger('gui.SpectrometerWidget')
        self.logger_widget.info('init spectrometer widget ui')
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.spectrometer = QSpectrometer()

    def connect_signals_slots(self):
        """ Connect signals between widget and spectrometer. """
        self.logger_widget.info('Connecting signals spectrometerwidget.')
        self.spectrometer.measurement_parameters.connect(self.update_parameters)
        self.spectrometer.measurement_lamp_complete.connect(self.lamp_measured)
        self.spectrometer.measurement_dark_complete.connect(self.dark_measured)
        self.spectrometer.transmission_set.connect(self.transmission_button_set)
        self.ui.spinBox_integration_time_alignment.editingFinished.connect(self.handle_integrationtime)
        self.ui.spinBox_averageing_alignment.editingFinished.connect(self.handle_averageing)
        self.ui.pushButton_dark.clicked.connect(
            self.handle_darkspectrum)
        self.ui.pushButton_reset.clicked.connect(self.handle_reset)
        self.ui.pushButton_lamp.clicked.connect(self.handle_lampspectrum)
        self.ui.pushButton_transmission.clicked.connect(self.handle_transmission)

    def disconnect_signals_slots(self):
        """ Disconnect signals between widget and spectrometer. """
        self.logger_widget.info('Disconnecting signals spectrometerwidget.')
        self.spectrometer.measurement_parameters.disconnect(self.update_parameters)
        self.spectrometer.measurement_lamp_complete.disconnect(self.lamp_measured)
        self.spectrometer.measurement_dark_complete.disconnect(self.dark_measured)
        self.spectrometer.transmission_set.disconnect(self.transmission_button_set)
        self.ui.spinBox_integration_time_alignment.editingFinished.disconnect(self.handle_integrationtime)
        self.ui.spinBox_averageing_alignment.editingFinished.disconnect(self.handle_averageing)
        self.ui.pushButton_dark.clicked.disconnect(
            self.handle_darkspectrum)
        self.ui.pushButton_reset.clicked.disconnect(self.handle_reset)
        self.ui.pushButton_lamp.clicked.disconnect(self.handle_lampspectrum)
        self.ui.pushButton_transmission.clicked.disconnect(self.handle_transmission)
        self.handle_reset()

    @pyqtSlot(int, int)
    def update_parameters(self, integrationtime, average_measurements):
        """ Update the current integration time and average measurements setting in the spectrometer widget. """
        self.logger_widget.info(f'setting spectrometer widget integration time to {integrationtime} and '
                                f'average measurements to {average_measurements}')
        self.ui.label_integration_time_alignment_value.setText(f'{integrationtime} ms')
        self.ui.label_averageing_alignment_value.setText(f'{average_measurements}')

    def handle_darkspectrum(self):
        """ Measure a dark spectrum if none present, otherwise remove the darkspectrum and any other saved spectra. """
        if not any(self.spectrometer.dark):
            self.logger_widget.info('Requesting dark spectrum from widget')
            QTimer.singleShot(0, self.spectrometer.measure_dark)
            self.ui.groupBox_alignment.setEnabled(False)
        else:
            self.logger_widget.info('Resetting dark spectrum and possibly lamp spectrum from widget')
            self.handle_reset()

    def handle_lampspectrum(self):
        """
        Set or reset the lamp spectrum. Checks if a lamp spectrum may be taken, can only be
        taken after a dark spectrum.
        """
        self.logger_widget.info('Requested a lamp spectrum')
        if not any(self.spectrometer.dark):
            QtWidgets.QMessageBox.information(self, 'No dark spectrum', 'Please first take dark spectrum')
            self.ui.pushButton_lamp.setChecked(False)
        elif not any(self.spectrometer.lamp):
            QTimer.singleShot(0, self.spectrometer.measure_lamp)
            self.ui.groupBox_alignment.setEnabled(False)
        elif self.spectrometer.transmission:
            self.spectrometer.transmission = False
            self.ui.pushButton_transmission.setChecked(False)
            self.spectrometer.clear_lamp()
            self.ui.pushButton_lamp.setChecked(False)
        else:
            self.spectrometer.clear_lamp()
            self.ui.pushButton_lamp.setChecked(False)

    def handle_transmission(self):
        """ Set the transmission attribute of the spectrometer when a lamp spectrum is present. """
        self.logger_widget.info('Requested setting the spectrometer transmission attribute. ')
        if not any(self.spectrometer.lamp):
            QtWidgets.QMessageBox.information(self, 'No lamp spectrum', 'Please first take lamp spectrum')
            self.ui.pushButton_transmission.setChecked(False)
        elif self.spectrometer.transmission:
            self.spectrometer.transmission = False
            self.ui.pushButton_transmission.setChecked(False)
        else:
            self.spectrometer.transmission = True
            self.ui.pushButton_transmission.setChecked(True)

    @pyqtSlot()
    def transmission_button_set(self):
        """
        Set the transmission button to checked.

        This is done to set the transmission button to during an automated experiment. Otherwise when returning
        from the experiment, there is a transmission spectrum but the button is unchecked.
        """
        self.ui.pushButton_transmission.setChecked(True)

    @pyqtSlot(np.ndarray)
    def dark_measured(self, *intensities):
        """ Set the dark spectrum button when a dark spectrum has been measured. """
        self.logger_widget.info('Dark spectrum measured, setting button.')
        self.ui.pushButton_dark.setChecked(True)
        self.ui.groupBox_alignment.setEnabled(True)

    @pyqtSlot(np.ndarray)
    def lamp_measured(self, *intensities):
        """ Set the lamp spectrum button when a lamp spectrum has been measured. """
        self.logger_widget.info('Lamp spectrum measured, setting button.')
        self.ui.pushButton_lamp.setChecked(True)
        self.ui.groupBox_alignment.setEnabled(True)

    def handle_reset(self):
        """ Reset the buttons and clear any stored spectra in the spectrometer. """
        self.logger_widget.info('Resetting all stored spectra from widget')
        self.spectrometer.transmission = False
        self.ui.pushButton_transmission.setChecked(False)
        self.spectrometer.clear_lamp()
        self.ui.pushButton_lamp.setChecked(False)
        self.spectrometer.clear_dark()
        self.ui.pushButton_dark.setChecked(False)

    def handle_integrationtime(self):
        """ Set the integration time attribute in the spectrometer. """
        value = self.ui.spinBox_integration_time_alignment.value()
        self.logger_widget.info(f'Setting spectrometer integration time from widget to {value}')
        self.spectrometer.integrationtime = value

    def handle_averageing(self):
        """ Set the number of measurements to average over. """
        value = self.ui.spinBox_averageing_alignment.value()
        self.logger_widget.info(f'Setting spectrometer averageing from widget to {value}')
        self.spectrometer.average_measurements = self.ui.spinBox_averageing_alignment.value()


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers
    pathlogging = Path(__file__).parent.parent / 'logging/loggingconfig_testing.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    # setup pyqt app
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = SpectrometerWidget()
    window.show()
    sys.exit(app.exec_())

