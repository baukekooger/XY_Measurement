import logging
import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from gui_action.plot_blitmanager import BlitManager
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
from instruments.CAEN.Qdigitizer import QDigitizer
import matplotlib.pyplot as plt
import time
import random


class DigitizerPlotWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.digitizer = QDigitizer()
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)
        self.blitmanager = None
        self.lines = []
        self.annotation = None
        self.active_channels = None
        self.available_channels = None
        self.samples = None
        self.post_trigger_size = None
        self.sample_rate = None

    def connect_signals_slots(self):
        """ Connect all the signals from the digitizer to the plotwindow """
        self.digitizer.measurement_complete.connect(self.plot)
        self.digitizer.redraw_plot.connect(self.redraw_axes)

    def disconnect_signals_slots(self):
        """ Disconnecting all the signals from the digitizer """
        self.digitizer.measurement_complete.disconnect()
        self.digitizer.redraw_plot.disconnect()

    @pyqtSlot()
    def redraw_axes(self):
        self.ax.clear()
        self.blitmanager = None

    @pyqtSlot(np.ndarray, np.ndarray, str)
    def plot(self, time, data, plotinfo):
        if not self.blitmanager:
            self.init_blitmanager(time, data, plotinfo)
        else:
            # for count, line in enumerate(self.lines, start=0):
            logging.debug(f'this is self.lines at updateing artists {self.lines}')
            self.lines.set_xdata(time)
            self.lines.set_ydata(data)
            self.annotation.set_text(plotinfo)
            self.blitmanager.update()

    def init_blitmanager(self, times, data, plotinfo):
        """
        Initializes the blitmanager by drawing the graph based on the data and saving a copy of the background """
        # clear blitmanager if existing
        logging.info('initializing blitmanager')
        if self.blitmanager:
            self.blitmanager = None

        self.lines = self.ax.plot(times, data, animated=True)
        logging.debug(f'this is self.lines at creation {self.lines}')
        # active_channels = list(self.digitizer.active_channels)
        self.annotation = self.ax.annotate(plotinfo, (0, 1), xycoords="axes fraction", xytext=(10, -10),
                                           textcoords="offset points", ha="left", va="top", animated=True)
        self.ax.set_ylabel('counts')
        self.ax.set_xlabel('time [ns]')
        self.ax.set_title('digitizer')
        self.blitmanager = BlitManager(self.canvas, [self.lines])
        time.sleep(0.1)
        # self.fit_plots()

    @pyqtSlot()
    def fit_plots(self):
        if self.blitmanager:
            self.blitmanager.redraw_canvas_digitizer()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = DigitizerPlotWidget()
    main.show()
    sys.exit(app.exec_())
