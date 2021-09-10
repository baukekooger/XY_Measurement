import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from gui_action.plot_blitmanager import BlitManager
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from instruments.CAEN.Qdigitizer import QDigitizer
import matplotlib.pyplot as plt
import random


class DigitizerPlotWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.digitizer = QDigitizer()
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.blitmanager = None
        self.lines = []
        self.active_channels = None
        self.available_channels = None
        self.samples = None
        self.post_trigger_size = None

    def connect_signals_slots(self):
        self.digitizer.measurement_complete.connect(self.plot_single)
        self.digitizer.measurement_complete_multiple.connect(self.plot_multiple)
        self.digitizer.digitizer_parameters.connect(self.update_settings)

    @pyqtSlot(list, list, int, int)
    def update_settings(self, available_channels, active_channels, samples, post_trigger_size):
        self.available_channels = available_channels
        self.active_channels = active_channels
        self.samples = samples
        self.post_trigger_size = post_trigger_size
        self.ax.clear()
        self.blitmanager = None

    @pyqtSlot(np.ndarray)
    def plot_single(self, data):
        if not self.blitmanager:
            self.init_blitmanager(data)
        else:
            # subtract mean and invert
            data = -(data.T - np.mean(data[0:50], axis=1)).T
            for count, line in enumerate(self.lines, start=0):
                line.set_ydata(data[count, :])
            self.blitmanager.update()

    @pyqtSlot(np.ndarray)
    def init_blitmanager(self, data):
        # clear blitmanager if existing
        if self.blitmanager:
            self.blitmanager = None

        data = -(data.T - np.mean(data[0:50], axis=1)).T

        self.lines = self.ax.plot(data.T, animated=True)
        active_channels = list(self.digitizer.active_channels)
        self.ax.legend(self.lines, active_channels)
        self.ax.set_ylabel('counts')
        self.ax.set_xlabel('sample nr')
        self.ax.set_title('single pulse')
        self.blitmanager = BlitManager(self.canvas, self.lines)
        self.fit_plots()

    @pyqtSlot(np.ndarray)
    def plot_multiple(self, data):
        pass

    @pyqtSlot()
    def fit_plots(self):
        if self.blitmanager:
            self.blitmanager.redraw_canvas_digitizer()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = DigitizerPlotWidget()
    main.show()
    sys.exit(app.exec_())