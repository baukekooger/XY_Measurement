from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, pyqtSlot
from gui_design.testplotxy import Ui_Form
from instruments.Thorlabs.xystage import QXYStage
import time

class TestPlotXY(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.pushButton_move.clicked.connect(self.emit_position)
        self.ui.pushButton_home.clicked.connect(self.home)
        self.ui.pushButton_plot.clicked.connect(self.plot)

        self.xystage = QXYStage()
        self.xystage.connect()
        self.xystagethread = QThread()
        self.xystage.moveToThread(self.xystagethread)
        self.xystagethread.start()

        self.ui.widget_plot.xystage = self.xystage
        self.ui.widget_plot.connect_signals_slots()

        self.heartbeat = QTimer()
        self.heartbeat.setInterval(int(200))
        self.heartbeat.timeout.connect(self.xystage.measure)
        self.heartbeat.start()

    def home(self):
        self.ui.widget_plot.xystage.home()

    def emit_position(self):
        x = int(self.ui.doubleSpinBox.value())
        y = int(self.ui.doubleSpinBox_2.value())
        self.ui.widget_plot.xystage.move(x, y)

    def plothandle(self):
        self.heartbeat.stop()
        QTimer.singleShot(1000, self.plot)

    def plot(self):
        self.ui.widget_plot.plot_layout(3, 4, 0, 0, 0, 0)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = TestPlotXY()
    window.show()
    sys.exit(app.exec_())