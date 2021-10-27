from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from gui_design.xystage import Ui_Form
from instruments.Thorlabs.xystage import QXYStage
import logging


class XYStageWidget(QtWidgets.QWidget):

    move = pyqtSignal(float, float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('gui.XYStageWidget')
        self.logger.info('init xystage widget')
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.xystage = QXYStage()
        self.ui.doubleSpinBox_x.clear()
        self.ui.doubleSpinBox_y.clear()

    def connect_signals_slots(self):
        self.xystage.measurement_complete.connect(self.set_position)
        self.xystage.homing_status.connect(self.set_homing)
        self.ui.doubleSpinBox_x.editingFinished.connect(self._handle_move_x)
        self.ui.doubleSpinBox_y.editingFinished.connect(self._handle_move_y)
        self.ui.pushButton_home_motors.clicked.connect(self._handle_home)
        self.ui.doubleSpinBox_x.setMaximum(self.xystage.xmax)
        self.ui.doubleSpinBox_y.setMaximum(self.xystage.ymax)

    def disconnect_signals_slots(self):
        self.xystage.homing_status.disconnect()
        self.ui.doubleSpinBox_x.editingFinished.disconnect()
        self.ui.doubleSpinBox_y.editingFinished.disconnect()
        self.ui.pushButton_home_motors.clicked.disconnect()

    def _handle_move_x(self):
        if not self.xystage.xhomed:
            QtWidgets.QMessageBox.information(self, 'homing warning', 'x stage not homed, wait for stages to home')
            self._handle_home()
        else:
            self.xystage.x = self.ui.doubleSpinBox_x.value()

    def _handle_move_y(self):
        if not self.xystage.yhomed:
            QtWidgets.QMessageBox.information(self, 'homing warning', 'y stage not homed, wait for stages to home')
            self._handle_home()
        else:
            self.xystage.y = self.ui.doubleSpinBox_y.value()

    def _handle_home(self):
        self.xystage.home()

    @pyqtSlot(float, float)
    def set_position(self, x, y):
        self.ui.label_x_value.setText(f'{x:.2f} mm')
        self.ui.label_y_value.setText(f'{y:.2f} mm')

    @pyqtSlot(bool, bool)
    def set_homing(self, xhome, yhome):
        self.ui.checkBox_homed_x.setChecked(xhome)
        self.ui.checkBox_homed_y.setChecked(yhome)


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    pathlogging = Path(__file__).parent.parent / 'loggingconfig.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    # setup pyqt app
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = XYStageWidget()
    window.show()
    sys.exit(app.exec_())

