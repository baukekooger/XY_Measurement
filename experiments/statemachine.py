from transitions.extensions import HierarchicalGraphMachine as Machine
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot, QEventLoop
import logging
import time
import numpy as np
from contextlib import contextmanager
from yaml import safe_load as yaml_safe_load
from instruments.OceanOptics.spectrometer_pyqt import QSpectrometer
from instruments.Thorlabs.xystage_pyqt import QXYStage
from pathlib import Path

logging.basicConfig(level=logging.INFO)

instrument_parser = {
    'xystage': QXYStage,
    'spectrometer': QSpectrometer,
}


def listify(obj):
    if obj is None:
        return []
    else:
        return obj if isinstance(obj, (list, np.ndarray, tuple, type(None))) else [obj]


def timed(func):
    def wrapper(self, *args, **kwargs):
        t1 = time.time()
        result = func(self, *args, **kwargs)
        t2 = time.time()
        self.measurement_duration += t2 - t1
        return result

    return wrapper


@contextmanager
def wait_for_signal(signal, timeout=60):
    """ Block execution until signal is emitted, or timeout (s) expires """
    loop = QEventLoop()
    signal.connect(loop.quit)
    yield
    if timeout is not None:
        QTimer.singleShot(timeout * 1000, loop.quit)
    # Direct execution of the loop is not possible
    # Has to be done by launching it in the QTimer thread
    loop.exec_()


class StateMachine(QObject):
    """State Machine for any Experiment

    Since this involves a State Machine, all methods are 'private'
    and should be accessed through this class' states
    """

    signalstatechange = pyqtSignal(str)     # signal that emits the state
    progress = pyqtSignal(float)            # signal emitting the progress of the measurement
    ect = pyqtSignal(float)                 # another signal
    connecting_done = pyqtSignal()

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
        self.experiment = None
        self.is_done = False
        self.instruments = {}
        self.timeout = 60
        self.is_done = False
        self._init_align()

    def _init_align(self):
        self.polltime = 0.1
        self.heartbeat = QTimer()
        self.heartbeat.setInterval(int(self.polltime * 1000))
        self.heartbeat.timeout.connect(self._measure_instruments)

    def _from_state(self, *args):
        self.signalstatechange.emit(f'from state {self.state}')

    def _in_state(self, *args):
        self.signalstatechange.emit(f'finished in state {self.state}')

    def _start(self):
        pass

    def _define_experiment(self, page):
        # checks the necessary instruments, disconnects ones that are not necessary anymore. Adds new instruments.
        self.experiment = self.config['experiments'][page]
        instruments_needed = self.config['instruments'][self.experiment]
        to_remove = [inst for inst in self.instruments.keys() if (inst not in instruments_needed)]
        to_add = [inst for inst in instruments_needed if (inst not in self.instruments.keys())]
        for inst in to_remove:
            self.instruments[inst].measuring = False
            self.instruments[inst].disconnect()
            self.instruments.pop(inst)
        for inst in to_add:
            self.instruments[inst] = instrument_parser[inst]()
        self.connect_all()

    def _parse_config(self):
        pass

    def _connect_all(self):
        for inst in self.instruments.keys():
            if self.instruments[inst].connected:
                logging.info(f'{inst} already connected')
            else:
                logging.info(f'{inst} connecting')
                self.instruments[inst].connect()
                self.instruments[inst].timeout = self.timeout


    def _align(self):
        self.heartbeat.start()

    def _stop_align(self):
        self.heartbeat.stop()

    def _measure_instruments(self):
        for inst in self.instruments.keys():
            if not self.instruments[inst].measuring:
                QTimer.singleShot(0, self.instruments[inst].measure)

    def _open_file(self):
        pass

    def _measure(self):
        pass

    def _prepare(self):
        pass

    def _process_data(self):
        pass

    def _write_file(self):
        pass

    def _calculate_progress(self):
        pass

    def _load_configuration(self):
        pass

    def _save_configuration(self):
        pass

    def _experiment_aborted(self):
        pass

    def _abort(self):
        pass

    def _completed(self):
        pass

    def _prepare_measurement(self):
        pass
