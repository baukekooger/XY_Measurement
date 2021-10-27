import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from gui_action.plot_blitmanager import BlitManager
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import time
import logging
import random
import numpy as np
from instruments.OceanOptics.spectrometer import QSpectrometer


class SpectrometerPlotWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('plot.Spectrometer')
        self.logger.info('init spectrometer plotwindow')
        self.spectrometer = QSpectrometer()
        self.figure, self.ax = plt.subplots()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.bm = None
        self.ln = None

    def connect_signals_slots(self):
        self.spectrometer.measurement_complete.connect(self.plot)

    def disconnect_signals_slots(self):
        self.spectrometer.measurement_complete.disconnect()

    @pyqtSlot(np.ndarray, list)
    def plot(self, intensities, times):
        """"plots graph using blitmanager for increased performance"""
        if not self.bm:
            self.init_blitmanager(intensities)
        if self.spectrometer.transmission:
            transmission = (intensities - self.spectrometer.dark)/(self.spectrometer.lamp - self.spectrometer.dark)
            np.clip(transmission, 0, 1, transmission)
            self.ln.set_ydata(transmission)
        elif any(self.spectrometer.dark):
            minusdark = intensities - self.spectrometer.dark
            self.ln.set_ydata(minusdark)
        else:
            self.ln.set_ydata(intensities)
        self.bm.update()

    def init_blitmanager(self, intensities):
        self.bm = None
        self.ln, = self.ax.plot(self.spectrometer.wavelengths, intensities, animated=True)
        self.ax.set_ylabel('counts')
        self.ax.set_xlabel('wavelength [nm]')
        self.bm = BlitManager(self.canvas, [self.ln])
        time.sleep(0.1)

    @pyqtSlot()
    def fit_plots(self):
        """
        Fit plots to screen by redrawing the canvas

        Function called from main.py as the button for it is in the main ui.
        """
        if self.bm:
            self.bm.redraw_canvas_spectrometer()


if __name__ == '__main__':
    # setup logging
    from pathlib import Path
    import yaml
    import logging.config
    pathlogging = Path(__file__).parent.parent / 'loggingconfig.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    app = QtWidgets.QApplication(sys.argv)
    main = SpectrometerPlotWidget()
    main.show()
    sys.exit(app.exec_())