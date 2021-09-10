import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Rectangle, Circle
import matplotlib.pyplot as plt
import logging
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from instruments.Thorlabs.xystage import QXYStage
import shapely.geometry as gmt
import descartes
from blitmanager import BlitManager
import numpy as np
from pathlib import Path
from yaml import safe_load as yaml_safe_load
import random
import time

logging.basicConfig(level=logging.INFO)


class BlittingWidgetXY(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.figure, self.ax = plt.subplots()
        # self.xystage = QXYStage()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)
        self.experiment = None
        self.substrate = None
        self.bm = None
        self.patches = []

    def connect_signals_slots(self):
        self.xystage.measurement_complete.connect(self.plot_position)

    def disconnect_signals_slots(self):
        try:
            self.xystage.measurement_complete.disconnect()
        except TypeError:
            pass

    # @pyqtSlot(float, float)
    # def plot_position(self, x, y):
    #     self.figure.clear()
    #     ax = self.figure.add_subplot(111)
    #     holder = gmt.Polygon([(x, y), (x - 50, y), (x - 50, y - 50), (x, y - 50)])
    #     lightsource = gmt.Point(x+10, y+10).buffer(1.75)
    #     ax.add_patch(descartes.PolygonPatch(holder, fc='k', ec='k'))
    #     ax.add_patch(descartes.PolygonPatch(lightsource, fc='green', label='sample spectrum'))
    #     ax.set_xlabel('x [mm]')
    #     ax.set_ylabel('y [mm]')
    #     ax.set_ylim(-100, 100)
    #     ax.set_xlim(-100, 100)
    #     self.figure.tight_layout()
    #     self.canvas.draw()

    @pyqtSlot(float, float)
    def plot_position(self, x, y):
        if not self.bm:
            self.init_blitmanager(x, y)
        self.patches[0].set_xy((x, y))
        self.patches[1].set_center((x+3, y+3))
        self.bm.update()

    def init_blitmanager(self, x, y):
        holder = self.ax.add_patch(Rectangle((x, y), 2, 2))
        lightsource = self.ax.add_patch(Circle((x+3, y-3), 1))
        self.patches.extend((holder, lightsource))
        self.ax.set_xlabel('x [mm]')
        self.ax.set_ylabel('y [mm]')
        self.ax.set_ylim(-100, 100)
        self.ax.set_xlim(-100, 100)
        self.bm = BlitManager(self.canvas, self.patches)
        self.figure.tight_layout()
        self.canvas.draw()

    def fit_plots(self):
        pass

#
# if __name__ == '__main__':
#     app = QtWidgets.QApplication(sys.argv)
#     main = BlittingWidgetXY()
#     main.show()
#     sys.exit(app.exec_())
