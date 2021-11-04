import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import matplotlib.pyplot as plt
from blitmanager import BlitManager
import time
import random


class BlittingWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.bm = None
        self.ln = None

    @pyqtSlot(np.ndarray)
    def plot(self, data):
        self.ax.clear()
        self.ax.plot(data, '*')
        self.figure.tight_layout()
        self.canvas.draw()

    @pyqtSlot(np.ndarray)
    def plot_blit(self, data):
        if not self.bm:
            self.init_blitmanager(data)
        else:
            self.ln.set_ydata(data)
            self.bm.update()
        pass

    def init_blitmanager(self, data):
        self.ln, = self.ax.plot(data, animated=True)
        self.bm = BlitManager(self.canvas, [self.ln])
        time.sleep(0.1)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = BlittingWidget()
    main.show()
    sys.exit(app.exec_())