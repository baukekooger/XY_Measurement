import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QTimer
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from instruments.Thorlabs.powermeters import QPowermeter
from matplotlib.ticker import FormatStrFormatter
from gui_action.plot_blitmanager import BlitManager
import time


class PowerMeterPlotWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.powermeter = QPowermeter()
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.log = np.zeros(1)
        self.lasttime = time.time()
        self.time = np.zeros(1)
        self.plotwindow = np.zeros(2000)
        self.blitmanager = None
        self.line = None

    def connect_signals_slots(self):
        self.powermeter.measurement_complete.connect(self.plot)

    def disconnect_signals_slots(self):
        self.powermeter.measurement_complete.disconnect()

    @pyqtSlot(list, list)
    def plot(self, times, power):
        self.log = np.append(self.log, power)
        self.plotwindow = np.append(self.plotwindow, power)
        self.plotwindow = self.plotwindow[1:]
        if not self.blitmanager:
            self.init_blitmanager()
        else:
            self.line.set_ydata(self.plotwindow)
        self.blitmanager.update()

    def init_blitmanager(self):
        self.blitmanager = None
        self.line, = self.ax.plot(np.linspace(50, 1), self.plotwindow, animated=True)
        self.ax.set_ylabel('power')
        self.ax.set_xlabel('measurement nr')
        self.ax.invert_xaxis()
        self.blitmanager = BlitManager(self.canvas, [self.line])
        time.sleep(0.1)

    def reset_log(self):
        pass

    def fit_plots(self):
        if self.blitmanager:
            self.blitmanager.redraw_canvas_powermeter()

    def clear(self):
        self.figure.clear()
        self.canvas.draw()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = PowerMeterPlotWidget()
    main.show()
    sys.exit(app.exec_())
