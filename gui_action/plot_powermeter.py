import sys
from PyQt5 import QtWidgets
import logging
from PyQt5.QtCore import pyqtSlot, QTimer
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from instruments.Thorlabs.qpowermeter import QPowerMeter
from gui_action.plot_blitmanager import BlitManager
import time


class PowerMeterPlotWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger_plot = logging.getLogger('plot.PowerMeter')
        self.logger_plot.info('init powermeter plot')
        self.powermeter = QPowerMeter()
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        # plotwindow has 2000 datapoints corresponding to 10 seconds of powermeasurement
        self.log_power = np.zeros(2000)
        self.log_time = np.linspace(10, 0, 2000)
        self.lasttime = time.time()
        self.time = []
        self.blitmanager = None
        self.line = None
        self.annotation = None

    def connect_signals_slots(self):
        self.powermeter.measurement_complete_multiple.connect(self.plot)

    def disconnect_signals_slots(self):
        self.powermeter.measurement_complete_multiple.disconnect(self.plot)

    @pyqtSlot(list, list, str)
    def plot(self, times, power, plotinfo):
        self.log_power = np.append(self.log_power, power)

        if not self.blitmanager:
            self.init_blitmanager(plotinfo)
        else:
            self.line.set_ydata(1000*self.log_power[-2001:-1])
            self.annotation.set_text(plotinfo)
        self.blitmanager.update()

    def init_blitmanager(self, plotinfo):
        self.blitmanager = None
        self.line, = self.ax.plot(self.log_time, 1000 * self.log_power[-2001:-1], animated=True)
        self.annotation = self.ax.annotate(plotinfo, (0, 1), xycoords="axes fraction", xytext=(10, -10),
                                           textcoords="offset points", ha="left", va="top", animated=True)
        self.ax.set_ylabel('power [mW]')
        self.ax.set_xlabel('time [s]')
        self.ax.set_title(f"Power Meter {self.powermeter.modelinfo_plot['Model']} - Sensor Model "
                          f"{self.powermeter.sensorinfo_plot['Model']}")
        self.ax.invert_xaxis()
        self.blitmanager = BlitManager(self.canvas, [self.line, self.annotation])
        time.sleep(0.1)

    def reset_log(self):
        pass

    def fit_plots(self):
        if self.blitmanager:
            self.blitmanager.redraw_canvas_powermeter()

    def clear(self):
        self.figure.clear()
        self.canvas.draw()


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
    # setup app
    app = QtWidgets.QApplication(sys.argv)
    main = PowerMeterPlotWidget()
    main.show()
    sys.exit(app.exec_())
