from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QThread, pyqtSlot, pyqtSignal, QObject
from ui_blitting import Ui_MainWindow
import numpy as np
import time
import datetime


class Worker(QObject):

    measurement_complete = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.amplitude = 1          #
        self.phase = 0              # radians
        self.datapoints = np.linspace(0, 2*np.pi, 4000)

    @pyqtSlot()
    def measure(self):
        ydata = self.amplitude * np.sin(self.datapoints + self.phase)
        self.phase += np.pi / 100
        self.measurement_complete.emit(ydata)

    @pyqtSlot(float)
    def amplitudechange(self, amplitude):
        self.amplitude = amplitude


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.worker = Worker()
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        self.repetition_rate = 1
        self.measurement_timer = QTimer()

        self.connect_signals_slots()

    def connect_signals_slots(self):
        self.ui.pushButton_start.clicked.connect(self.start_timer)
        self.ui.pushButton_stop.clicked.connect(self.stop_timer)
        self.ui.spinBox_repetition.valueChanged.connect(self.changed_repetitionrate)
        self.ui.doubleSpinBox_amplitude.valueChanged.connect(self.worker.amplitudechange)
        self.measurement_timer.timeout.connect(self.worker.measure)
        self.worker.measurement_complete.connect(self.ui.widget_blit.plot_blit)

    @pyqtSlot()
    def start_timer(self):
        interval = int(1000/self.repetition_rate)
        self.measurement_timer.start(interval)

    @pyqtSlot()
    def stop_timer(self):
        self.measurement_timer.stop()

    @pyqtSlot(int)
    def changed_repetitionrate(self, rate):
        self.repetition_rate = rate
        interval = int(1000/rate)
        if self.measurement_timer.isActive():
            self.measurement_timer.setInterval(interval)

    @pyqtSlot(float)
    def changed_amplitude(self, amplitude):
        self.worker.amplitude = amplitude


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
