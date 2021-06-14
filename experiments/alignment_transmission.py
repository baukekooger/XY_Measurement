# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 13:43:02 2017

@author: epjmerkx
"""
from transitions import Machine, MachineError, State
import logging
import time
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot, QEventLoop
import numpy as np
from contextlib import contextmanager

from instruments.OceanOptics.spectrometer_pyqt import QSpectrometer
from instruments.Thorlabs.xystage_pyqt import QXYStage

logging.basicConfig(level=logging.INFO)


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


def wait_for_true(condition, timeout, polltime=0.1):
    t1 = time.time()
    if callable(condition):
        while (time.time() - t1 < timeout) and not condition():
            logging.info('Waiting...')
            time.sleep(polltime)
            if time.time() - t1 >= timeout: raise TimeoutError
    else:
        while (time.time() - t1 < timeout) and not condition:
            logging.info('Waiting...')
            time.sleep(polltime)
            if time.time() - t1 >= timeout: raise TimeoutError


def wait_for_true_or_exit(condition, timeout, polltime=0.1):
    t1 = time.time()
    if callable(condition):
        while (time.time() - t1 < timeout) and not condition():
            logging.info('Waiting...')
            time.sleep(polltime)
            if time.time() - t1 >= timeout:
                logging.warning('Condition not met in allotted time!')
                break
    else:
        while (time.time() - t1 < timeout) and not condition:
            logging.info('Waiting...')
            time.sleep(polltime)
            if time.time() - t1 >= timeout:
                logging.warning('Condition not met in allotted time!')
                break


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


class BaseExperiment(QObject):
    """Base State Machine for any Experiment

    Since this involves a State Machine, all methods are 'private'
    and should be accessed through this class' states.
    """

    signalstatechange = pyqtSignal(str)  # machine.prepare_event

    def __init__(self, name, parent=None):
        super().__init__()
        states = [State('waiting', on_enter=['_statechange', '_finalize'])]
        self.machine = Machine(model=self, states=states,
                               initial='waiting', name=name,
                               queued=True)
        self.instruments = []
        self.name = name
        self.timeout = 60

    def _parse_config(self):
        pass

    def _connect_all(self):
        """Connects all instruments"""
        for instrument in self.instruments:
            logging.info(f'Connecting to {repr(instrument)}')
            instrument.connect()
            instrument.timeout = self.timeout

    def _finalize(self):
        """Stops all measurements and disconnects all Instruments
        """
        for instrument in self.instruments:
            instrument.measuring = False
            instrument.disconnect()

    def _statechange(self):
        """
        Emits:
            signalstatechange (str): String with the current state
        """
        self.signalstatechange.emit(self.state)


class Alignment(BaseExperiment):
    def __init__(self, name):
        super().__init__(name=name)

        states = [
            State('parsing configuration', on_enter='_parse_config'),
            State('connecting', on_enter='_connect_all'),
            State('aligning', on_enter='_align')
        ]
        transitions = [
            {'trigger': 'parse_config', 'source': 'waiting',
             'dest': 'parsing configuration'},
            {'trigger': 'connect_all', 'source': 'parsing configuration',
             'dest': 'connecting'},
            {'trigger': 'align', 'source': 'connecting',
             'dest': 'aligning'},
            {'trigger': 'finalize', 'source': '*',
             'dest': 'waiting'}
        ]
        for s in states:
            s.on_enter.append('_statechange')
            s.on_enter.reverse()
            self.machine.add_state(s)
        for t in transitions:
            self.machine.add_transition(t['trigger'], t['source'], t['dest'])

        self.polltime = 0.1
        self.heartbeat = QTimer()
        self.heartbeat.setInterval(self.polltime * 1000)
        self.heartbeat.timeout.connect(self.measure_instruments)
        ## Devices
        self.xystage = QXYStage()
        self.instruments.append(self.xystage)

    def measure_instruments(self):
        for instrument in self.instruments:
            if not instrument.measuring:
                QTimer.singleShot(0, instrument.measure)

    @pyqtSlot()
    def run(self):
        # Run statemachine
        self.parse_config()
        self.connect_all()
        self.align()

    def _align(self):
        self.heartbeat.start()

    def _finalize(self):
        for instrument in self.instruments:
            instrument.measuring = False
            instrument.disconnect()
        self.heartbeat.stop()


class TransmissionAlignment(Alignment):
    """Alignment for transmission experiments
    """

    def __init__(self):
        super().__init__(name='TransmissionAlignment')
        # Devices
        self.spectrometer = QSpectrometer()
        self.instruments.append(self.spectrometer)

