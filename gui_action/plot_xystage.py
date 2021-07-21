import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import logging
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from instruments.Thorlabs.xystage import QXYStage
import shapely.geometry as gmt
import descartes
import random
import time
logging.basicConfig(level=logging.INFO)


class XYStagePlotWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.figure, self.ax = None, None
        self.canvas = None
        self.layout = None
        self.xystage = QXYStage()

    def connect_signals_slots(self):
        self.figure = plt.figure()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)
        self.plot_position(50, 50)
        self.xystage.measurement_complete.connect(self.handle_plot)

    @pyqtSlot(float, float)
    def handle_plot(self, x, y):
        print(f'x = {x} and y = {y}')
        self.plot_position(x, y)

    def plot_position(self, x, y):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        t1 = time.time()
        who = 150  # width holder outline
        hho = 100  # height holder outline
        whse = 50  # width holder sample edge
        hhse = 50  # height holder sample edge
        ws = 47  # width sample
        hs = 47  # height sample
        dfhx = 15  # distance from holder x
        dfhy = 15  # distance from holder y
        # ax.clear()
        holder = gmt.Polygon([(x, y), (x - who, y), (x - who, y - hho), (x, y - hho)])
        sampleholder_edge = gmt.Polygon([(x - dfhx, y - dfhy), (x - dfhx - whse, y - dfhy),
                                         (x - dfhx - whse, y - dfhy - hhse), (x - dfhx, y - dfhy - hhse)])
        sample = gmt.Polygon([
            (x - dfhx - (whse - ws) / 2, y - dfhy - (hhse - hs) / 2),
            (x - dfhx - whse + (whse - ws) / 2, y - dfhy - (hhse - hs) / 2),
            (x - dfhx - whse + (whse - ws) / 2, y - dfhy - hhse + (hhse - hs) / 2),
            (x - dfhx - (whse - ws) / 2, y - dfhy - hhse + (hhse - hs) / 2)
        ])

        lightsource = gmt.Point(20, 20).buffer(2)

        ax.add_patch(descartes.PolygonPatch(holder, fc='k', ec='k'))
        ax.add_patch(descartes.PolygonPatch(sampleholder_edge, fc='dimgrey'))
        ax.add_patch(descartes.PolygonPatch(sample, fc='lightcyan', ec='lightcyan'))

        if lightsource.within(sample):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='green', label='sample spectrum'))
            ax.legend()
        elif lightsource.intersects(sampleholder_edge) and ~lightsource.within(sample):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='red', label='on edge'))
            ax.legend()
        elif lightsource.overlaps(holder) and ~lightsource.within(sample):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='red', label='on edge'))
            ax.legend()
        elif lightsource.within(holder) and ~lightsource.intersects(sampleholder_edge):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='purple', label='dark spectrum'))
            ax.legend()
        elif lightsource.disjoint(holder):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='yellow', label='lamp spectrum'))
            ax.legend()

        ax.invert_xaxis()
        ax.set_xlabel('x [mm]')
        ax.set_ylabel('y [mm]')
        self.figure.tight_layout()
        ax.set(xlim=(90, -50), ylim=(-50, 90))
        self.canvas.draw()
        print(f'x = {x} and y = {y}')
        t2 = time.time()
        print(f'elapsed time = {t2-t1} seconds')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = XYStagePlotWidget()
    main.show()
    sys.exit(app.exec_())
