import logging
from PyQt5 import QtWidgets
from gui_design.shuttercontrol import Ui_Form
from instruments.Thorlabs.shuttercontrollers import QShutterControl
from PyQt5.QtCore import pyqtSlot, QTimer


class ShutterControlWidget(QtWidgets.QWidget):
    """
    PyQt Widget for controlling the shutter.
    Check the corresponding gui design file in pyqt designer for detailed info.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger_widget = logging.getLogger('gui.ShutterControlWidget')
        self.logger_widget.info('init shuttercontrol widget ui')
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.shuttercontrol = QShutterControl()
        # self.shuttercontrol.connect()
        self.shutterstatus = False

    def connect_signals_slots(self):
        """ Connect signals shuttercontrol to widget and vice versa. """
        self.logger_widget.info('Connecting signals shuttercontrolwidget. ')
        self.shuttercontrol.shutter_status.connect(self.handle_shutterstatus)
        self.ui.pushButton_shutter.clicked.connect(self.handle_shutter_open_close)

    def disconnect_signals_slots(self):
        """ Disconnect all signals. """
        self.logger_widget.info('Disconnecting all signals shuttercontrol widget')
        self.shuttercontrol.shutter_status.disconnect(self.handle_shutterstatus)
        self.ui.pushButton_shutter.clicked.disconnect(self.handle_shutter_open_close)

    @pyqtSlot(bool)
    def handle_shutterstatus(self, status):
        """ Set the status checkbox of the shuttercontrol widget depending on the shutter status. """
        if status:
            self.logger_widget.info('Setting shuttercontrolwidget status to true')
            self.shutterstatus = status
            self.ui.checkBox.setChecked(True)
        else:
            self.logger_widget.info('Setting shuttercontrolwidget status to false')
            self.shutterstatus = False
            self.ui.checkBox.setChecked(False)

    @pyqtSlot()
    def handle_shutter_open_close(self):
        """ Open or close the shutter. """
        self.shuttercontrol.measure()
        if self.shutterstatus:
            self.logger_widget.info('Disabling the shutter from widget')
            QTimer.singleShot(0, self.shuttercontrol.disable)
        else:
            self.logger_widget.info('Enabling the shutter from widget')
            QTimer.singleShot(0, self.shuttercontrol.enable)


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
    window = ShutterControlWidget()
    window.show()
    sys.exit(app.exec_())

    # self.connect_signals_slots()
    # self.hb = QTimer()
    # self.hb.setInterval(100)
    # self.hb.timeout.connect(self.shuttercontrol.measure)
    # self.hb.start()