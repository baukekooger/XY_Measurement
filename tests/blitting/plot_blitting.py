import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
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
        self.plot()

    def connect_signals_slots(self):
        self.digitizer.measurement_complete(self.plot_single)
        self.digitizer.measurement_complete_multiple(self.plot_multiple)

    @pyqtSlot(np.ndarray)
    def plot_single(self, data):
        self.ax.clear()
        # subtract mean and invert
        data = (data - np.mean(data[0:50], axis=1))
        # data needs to be transposed to be plotted
        self.ax.plot(data.T)
        self.ax.set_xlabel('sample')
        self.ax.set_ylabel('counts')
        self.set_title('single pulse')
        self.figure.tight_layout()
        self.canvas.draw()

    @pyqtSlot(np.ndarray)
    def plot_multiple(self, data):
        pass

    def clear(self):
        self.figure.clear()
        self.canvas.draw()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = DigitizerPlotWidget()
    main.show()
    sys.exit(app.exec_())