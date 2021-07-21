from transitions.extensions import HierarchicalGraphMachine as Machine
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot, QEventLoop
import logging
import time
import numpy as np
from contextlib import contextmanager
from yaml import safe_load as yaml_safe_load
from yaml import dump as yaml_dump
from instruments.OceanOptics.spectrometer import QSpectrometer
from instruments.Thorlabs import apt
from instruments.Thorlabs.xystage import QXYStage
from pathlib import Path
from netCDF4 import Dataset


class StateMachine(QObject):
    """State Machine for any Experiment

    Since this involves a State Machine, all methods are 'private'
    and should be accessed through this class' states
    """

    signalstatechange = pyqtSignal(str)     # signal that emits the state
    progress = pyqtSignal(float)            # signal emitting the progress of the measurement
    ect = pyqtSignal(float)                 # another signal
    connecting_done = pyqtSignal()
    signal_return_setexperiment = pyqtSignal()
    state = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        pathstateconfig = Path.home() / 'PycharmProjects/XY_New/experiments/config_statemachine.yaml'
        with pathstateconfig.open() as f:
            self.stateconfig = yaml_safe_load(f)
        self.stateconfig['model'] = self
        self.machine = Machine(**self.stateconfig)
        pathconfig = Path.home() / 'PycharmProjects/XY_New/config_main.yaml'
        with pathconfig.open() as f:
            self.config = yaml_safe_load(f)
        self.experiment = 'transmission'
        self.instruments = {}
        self.measurement_parameters = {}
        self.timeout = 60


    def _parse_config(self):
        path_settings = Path.home() / 'PycharmProjects/XY_New/settings_ui.yaml'
        with path_settings.open() as f:
            settings = yaml_safe_load(f)
        xysettings = settings[self.experiment][f'widget_xystage_{self.experiment}']
        x_start = xysettings['doubleSpinBox_x_start']
        x_stop = xysettings['doubleSpinBox_x_stop']
        x_num = xysettings['spinBox_x_num']
        x = np.linspace(x_start, x_stop, num=x_num)
        y_start = xysettings['doubleSpinBox_y_start']
        y_stop = xysettings['doubleSpinBox_y_stop']
        y_num = xysettings['spinBox_y_num']
        y = np.linspace(y_start, y_stop, num=y_num)
        self.measurement_parameters = {}
        self._add_measurement_parameter('x', x)
        self._add_measurement_parameter('y', y)
        dark_lamp_x = np.array((20, 0))
        dark_lamp_y = np.array((80, 0))
        self.measurement_parameters['x'] = np.hstack((dark_lamp_x, self.measurement_parameters['x']))
        self.measurement_parameters['y'] = np.hstack((dark_lamp_y, self.measurement_parameters['y']))

    def _add_measurement_parameter(self, name, parameter):
        length = None
        for keys, values in self.measurement_parameters.items():
            length = len(values)
            self. measurement_parameters[keys] = np.repeat(values, len(parameter))
        if length:
            parameter = np.tile(parameter, length)
        self.measurement_parameters[name] = parameter
        return parameter

    def _write_file(self):
        x = self.measurement_parameters['x'][self.measurement_index]
        y = self.measurement_parameters['y'][self.measurement_index]
        x_inx = list(np.unique(self.measurement_parameters['x'][2:-1])).index(x)
        y_iny = list(np.unique(self.measurement_parameters['y'][2:-1])).index(y)
        print(x)
        print(y)
        print(x_inx)
        print(y_iny)
