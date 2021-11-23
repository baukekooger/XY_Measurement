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
        self.darkspectrum = []
        self.lampspectrum = []
        self.transmission = False

    def connect_signals_slots(self):
        self.spectrometer.measurement_complete.connect(self.plot)
        self.spectrometer.clear_darkspectrum_plot.connect(self.clear_dark)
        self.spectrometer.clear_lampspectrum_plot.connect(self.clear_lamp)

    def disconnect_signals_slots(self):
        self.spectrometer.measurement_complete.disconnect(self.plot)
        self.spectrometer.clear_darkspectrum_plot.disconnect(self.clear_dark)
        self.spectrometer.clear_lampspectrum_plot.disconnect(self.clear_lamp)

    @pyqtSlot(np.ndarray, str)
    def plot(self, intensities, plotinfo):
        """
        Plot spectrum and set graph annotation. Plot raw spectra, spectra with dark spectrum removed or
        transmission spectrum based on spectrometer settings.

        Plots using a blitmanager for increased performance.
        """
        if not self.blitmanager:
            self.init_blitmanager(intensities, plotinfo)

        self.transmission = True if 'Transmission' in plotinfo and any(self.darkspectrum) \
                                    and any(self.lampspectrum) else False

        if self.transmission:
            self.logger_plot.info('plotting transmission spectrum')
            divideby = self.lampspectrum - self.darkspectrum
            divideby[divideby <= 0] = 1
            transmission = (intensities - self.darkspectrum)/divideby
            np.clip(transmission, 0, 1, transmission)
            self.line.set_ydata(transmission)
            self.annotation.set_text(plotinfo)
        elif any(self.darkspectrum):
            self.logger_plot.info('plotting spectrum minus dark spectrum')
            minusdark = intensities - self.darkspectrum
            self.line.set_ydata(minusdark)
            self.annotation.set_text(plotinfo)
        else:
            self.line.set_ydata(intensities)
            self.annotation.set_text(plotinfo)
        self.blitmanager.update()
        if 'Dark Spectrum' in plotinfo and 'minus' not in plotinfo:
            self.logger_plot.info('setting dark spectrum plot')
            self.darkspectrum = intensities
        elif 'Lamp Spectrum' in plotinfo:
            self.logger_plot.info('setting lamp spectrum plot')
            self.lampspectrum = intensities

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

    @pyqtSlot()
    def clear_dark(self):
        self.logger_plot.info('clearing dark spectrum plot')
        self.darkspectrum = []

    @pyqtSlot()
    def clear_lamp(self):
        self.logger_plot.info('clearing lamp spectrum plot')
        self.lampspectrum = []


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