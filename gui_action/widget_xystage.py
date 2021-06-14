from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from gui_design.xystage import Ui_Form
from instruments.Thorlabs.xystage_pyqt import QXYStage


class XYStageWidget(QtWidgets.QWidget):

    move = pyqtSignal(float, float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.xystage = QXYStage()

    def connect_signals_slots(self):
        self.ui.doubleSpinBox_x.editingFinished.connect(self._handle_move_x)
        self.ui.doubleSpinBox_y.editingFinished.connect(self._handle_move_y)
        self.ui.pushButton_home_motors.clicked.connect(self.xystage.home)
        self.move.connect(self.xystage.move)

    def _handle_move_x(self):
        self.ui.doubleSpinBox_y.blockSignals(True)
        self.ui.doubleSpinBox_y.setValue(self.xystage.y)
        self.ui.doubleSpinBox_y.blockSignals(False)
        self.move.emit(self.ui.doubleSpinBox_x.value(), self.ui.doubleSpinBox_y.value())

    def _handle_move_y(self):
        self.ui.doubleSpinBox_x.blockSignals(True)
        self.ui.doubleSpinBox_x.setValue(self.xystage.x)
        self.ui.doubleSpinBox_x.blockSignals(False)
        self.move.emit(self.ui.doubleSpinBox_x.value(), self.ui.doubleSpinBox_y.value())


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = XYStageWidget()
    window.show()
    sys.exit(app.exec_())

