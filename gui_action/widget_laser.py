from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QTimer
from gui_design.laser import Ui_Form
from instruments.Ekspla.lasers import QLaser
import logging


class LaserWidget(QtWidgets.QWidget):
    """
    PyQt Widget for controlling the laser.
    Check the corresponding gui design file in pyqt designer for detailed info.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger_widget = logging.getLogger('gui.Laser')
        self.logger_widget.info('init laser widget ui')
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.laser = QLaser()

    def connect_signals_slots(self):
        """ Connect signals from the laser widget to laser function. """
        self.logger_widget.info('Connecting signals laser widget')
        self.laser.measurement_complete.connect(self.update_status)
        self.ui.spinBox_wavelength_alignment.editingFinished.connect(self.set_wavelength)
        self.ui.pushButton_max.clicked.connect(self.handle_max)
        self.ui.pushButton_off.clicked.connect(self.handle_off)
        self.ui.pushButton_adjust.clicked.connect(self.handle_adjust)
        self.ui.pushButton_output.clicked.connect(self.handle_output)

    def disconnect_signals_slots(self):
        """ Disconnect laser widget signals. """
        self.logger_widget.info('Disconnecting laser widget signals. ')
        self.laser.measurement_complete.disconnect(self.update_status)
        self.ui.spinBox_wavelength_alignment.editingFinished.disconnect(self.set_wavelength)
        self.ui.pushButton_max.clicked.disconnect(self.handle_max)
        self.ui.pushButton_off.clicked.disconnect(self.handle_off)
        self.ui.pushButton_adjust.clicked.disconnect(self.handle_adjust)
        self.ui.pushButton_output.clicked.disconnect(self.handle_output)

    @pyqtSlot(float, str, float, bool, bool)
    def update_status(self, wavelength, energylevel, power, stable, output):
        """ Update the current status of the laser in the widget e.g. wavelength, stability. """
        self.logger_widget.info(f'updating laser status, wl = {wavelength}, energylevel = {energylevel}, '
                                f'stable = {stable}, output = {output}')
        self.ui.label_wavelength_indicator.setText(f'{wavelength:.0f} nm')
        self.ui.checkBox_stable.setChecked(stable)
        if energylevel == 'Off':
            self.ui.pushButton_off.setChecked(True)
            self.ui.pushButton_adjust.setChecked(False)
            self.ui.pushButton_max.setChecked(False)
        elif energylevel == 'Adjust':
            self.ui.pushButton_off.setChecked(False)
            self.ui.pushButton_adjust.setChecked(True)
            self.ui.pushButton_max.setChecked(False)
        elif energylevel == 'Max':
            self.ui.pushButton_off.setChecked(False)
            self.ui.pushButton_adjust.setChecked(False)
            self.ui.pushButton_max.setChecked(True)
        if output:
            self.ui.pushButton_output.setChecked(True)
        else:
            self.ui.pushButton_output.setChecked(False)

    def set_wavelength(self):
        """ Set the laser wavelength. """
        self.logger_widget.info(f'Setting the laser wavelength from widget'
                                f' to {self.ui.spinBox_wavelength_alignment.value()}')
        self.laser.wavelength = self.ui.spinBox_wavelength_alignment.value()

    def handle_max(self):
        """ Set the energy level to maximum. """
        self.logger_widget.info('setting laser energylevel from widget to Max')
        self.laser.energylevel = 'Max'

    def handle_adjust(self):
        """ Set the energy level to adjust. """
        self.logger_widget.info('setting laser energylevel from widget to Adjust')
        self.laser.energylevel = 'Adjust'

    def handle_off(self):
        """ Set the energy level to off. """
        self.logger_widget.info('setting laser energylevel from widet to Off')
        self.laser.energylevel = 'Off'

    def handle_output(self):
        """ Turn laser output on or off. """
        if not self.laser.output:
            self.logger_widget.info('Turning on laser from widget')
            self.laser.output = True
        else:
            self.logger_widget.info('Turning off laser from widget')
            self.laser.output = False


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
    window = LaserWidget()
    window.show()
    sys.exit(app.exec_())

    # self.laser.connect()
    # self.connect_signals_slots()
    # self.hb = QTimer()
    # self.hb.setInterval(500)
    # self.hb.timeout.connect(self.measure)
    # self.hb.start()

    # def measure(self):
    #     if not self.laser.measuring:
    #         self.laser.measure()
