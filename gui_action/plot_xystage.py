import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import logging
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from instruments.Thorlabs.xystage import QXYStage
import shapely.geometry as gmt
import descartes
import numpy as np
from pathlib import Path
from yaml import safe_load as yaml_safe_load
import random
import time

logging.basicConfig(level=logging.INFO)


class XYStagePlotWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.figure, self.ax = None, None
        self.xystage = QXYStage()
        self.figure = plt.figure()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)
        self.experiment = None
        self.substrate = None
        pathconfig = Path(__file__).parent.parent / 'config_main.yaml'
        with pathconfig.open() as f:
            self.config = yaml_safe_load(f)

    def connect_signals_slots(self):
        self.xystage.measurement_complete.connect(self.plot_position)

    def disconnect_signals_slots(self):
        try:
            self.xystage.measurement_complete.disconnect()
        except TypeError:
            pass

    @pyqtSlot(float, float)
    def plot_position(self, x, y):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        who = 200  # width holder outline
        hho = 100  # height holder outline
        whse = self.config['substrates'][self.substrate]['whse']  # width holder sample edge
        hhse = self.config['substrates'][self.substrate]['hhse']  # height holder sample edge
        ws = self.config['substrates'][self.substrate]['ws']  # width sample
        hs = self.config['substrates'][self.substrate]['hs']  # height sample
        dfhx = self.config['substrates'][self.substrate]['dfhx']  # distance from holder x
        dfhy = self.config['substrates'][self.substrate]['dfhy']  # distance from holder y

        holes_tapped_x = [12.5, 12.5, 37.5, 37.5, 62.5, 62.5, 62.5, 62.5, 87.5, 87.5, 87.5, 87.5]
        holes_tapped_y = [62.5, 87.5, 62.5, 87.5, 12.5, 37.5, 62.5, 87.5, 12.5, 37.5, 62.5, 87.5]

        holes_drilled_x = [25, 50, 75, 100]
        holes_drilled_y = [75, 75, 75, 75]

        holder = gmt.Polygon([(x, y), (x - who, y), (x - who, y - hho), (x, y - hho)])
        sample_edge = gmt.Polygon([(x - dfhx, y - dfhy), (x - dfhx - whse, y - dfhy),
                                         (x - dfhx - whse, y - dfhy - hhse), (x - dfhx, y - dfhy - hhse)])
        sample = gmt.Polygon([
            (x - dfhx - (whse - ws) / 2, y - dfhy - (hhse - hs) / 2),
            (x - dfhx - whse + (whse - ws) / 2, y - dfhy - (hhse - hs) / 2),
            (x - dfhx - whse + (whse - ws) / 2, y - dfhy - hhse + (hhse - hs) / 2),
            (x - dfhx - (whse - ws) / 2, y - dfhy - hhse + (hhse - hs) / 2)
        ])

        lightsource_x = self.config['substrates'][self.substrate][f'lightsource_x_{self.experiment}']
        lightsource_y = self.config['substrates'][self.substrate][f'lightsource_y_{self.experiment}']
        lightsource = gmt.Point(lightsource_x, lightsource_y).buffer(1.75)

        ax.add_patch(descartes.PolygonPatch(holder, fc='k', ec='k'))
        ax.add_patch(descartes.PolygonPatch(sample_edge, fc='dimgrey'))
        ax.add_patch(descartes.PolygonPatch(sample, fc='lightcyan', ec='lightcyan'))

        holes = []
        for h_x, h_y in zip(holes_tapped_x, holes_tapped_y):
            hole = gmt.Point(x-h_x, y-h_y).buffer(2.75)
            holes.append(hole)
            ax.add_patch(descartes.PolygonPatch(hole, fc='white', ec='white'))

        for h_x, h_y in zip(holes_drilled_x, holes_drilled_y):
            hole = gmt.Point(x-h_x, y-h_y).buffer(3.3)
            holes.append(hole)
            ax.add_patch(descartes.PolygonPatch(hole, fc='white', ec='white'))

        if lightsource.within(sample):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='green', label='sample spectrum'))
            ax.legend()
        elif lightsource.intersects(sample_edge) and ~lightsource.within(sample):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='red', label='on edge'))
            ax.legend()
        elif lightsource.overlaps(holder) and ~lightsource.within(sample):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='red', label='on edge'))
            ax.legend()
        elif any([lightsource.overlaps(hole) for hole in holes]):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='red', label='on edge'))
            ax.legend()
        elif any([lightsource.within(hole) for hole in holes]):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='yellow', label='lamp spectrum'))
            ax.legend()
        elif lightsource.within(holder) and ~lightsource.intersects(sample_edge):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='purple', label='dark spectrum'))
            ax.legend()
        elif lightsource.disjoint(holder):
            ax.add_patch(descartes.PolygonPatch(lightsource, fc='yellow', label='lamp spectrum'))
            ax.legend()

        ax.invert_xaxis()
        ax.set_xlabel('x [mm]')
        ax.set_ylabel('y [mm]')
        self.figure.tight_layout()
        if self.experiment == 'transmission':
            ax.set(xlim=(90, -50), ylim=(-50, 90))
        else:
            ax.set(xlim=(90, -50), ylim=(-50, 170))
        self.canvas.draw()

    def plot_layout(self, xnum, ynum, xoffleft, xoffright, yoffbottom, yofftop):
        whse = self.config['substrates'][self.substrate]['whse']  # width holder sample edge
        hhse = self.config['substrates'][self.substrate]['hhse']  # height holder sample edge
        ws = self.config['substrates'][self.substrate]['ws']  # width sample
        hs = self.config['substrates'][self.substrate]['hs']  # height sample
        bw = 3.5    # width of the beam of light
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        sample_edge = gmt.Polygon([(0, 0), (whse, 0), (whse, hhse), (0, hhse)])
        sample = gmt.Polygon([((whse - ws) / 2, (hhse - hs) / 2), (whse - (whse - ws) / 2, (hhse - hs) / 2),
                              (whse - (whse - ws) / 2, hhse - (hhse - hs) / 2),
                              ((whse - ws) / 2, hhse - (hhse - hs) / 2)])
        ax.add_patch(descartes.PolygonPatch(sample_edge, fc='dimgrey'))
        ax.add_patch(descartes.PolygonPatch(sample, fc='lightcyan', ec='lightcyan'))

        xoffleft_mm = (ws - bw) * xoffleft / (100 + xoffright)
        xoffright_mm = (ws - bw) * xoffright / (100 + xoffleft)
        yoffleft_mm = (hs - bw) * yoffbottom / (100 + yofftop)
        yoffright_mm = (hs - bw) * yofftop / (100 + yoffbottom)

        measurements_x = [(whse + xoffleft_mm - xoffright_mm) / 2]
        measurements_x = np.linspace((whse - ws + bw) / 2 + xoffleft_mm,
                                     whse - (whse - ws + bw) / 2 - xoffright_mm, xnum) if xnum > 1 else measurements_x
        lenx = len(measurements_x)
        measurements_y = [(hhse + yoffleft_mm - yoffright_mm) / 2]
        measurements_y = np.linspace((hhse - hs + bw) / 2 + yoffleft_mm,
                                     hhse - (hhse - hs + bw) / 2 - yoffright_mm, ynum) if ynum > 1 else measurements_y
        leny = len(measurements_y)
        measurements_x = np.repeat(measurements_x, leny)
        measurements_y = np.tile(measurements_y, lenx)

        measurements = []
        for m_x, m_y in zip(measurements_x, measurements_y):
            measurement = gmt.Point(m_x, m_y).buffer(bw / 2)
            measurements.append(measurement)
            ax.add_patch(descartes.PolygonPatch(measurement, fc='green', ec='green'))

        ax.set_xlabel('x [mm]')
        ax.set_ylabel('y [mm]')
        ax.set(xlim=(0, whse), ylim=(0, hhse))
        # plt.axis('scaled')
        self.figure.tight_layout()
        self.canvas.draw()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = XYStagePlotWidget()
    main.show()
    sys.exit(app.exec_())
