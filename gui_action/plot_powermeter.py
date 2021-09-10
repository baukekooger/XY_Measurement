import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QTimer
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from instruments.Thorlabs.powermeters import QPowermeter
from matplotlib.ticker import FormatStrFormatter
import time


class PowerMeterPlotWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.powermeter = QPowermeter()
        # self.powermeter.connect()
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        # self.toolbar = NavigationToolbar(self.canvas, self)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.log = np.zeros(1)
        self.lasttime = time.time()
        self.time = np.zeros(1)

        # self.connect_signals_slots()
        # self.hb = QTimer()
        # self.hb.setInterval(100)
        # self.hb.timeout.connect(self.powermeter.measure)
        # self.hb.start()

    def connect_signals_slots(self):
        self.powermeter.measurement_complete.connect(self.plot)

    def disconnect_signals_slots(self):
        self.powermeter.measurement_complete.disconnect()

    @pyqtSlot(float)
    def plot(self, power):
        self.log = np.append(self.log, power)
        if len(self.log) > 50:
            self.log = self.log[1:]
        newtime = time.time()
        self.time = self.time - (newtime - self.lasttime)
        self.lasttime = newtime
        self.time = np.append(self.time, 0)
        if len(self.time) > 50:
            self.time = self.time[1:]

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if power > 5:
            # plots overload warning and clears the log
            ax.text(0.5, 0.5, 'Sensor out of range (OL)!', dict(ha='center', va='center', fontsize=15))
            self.log = np.zeros(1)
            self.lasttime = time.time()
            self.time = np.zeros(1)
        elif power > 1:
            ax.plot(self.time, self.log, '-')
            ax.set_ylabel('power [W]')
            ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        elif power > 0.001:
            ax.plot(self.time, self.log*1e3, '-')
            ax.set_ylabel(f'power [mW]')
            ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        else:
            ax.plot(self.time, self.log * 1e6, '-')
            ax.set_ylabel(f'power [\u03BCW]')
            ax.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        ax.set_xlabel('time [s]')
        self.figure.tight_layout()
        self.canvas.draw()

    def fit_plots(self):
        pass

    def clear(self):
        self.figure.clear()
        self.canvas.draw()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = PowerMeterPlotWidget()
    main.show()
    sys.exit(app.exec_())
