import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import random
import numpy as np
from instruments.OceanOptics.spectrometer import QSpectrometer


class SpectrometerPlotWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.figure = None
        self.canvas = None
        self.spectrometer = QSpectrometer()

    def connect_signals_slots(self):
        self.figure = plt.figure()
        layout = QtWidgets.QVBoxLayout()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        # self.toolbar = NavigationToolbar(self.canvas, self)
        # layout.addWidget(self.toolbar)
        self.setLayout(layout)
        self.spectrometer.measurement_complete.connect(self.plot)

    @pyqtSlot(np.ndarray, list)
    def plot(self, intensities, times):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(self.spectrometer.wavelengths, intensities, '*-')
        ax.set_title(f'measurement completed in {times[-1]-times[0]:.2f} seconds')
        self.figure.tight_layout()
        self.canvas.draw()

    def plotinitial(self):
        # plot random values if not called with arguments
        wavelengths = list(range(10))
        intensities = [random.random() for i in range(10)]
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(wavelengths, intensities, '*-')
        self.figure.tight_layout()
        self.canvas.draw()

    def clear(self):
        self.figure.clear()
        self.canvas.draw()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = SpectrometerPlotWidget()
    main.show()
    sys.exit(app.exec_())