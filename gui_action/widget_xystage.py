from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from gui_design.xystage import Ui_Form
from instruments.Thorlabs.xystage import QXYStage
import logging


class XYStageWidget(QtWidgets.QWidget):
    """
    PyQt Widget for controlling the xy stages.
    Check the corresponding gui design file in pyqt designer for detailed info.
    """
    move = pyqtSignal(float, float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger_widget = logging.getLogger('gui.XYStageWidget')
        self.logger_widget.info('init xystage widget')
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.xystage = QXYStage()
        self.ui.doubleSpinBox_x.clear()
        self.ui.doubleSpinBox_y.clear()

    def connect_signals_slots(self):
        """ Connect signals between xy stage and widget. """
        self.logger_widget.info('Connecting signals xystage widget')
        self.xystage.measurement_complete.connect(self.set_position)
        self.xystage.homing_status.connect(self.set_homing)
        self.ui.doubleSpinBox_x.editingFinished.connect(self._handle_move_x)
        self.ui.doubleSpinBox_y.editingFinished.connect(self._handle_move_y)
        self.ui.pushButton_home_motors.clicked.connect(self._handle_home)
        self.ui.doubleSpinBox_x.setMaximum(self.xystage.xmax)
        self.ui.doubleSpinBox_y.setMaximum(self.xystage.ymax)

    def disconnect_signals_slots(self):
        """ Disconnect signals between xy stage and widget. """
        self.logger_widget.info('Disconnecting signals xystage widget')
        self.xystage.measurement_complete.disconnect(self.set_position)
        self.xystage.homing_status.disconnect(self.set_homing)
        self.ui.doubleSpinBox_x.editingFinished.disconnect(self._handle_move_x)
        self.ui.doubleSpinBox_y.editingFinished.disconnect(self._handle_move_y)
        self.ui.pushButton_home_motors.clicked.disconnect(self._handle_home)

    def _handle_move_x(self):
        """ Move the x stage to the value in the box. """
        if not self.xystage.xhomed:
            self.logger_widget.info('requested move in x but need to home first')
            QtWidgets.QMessageBox.information(self, 'homing warning', 'x stage not homed, wait for stages to home')
            self._handle_home()
        else:
            value = self.ui.doubleSpinBox_x.value()
            self.logger_widget.info(f'Moving xstage to {value}')
            self.xystage.x = value

    def _handle_move_y(self):
        """ Move the y stage to the value in the box. """
        if not self.xystage.yhomed:
            self.logger_widget.info('requested move in y but need to home first')
            QtWidgets.QMessageBox.information(self, 'homing warning', 'y stage not homed, wait for stages to home')
            self._handle_home()
        else:
            value = self.ui.doubleSpinBox_y.value()
            self.logger_widget.info(f'Moving ystage to {value}')
            self.xystage.y = value

    def _handle_home(self):
        """ Home the xystages"""
        self.logger_widget.info('Requested homing from widget')
        self.xystage.home()

    @pyqtSlot(float, float)
    def set_position(self, x, y):
        """ Set the current position in the widget. """
        self.logger_widget.debug(f'setting xystage widget x and y to {x}, {y}')
        self.ui.label_x_value.setText(f'{x:.2f} mm')
        self.ui.label_y_value.setText(f'{y:.2f} mm')

    @pyqtSlot(bool, bool)
    def set_homing(self, xhome, yhome):
        """ Set the homing status in the xystage widget. """
        self.logger_widget.debug(f'setting xystage widget homing status to {xhome}, {yhome}')
        self.ui.checkBox_homed_x.setChecked(xhome)
        self.ui.checkBox_homed_y.setChecked(yhome)


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
    window = XYStageWidget()
    window.show()
    sys.exit(app.exec_())

