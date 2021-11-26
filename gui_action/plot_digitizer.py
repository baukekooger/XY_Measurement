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


class DigitizerPlotWidget(QtWidgets.QWidget):
    """
    Plot widget for the digitizer data.

    Uses a blitmanager for faster rendering.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('plot.digitizer')
        self.logger.info('init plotwindow digitizter')
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
        """ Connect all the signals from the digitizer to the plotwindow. """
        self.logger.info('connecting signals digitizer plotwindow')
        self.digitizer.measurement_complete.connect(self.plot)
        self.digitizer.plotaxis_labels.connect(self.set_axislabels)

    def disconnect_signals_slots(self):
        """ Disconnect all the signals from the digitizer """
        self.logger.info('disconnecting signals digitizer plotwindow')
        self.digitizer.measurement_complete.disconnect()
        self.digitizer.plotaxis_labels.disconnect()

    @pyqtSlot(np.ndarray, np.ndarray, str)
    def plot(self, times, data, plotinfo):
        """
        Plot the digitizer data.
        If there is not yet a blitmanager, intialize one.
        """
        if not self.blitmanager:
            self.init_blitmanager(times, data, plotinfo)
        else:
            # for count, line in enumerate(self.lines, start=0):
            self.logger.debug('updating digitizer plot')
            self.lines.set_xdata(times)
            self.lines.set_ydata(data)
            self.annotation.set_text(plotinfo)
            self.blitmanager.update()

    def init_blitmanager(self, times, data, plotinfo):
        """
        Initialize the blitmanager for quicker rendering of the plotdata.
        """
        self.logger.info('initializing blitmanager digitizer plotwindow')
        if self.blitmanager:
            self.blitmanager = None

        self.lines, = self.ax.plot(times, data, animated=True)
        self.annotation = self.ax.annotate(plotinfo, (0, 1), xycoords="axes fraction", xytext=(10, -10),
                                           textcoords="offset points", ha="left", va="top", animated=True)
        self.ax.set_ylabel('counts')
        self.ax.set_xlabel('time [s]')
        self.ax.set_title('digitizer')
        self.blitmanager = BlitManager(self.canvas, [self.lines, self.annotation])
        time.sleep(0.1)
        # self.fit_plots()

    @pyqtSlot(dict)
    def set_axislabels(self, axislabels):
        """ Set the title and yaxis lable when measurement mode changes. """
        title = axislabels['title']
        ylabel = axislabels['ylabel']
        self.logger.info(f'changing digitizer title to {title}, ylabel to {ylabel}')
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)

    @pyqtSlot()
    def fit_plots(self):
        """
        Fit plots to screen by redrawing the canvas.

        Function called from main.py as the button for it is in the main ui.
        """
        if self.blitmanager:
            self.logger.info('fitting digitizer plot to window')
            self.blitmanager.redraw_canvas_digitizer()


if __name__ == '__main__':
    # setup logging
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers
    pathlogging = Path(__file__).parent.parent / 'logging/loggingconfig_testing.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    # pyqt app
    app = QtWidgets.QApplication(sys.argv)
    main = DigitizerPlotWidget()
    main.show()
    sys.exit(app.exec_())

