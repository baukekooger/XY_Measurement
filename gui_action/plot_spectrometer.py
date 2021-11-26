import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from gui_action.plot_blitmanager import BlitManager
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import time
import logging
import numpy as np
from instruments.OceanOptics.spectrometer import QSpectrometer


class SpectrometerPlotWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger_plot = logging.getLogger('plot.Spectrometer')
        self.logger_plot.info('init spectrometer plotwindow')
        self.spectrometer = QSpectrometer()
        self.figure, self.ax = plt.subplots()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.blitmanager = None
        self.line = None
        self.annotation = None

    def connect_signals_slots(self):
        self.spectrometer.measurement_complete.connect(self.plot)
        self.spectrometer.measurement_dark_complete.connect(self.plot_dark)
        self.spectrometer.measurement_lamp_complete.connect(self.plot_lamp)

    def disconnect_signals_slots(self):
        self.spectrometer.measurement_complete.disconnect(self.plot)
        self.spectrometer.measurement_dark_complete.disconnect(self.plot_dark)
        self.spectrometer.measurement_lamp_complete.disconnect(self.plot_lamp)

    def define_plotinfo(self) -> str:
        """
        Define the information to plot in the screen. If there is custom plotinfo, use that. Otherwise determine
        plotinfo from which spectra are available.
        :returns: plotinfo string.
        """
        if self.spectrometer.plotinfo:
            return self.spectrometer.plotinfo
        if self.spectrometer.transmission:
            plotinfo = 'Transmission Spectrum'
        elif any(self.spectrometer.dark):
            plotinfo = 'Spectrum minus Dark Spectrum'
        else:
            plotinfo = 'Raw Spectrum'
        return plotinfo

    @pyqtSlot(np.ndarray)
    def plot_dark(self, intensities):
        """ Plot the dark spectrum. """
        self.logger_plot.info('plotting dark spectrum')
        plotinfo = 'Dark Spectrum'
        if not self.blitmanager:
            self.init_blitmanager(intensities, plotinfo)
        self.line.set_ydata(intensities)
        self.annotation.set_text(plotinfo)
        self.blitmanager.update()

    @pyqtSlot(np.ndarray)
    def plot_lamp(self, intensities):
        """ Plot the lamp spectrum. """
        self.logger_plot.info('plotting lamp spectrum')
        plotinfo = 'Lamp Spectrum'
        if not self.blitmanager:
            self.init_blitmanager(intensities, plotinfo)
        self.line.set_ydata(intensities)
        self.annotation.set_text(plotinfo)
        self.blitmanager.update()

    @pyqtSlot(np.ndarray)
    def plot(self, intensities):
        """
        Plot spectrum and set graph annotation. Plot raw spectra, spectra with dark spectrum removed or
        transmission spectrum based on spectrometer settings.

        Plots using a blitmanager for increased performance.
        """
        plotinfo = self.define_plotinfo()
        if not self.blitmanager:
            self.init_blitmanager(intensities, self.spectrometer.plotinfo)
        if self.spectrometer.transmission:
            self.logger_plot.info('plotting transmission spectrum')
            divideby = self.spectrometer.lamp - self.spectrometer.dark
            divideby[divideby <= 0] = 1
            transmission = (intensities - self.spectrometer.dark)/divideby
            np.clip(transmission, 0, 1, transmission)
            self.line.set_ydata(transmission)
            self.annotation.set_text(plotinfo)
        elif any(self.spectrometer.dark):
            self.logger_plot.info('plotting spectrum minus dark spectrum')
            minusdark = intensities - self.spectrometer.dark
            self.line.set_ydata(minusdark)
            self.annotation.set_text(plotinfo)
        else:
            self.line.set_ydata(intensities)
            self.annotation.set_text(plotinfo)
        self.blitmanager.update()

    def init_blitmanager(self, intensities, plotinfo):
        self.logger_plot.info(f'Initializing blitmanager spectrometerplot with data '
                              f'= {intensities} and plotinfo = {plotinfo}')
        self.blitmanager = None
        self.line, = self.ax.plot(self.spectrometer.wavelengths, intensities, animated=True)
        self.annotation = self.ax.annotate(plotinfo, (0, 1), xycoords="axes fraction", xytext=(10, -10),
                                           textcoords="offset points", ha="left", va="top", animated=True)
        self.ax.set_ylabel('counts')
        self.ax.set_xlabel('wavelength [nm]')
        self.ax.set_title(f"Spectrometer {self.spectrometer.spec.model + ' ' + self.spectrometer.spec.serial_number}")
        self.blitmanager = BlitManager(self.canvas, [self.line, self.annotation])
        time.sleep(0.1)

    @pyqtSlot()
    def fit_plots(self):
        """
        Fit plots to screen by redrawing the canvas

        Function called from main.py as the button for it is in the main ui.
        """
        if self.blitmanager:
            self.blitmanager.redraw_canvas_spectrometer()


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
    app = QtWidgets.QApplication(sys.argv)
    main = SpectrometerPlotWidget()
    main.show()
    sys.exit(app.exec_())