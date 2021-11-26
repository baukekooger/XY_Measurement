from transitions.extensions import HierarchicalGraphMachine as Machine
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot, QEventLoop
import logging
import time
import numpy as np
import math
from yaml import safe_load as yaml_safe_load
from yaml import dump as yaml_dump
from instruments.OceanOptics.spectrometer import QSpectrometer
from pathlib import Path
from statemachine.multiple_signals import MultipleSignal


class StateMachine(QObject):
    """
    Minimal statemachine
    """
    statesignal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.logger = logging.getLogger('statemachine')
        self.logger.info('init statemachine')
        pathstateconfig = Path(__file__).parent / 'config_statemachine_minimal.yaml'
        with pathstateconfig.open() as file:
            self.stateconfig = yaml_safe_load(file)
        self.stateconfig['model'] = self
        self.machine = Machine(**self.stateconfig)
        self.spectrometer = QSpectrometer()
        self.heartbeat = QTimer()
        self.heartbeat.setInterval(int(200))
        self.heartbeat.timeout.connect(lambda pi='Plotinfo_Spectrometer': self.measure_spectrometer(pi))
        self.measurement_parameters = np.arange(1, 10)
        self.measurement_index = 0

    def _in_state(self, *args):
        self.logger.info(f'emitting current state {self.state}')
        self.statesignal.emit(self.state)

    def _connect_all(self):
        self.logger.info('connecting spectrometer')
        self.spectrometer.connect()
        self.align()

    def _disconnect_all(self):
        self.logger.info('disconnecting spectrometer')
        self.spectrometer.disconnect()

    @pyqtSlot(str)
    def measure_spectrometer(self, pi):
        if not self.spectrometer.measuring:
            self.logger.info(f'spectrometer measuring = {self.spectrometer.measuring}')
            QTimer.singleShot(0, self.spectrometer.measure)

    @pyqtSlot()
    @pyqtSlot(tuple)
    def _align(self, *args):
        self.logger.info('in alignment, starting heartbeat')
        self.heartbeat.start()
        self.logger.info(f'heartbeat state acitve = {self.heartbeat.isActive()}')

    @pyqtSlot()
    @pyqtSlot(tuple)
    def _stop_align(self, *args):
        self.logger.info('stopping alignment heartbeat')
        self.heartbeat.stop()
        self.logger.info(f'heartbeat state acitve = {self.heartbeat.isActive()}')

    @pyqtSlot()
    def _connect_signals_experiment(self):
        self.logger.info('connecting signals to triggers experiment')
        self.spectrometer.measurement_done.connect(self.process_data)
        # QTimer.singleShot(0, self.start_experiment)
        self.start_experiment()

    @pyqtSlot()
    def _disconnect_signals_experiment(self):
        self.logger.info('disconnecting signals from triggers experiment')
        self.spectrometer.measurement_done.disconnect(self.process_data)

    @pyqtSlot()
    def _prepare_measurement(self):
        self.logger.info(f'preparing measurement {self.measurement_index}')
        # QTimer.singleShot(0, self.measure)
        self.measure()

    @pyqtSlot()
    def _measure(self):
        self.logger.info('measuring spectrometer')
        plotinfo = f'measurement {self.measurement_index + 1} of {len(self.measurement_parameters)}'
        QTimer.singleShot(0, self.spectrometer.measure)

    @pyqtSlot()
    def _process_data(self):
        self.logger.info('processing data')
        self.measurement_index += 1
        try:
            a = self.measurement_parameters[self.measurement_index]
            self.logger.info('moving to next measurement parameter')
            # QTimer.singleShot(0, self.prepare)
            self.prepare()
        except IndexError:
            self.logger.info('all measurements done, finishing experiment')
            # QTimer.singleShot(0, self.measurement_complete)
            self.measurement_complete()

    @pyqtSlot()
    def _measurement_completed(self):
        self.logger.info('experiment completed, resetting measurement index to 0. ')
        self.measurement_index = 0
        # QTimer.singleShot(0, self.continue_experiment)
        # QTimer.singleShot(0, self.return_setexperiment)
        self.continue_experiment()
        self.return_setexperiment()

    @pyqtSlot()
    def _measurement_aborted(self):
        self.logger.warning(f'measurement aborted at measurement {self.measurement_index -1},'
                            f' resetting measurement index to 0')
        self.measurement_index = 0
        # QTimer.singleShot(0, self.continue_experiment)
        # QTimer.singleShot(0, self.return_setexperiment)
        self.continue_experiment()
        self.return_setexperiment()

if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers

    pathlogging = Path(__file__).parent.parent.parent / 'logging/loggingconfig_testing.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
