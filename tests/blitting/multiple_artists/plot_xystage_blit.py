import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import logging
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from instruments.Thorlabs.xystage import QXYStage
import shapely.geometry as gmt
import descartes
import numpy as np
from pathlib import Path
from yaml import safe_load as yaml_safe_load
from blitmanager import BlitManager
import random
import time

logging.basicConfig(level=logging.INFO)


class BlittingWidgetXY(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.xystage = QXYStage()
        self.figure, self.ax = plt.subplots()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = FigureCanvas(self.figure)
        self.zoombutton = QtWidgets.QPushButton('Zoom to lightsource')
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.zoombutton)
        self.setLayout(self.layout)
        self.experiment = 'transmission'
        self.substrate = 0
        self.zoom = False
        self.bm = None
        self.holder_patch = None
        self.holder_sample_edge_patch = None
        self.holder_sample_patch = None
        self.light_source_patch = None
        pathconfig = Path(__file__).parent.parent.parent.parent / 'config_main.yaml'
        with pathconfig.open() as f:
            self.config = yaml_safe_load(f)
        self.connect_signals_slots()

    def connect_signals_slots(self):
        # self.xystage.measurement_complete.connect(self.plot_position)
        self.zoombutton.clicked.connect(self.zoomview)

    def disconnect_signals_slots(self):
        try:
            self.xystage.measurement_complete.disconnect()
        except TypeError:
            pass

    @pyqtSlot(float, float)
    def plot_position(self, x, y):
        if not self.bm:
            self.init_blitmanager(x, y)
        else:
            who = 200  # width holder outline
            hho = 100  # height holder outline
            whse = self.config['substrates'][self.substrate]['whse']  # width holder sample edge
            hhse = self.config['substrates'][self.substrate]['hhse']  # height holder sample edge
            ws = self.config['substrates'][self.substrate]['ws']  # width sample
            hs = self.config['substrates'][self.substrate]['hs']  # height sample
            dfhx = self.config['substrates'][self.substrate]['dfhx']  # distance from holder x
            dfhy = self.config['substrates'][self.substrate]['dfhy']  # distance from holder y
            lightsource_x = self.config['substrates'][self.substrate][f'lightsource_x_{self.experiment}']
            lightsource_y = self.config['substrates'][self.substrate][f'lightsource_y_{self.experiment}']

            self.holder_patch.set_xy((x, y))
            self.holder_patch.set_width(-who)
            self.holder_patch.set_height(-hho)
            self.holder_sample_edge_patch.set_xy((x - dfhx + 1.5, y - dfhy + 1.5))
            self.holder_sample_edge_patch.set_width(-whse)
            self.holder_sample_edge_patch.set_height(-hhse)
            self.holder_sample_patch.set_xy((x - dfhx, y - dfhy))
            self.holder_sample_patch.set_width(-ws)
            self.holder_sample_patch.set_height(-hs)
            self.light_source_patch.set_center((lightsource_x, lightsource_y))
            self.bm.update()

    def init_blitmanager(self, x, y):
        who = 200  # width holder outline
        hho = 100  # height holder outline
        whse = self.config['substrates'][self.substrate]['whse']  # width holder sample edge
        hhse = self.config['substrates'][self.substrate]['hhse']  # height holder sample edge
        ws = self.config['substrates'][self.substrate]['ws']  # width sample
        hs = self.config['substrates'][self.substrate]['hs']  # height sample
        dfhx = self.config['substrates'][self.substrate]['dfhx']  # distance from holder x
        dfhy = self.config['substrates'][self.substrate]['dfhy']  # distance from holder y
        lightsource_x = self.config['substrates'][self.substrate][f'lightsource_x_{self.experiment}']
        lightsource_y = self.config['substrates'][self.substrate][f'lightsource_y_{self.experiment}']

        self.holder_patch = self.ax.add_patch(Rectangle((x, y), -who, -hho, fc='black'))
        self.holder_sample_edge_patch = self.ax.add_patch(Rectangle((x - dfhx + 1.5, y - dfhy + 1.5),
                                                                    -whse, -hhse, fc='dimgrey'))
        self.holder_sample_patch = self.ax.add_patch(Rectangle((x - dfhx, y - dfhy), -ws, -hs, fc='paleturquoise'))
        self.light_source_patch = self.ax.add_patch(Circle((lightsource_x, lightsource_y), 1.75, fc='orange'))

        self.ax.set_xlabel('x [mm]')
        self.ax.set_ylabel('y [mm]')

        self.ax.set_xlim(-200, 100)
        self.ax.set_ylim(lightsource_y + 50, -hho)
        self.ax.invert_yaxis()
        self.ax.invert_xaxis()
        self.bm = BlitManager(self.canvas, [self.holder_patch, self.holder_sample_edge_patch,
                                            self.holder_sample_patch, self.light_source_patch])
        self.figure.tight_layout()
        self.canvas.draw()

    @pyqtSlot()
    def zoomview(self):
        who = 200
        hho = 100
        whse = self.config['substrates'][self.substrate]['whse']  # width holder sample edge
        hhse = self.config['substrates'][self.substrate]['hhse']  # height holder sample edge
        lightsource_x = self.config['substrates'][self.substrate][f'lightsource_x_{self.experiment}']
        lightsource_y = self.config['substrates'][self.substrate][f'lightsource_y_{self.experiment}']
        if not self.zoom:
            self.zoom = True
            self.ax.set_xlim(lightsource_x - whse / 2 * 1.1, lightsource_x + whse / 2 * 1.1)
            self.ax.set_ylim(lightsource_y - hhse / 2 * 1.1, lightsource_y + hhse / 2 * 1.1)
            self.ax.invert_xaxis()
        else:
            self.zoom = False
            self.ax.set_xlim(-200, 100)
            self.ax.set_ylim(lightsource_y + 50, -hho)
            self.ax.invert_xaxis()
            self.ax.invert_yaxis()
        self.figure.tight_layout()
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

    def fit_plots(self):
        pass


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = BlittingWidgetXY()
    main.show()
    sys.exit(app.exec_())
