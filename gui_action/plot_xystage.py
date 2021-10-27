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
import numpy as np
from pathlib import Path
from yaml import safe_load as yaml_safe_load
from gui_action.plot_blitmanager import BlitManager
import random
import time


class XYStagePlotWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('plot.XYStage')
        self.logger.info('init plotwindow XYStage (position indicator)')
        self.xystage = QXYStage()
        self.figure, self.ax = plt.subplots()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.zoombutton = QtWidgets.QPushButton('zoom to lightsource')
        self.zoombutton.isCheckable()
        self.layout.addWidget(self.zoombutton)
        self.setLayout(self.layout)
        self.experiment = 'transmission'
        self.substrate = '50X50 mm (Borofloat)'
        self.zoom = False
        self.bm = None
        self.holder_patch = None
        self.holder_sample_edge_patch = None
        self.holder_sample_patch = None
        self.light_source_patch = None
        pathconfig = Path(__file__).parent.parent / 'config_main.yaml'
        with pathconfig.open() as f:
            self.config = yaml_safe_load(f)

    def connect_signals_slots(self):
        self.xystage.measurement_complete.connect(self.plot_position)
        self.zoombutton.clicked.connect(self.zoomview)

    def disconnect_signals_slots(self):
        try:
            self.xystage.measurement_complete.disconnect()
            self.zoombutton.clicked.disconnect()
        except TypeError:
            pass

    @pyqtSlot(float, float)
    def plot_position(self, x, y):
        if not self.zoombutton.isVisible():
            self.zoombutton.setVisible(True)
        if self.substrate == '22X22 mm (Quartz small)':
            # adds extra distance for small holder
            x = x + 25
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
        self.ax.clear()
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

        self.ax.set_xlabel('x')
        self.ax.set_ylabel('y')

        self.ax.set_xlim(-200, 100)
        self.ax.set_ylim(150, -150)
        self.ax.invert_yaxis()
        self.ax.invert_xaxis()
        self.ax.xaxis.set_ticks([])
        self.ax.yaxis.set_ticks([])
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
            self.zoombutton.setText('zoom out')
            self.ax.set_xlim(lightsource_x - whse / 2 * 1.1, lightsource_x + whse / 2 * 1.1)
            self.ax.set_ylim(lightsource_y - hhse / 2 * 1.1, lightsource_y + hhse / 2 * 1.1)
            self.ax.invert_xaxis()
            self.ax.xaxis.set_ticks([])
            self.ax.yaxis.set_ticks([])
        else:
            self.zoom = False
            self.zoombutton.setText('zoom to lightsource')
            self.ax.set_xlim(-200, 100)
            self.ax.set_ylim(150, -150)
            self.ax.invert_xaxis()
            self.ax.invert_yaxis()
            self.ax.xaxis.set_ticks([])
            self.ax.yaxis.set_ticks([])
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_layout(self, xnum, ynum, xoffleft, xoffright, yoffbottom, yofftop):
        if self.zoombutton.isVisible():
            self.zoombutton.setVisible(False)
        self.ax.clear()
        if self.bm:
            self.bm = None
        whse = self.config['substrates'][self.substrate]['whse']  # width holder sample edge
        hhse = self.config['substrates'][self.substrate]['hhse']  # height holder sample edge
        ws = self.config['substrates'][self.substrate]['ws']  # width sample
        hs = self.config['substrates'][self.substrate]['hs']  # height sample
        bw = 3.5    # width of the beam of light

        sample_edge = gmt.Polygon([(0, 0), (whse, 0), (whse, hhse), (0, hhse)])
        sample = gmt.Polygon([((whse - ws) / 2, (hhse - hs) / 2), (whse - (whse - ws) / 2, (hhse - hs) / 2),
                              (whse - (whse - ws) / 2, hhse - (hhse - hs) / 2),
                              ((whse - ws) / 2, hhse - (hhse - hs) / 2)])
        self.ax.add_patch(descartes.PolygonPatch(sample_edge, fc='dimgrey'))
        self.ax.add_patch(descartes.PolygonPatch(sample, fc='lightcyan', ec='lightcyan'))

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
            self.ax.add_patch(descartes.PolygonPatch(measurement, fc='green', ec='green'))

        self.ax.set_xlabel('x [mm]')
        self.ax.set_ylabel('y [mm]')
        self.ax.set(xlim=(0, whse), ylim=(0, hhse))
        # plt.axis('scaled')
        self.figure.tight_layout()
        self.canvas.draw()

    def fit_plots(self):
        pass


if __name__ == '__main__':
    # set up logging if file called directly
    import yaml
    import logging.config
    pathlogging = Path(__file__).parent.parent / 'loggingconfig.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    # setup pyqt app
    app = QtWidgets.QApplication(sys.argv)
    main = XYStagePlotWidget()
    main.show()
    sys.exit(app.exec_())
