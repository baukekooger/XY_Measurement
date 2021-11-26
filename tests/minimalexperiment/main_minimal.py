import logging
from PyQt5 import QtWidgets
import sys
from PyQt5.QtCore import QTimer, QThread, pyqtSlot
from mainui import Ui_MainWindow
from yaml import safe_load as yaml_safe_load, dump
from statemachine_minimal import StateMachine
import time
import datetime
from os import path
import random


class MinimalExperiment(QtWidgets.QMainWindow):
    """
    Minimal experiment for testing reponsiveness of the ui during an experiment.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Init mainwindow')
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.statemachine = StateMachine()
        self.statemachinethread = QThread()
        self.statemachine.moveToThread(self.statemachinethread)

        self.spectrometerthread = QThread()
        self.statemachine.spectrometer.moveToThread(self.spectrometerthread)

        self.connect_signals()

        self.statemachinethread.start()
        self.spectrometerthread.start()
        self.statemachine.start()

        self.ui.widget_spectrometer.spectrometer = self.statemachine.spectrometer
        self.ui.widget_spectrometer.connect_signals_slots()

    def connect_signals(self):
        self.logger.info('connecting signals main ui')
        self.statemachine.statesignal.connect(self.set_state_indicator)
        self.ui.pushButton_random_number.clicked.connect(self.random_number)
        self.ui.pushButton_start_stop_experiment.clicked.connect(self.start_experiment)
        self.ui.pushButton_align_stop_align.clicked.connect(self.statemachine.align_experiment)
        self.ui.pushButton_fit_plots.clicked.connect(self.ui.widget_spectrometer.fit_plots)

    def random_number(self):
        number = f'Random number = {random.random():.3f}'
        self.logger.info(f'showing {number}')
        self.ui.label_random_number.setText(number)

    @pyqtSlot()
    def start_experiment(self):
        self.logger.info('starting experiment')
        self.ui.pushButton_start_stop_experiment.setText('Stop Experiment')
        self.ui.pushButton_start_stop_experiment.clicked.disconnect()
        self.ui.pushButton_start_stop_experiment.clicked.connect(self.stop_experiment)
        QTimer.singleShot(0, self.statemachine.init_experiment)

    @pyqtSlot()
    def stop_experiment(self):
        self.logger.info('stopping experiment')
        self.ui.pushButton_start_stop_experiment.setText('Start Experiment')
        self.ui.pushButton_start_stop_experiment.clicked.disconnect()
        self.ui.pushButton_start_stop_experiment.clicked.connect(self.start_experiment)
        QTimer.singleShot(0, self.statemachine.abort)

    def quit_all_threads(self):
        self.logger.info('quitting threads')
        self.statemachinethread.quit()
        self.spectrometerthread.quit()

    def closeEvent(self, event):
        self.logger.info('close event called')
        self.statemachine.abort()
        self.statemachine._disconnect_all()
        self.quit_all_threads()
        self.logger.info('close event finished')
        event.accept()

    @pyqtSlot(str)
    def set_state_indicator(self, state):
        self.logger.info(f'got statechange from statemachine, current state = {state}')
        self.ui.label_state.setText(f'Current state = {state}')


if __name__ == '__main__':
    # setup logging
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers
    pathlogging = Path(__file__).parent.parent.parent / 'logging/loggingconfig_testing.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    app = QtWidgets.QApplication(sys.argv)
    main = MinimalExperiment()
    main.show()
    sys.exit(app.exec_())
