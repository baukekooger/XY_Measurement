# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 13:43:02 2017

@author: epjmerkx
"""
from transitions import Machine, MachineError, State
import logging
import time
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot, QEventLoop
import yaml
import numpy as np
from contextlib import contextmanager
from netCDF4 import Dataset

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
            logging.info('Connecting to {}'.format(repr(instrument)))
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


class Experiment(BaseExperiment):
    progress = pyqtSignal(float)
    ect = pyqtSignal(float)

    def __init__(self, name, configfile='config.yml'):
        super().__init__(name=name)
        states = [
            State('parsing configuration', on_enter='_parse_config'),
            State('connecting', on_enter='_connect_all'),
            State('opening file', on_enter='_open_file'),
            State('measuring', on_enter='_measure'),
            State('preparing', on_enter='_prepare'),
            State('processing data', on_enter='_process_data'),
            State('writing to file', on_enter='_write_file'),
            State('calculating progress', on_enter='_calculate_progress')
        ]
        transitions = [
            {'trigger': 'connect_all', 'source': 'waiting',
             'dest': 'connecting'},
            {'trigger': 'parse_config', 'source': 'connecting',
             'dest': 'parsing configuration'},
            {'trigger': 'open_file', 'source': 'parsing configuration',
             'dest': 'opening file'},
            {'trigger': 'prepare', 'source': ['opening file', 'writing to file'],
             'dest': 'preparing', 'unless': 'is_done'},
            {'trigger': 'measure', 'source': 'preparing',
             'dest': 'measuring', 'unless': 'is_done'},
            {'trigger': 'process_data', 'source': 'measuring',
             'dest': 'processing data', 'unless': 'is_done'},
            {'trigger': 'write_file', 'source': '*',
             'dest': 'writing to file'},
            {'trigger': 'calculate_progress', 'source': '*',
             'dest': 'calculating progress', 'unless': 'is_done'},
            {'trigger': 'finalize', 'source': '*',
             'dest': 'waiting'}]
        for s in states:
            s.on_enter.append('_statechange')
            s.on_enter.reverse()
            self.machine.add_state(s)
        for t in transitions:
            try:
                self.machine.add_transition(t['trigger'], t['source'], t['dest'],
                                            unless=t['unless'])
            except KeyError:
                self.machine.add_transition(t['trigger'], t['source'], t['dest'])
        self.measurement_duration = 0
        self._done = True
        self.configfile = configfile
        self.measurement_params = {}
        self.measurement_index = 0
        self.startingtime = time.time()

        ## Devices
        self.xystage = QXYStage()
        self.instruments.append(self.xystage)

    @pyqtSlot()
    def run(self):
        self.measurement_duration = 0
        self._done = False
        self.measurement_index = 0
        try:
            self.connect_all()
            self.parse_config()
            self.open_file()
        except Exception as e:
            self.finalize()
            raise e
        while not self.state == 'waiting':
            try:
                self.prepare()
                self.measure()
                self.process_data()
                self.calculate_progress()
                self.write_file()
                self.measurement_index += 1
            except (MachineError, IndexError):
                self.calculate_progress()
                self.finalize()
                self.dataset.close()
                self._done = True
                pass
            except Exception as e:
                self.finalize()
                self.dataset.close()
                self._done = True
                raise e

    def is_done(self):
        return self._done

    def _parse_config(self):
        """Read in the `config.yml` file for this Experiment
        """
        with open(self.configfile, 'r') as ymlfile:
            config = yaml.load(ymlfile)
        self.storage_dir = config[self.name]['general']['storage_dir']
        self.sample = config[self.name]['general']['sample']
        #        self.comments = config[self.name]['general']['comments']
        xysettings = config[self.name]['xystage']
        xstart = xysettings['xstart']
        xstop = xysettings['xstop']
        xnum = xysettings['xnum']
        x = np.linspace(xstart, xstop, xnum)
        ystart = xysettings['ystart']
        ystop = xysettings['ystop']
        ynum = xysettings['ynum']
        y = np.linspace(ystart, ystop, ynum)
        self.measurement_params = {}
        # y is added before x since the y stage should move the least
        self.add_measurement_param('y', y)
        self.add_measurement_param('x', x)

    def add_measurement_param(self, name, param):
        """ Adds measurement parameters as
        1: 01
        2: 01
        3: ab

        add_measurement_param(1) -> 01
        add_measurement_param(2) -> 0011
                                    0101
        add_measurement_param(3) -> 00001111
                                    00110011
                                    abababab
        """
        param = listify(param)
        l = None
        for k, v in self.measurement_params.items():
            l = len(v)
            self.measurement_params[k] = np.repeat(v, len(param))
        if l: param = np.tile(param, l)
        self.measurement_params[name] = param
        return param

    def prepend_measurement_param(self, name, param):
        """ Prepends measurement paramaters as
        1: 01
        2: 01
        3: ab

        prepend_measurement_param(1) -> 01
        prepend_measurement_param(2) -> 0011
                                        0101
        prepend_measurement_param(3) -> aaaabbbb
                                        00110011
                                        01010101
        """
        param = listify(param)
        l = None
        for k, v in self.measurement_params.items():
            l = len(v)
            self.measurement_params[k] = np.tile(v, len(param))
        if l: param = np.repeat(param, l)
        self.measurement_params[name] = param
        return param

    def _open_file(self):
        """Creates a new file (netCDF4 (*.hdf5)) in the storage directory.
        Copies config file to storage directory.
        """
        self.startingtime = time.time()
        fname = '{}{}_{}_{}'.format(
            self.storage_dir,
            time.strftime("%y%m%d%H%M", time.localtime(self.startingtime)),
            self.sample,
            self.name)
        # Store configuration file
        with open(self.configfile, 'r') as ymlfile:
            config = yaml.load(ymlfile)
        with open(fname + '.yml', 'w') as outfile:
            yaml.dump(config, outfile)
        # Open a new datafile
        self.dataset = Dataset(fname + '.hdf5', 'w', format='NETCDF4')
        self.dataset.sample = config[self.name]['general']['sample']
        self.dataset.comments = config[self.name]['general']['comments']
        self.dataset.experiment = self.name
        self.dataset.creationdate = time.asctime(time.localtime(self.startingtime))
        self.dataset.xnum = config[self.name]['xystage']['xnum']
        self.dataset.ynum = config[self.name]['xystage']['ynum']

        self.dataset.createDimension('xy_position', 2)

    @timed
    def _write_file(self):
        x = self.measurement_params['x'][self.measurement_index]
        y = self.measurement_params['y'][self.measurement_index]
        x_inx = list(np.unique(self.measurement_params['x'])).index(x)
        y_inx = list(np.unique(self.measurement_params['y'])).index(y)
        g = self.dataset.createGroup('x{:03}y{:03}'.format(x_inx, y_inx))
        try:
            xy_pos = g['position']
        except IndexError:
            xy_pos = g.createVariable('position', 'f8', 'xy_position',
                                      fill_value=np.nan)
            xy_pos.units = 'mm'
        keep_trying = 5
        while keep_trying:
            failed = False
            try:
                xy_pos[:] = [self.xystage.x, self.xystage.y]
            except Exception:
                keep_trying -= 1
                failed = True
                logging.info('Getting position failed. Retrying {}'.format(keep_trying))
                logging.info('Reconnecting...')
                time.sleep(5 - keep_trying)
                self.xystage.reconnect()
            if not failed:
                logging.info('Position acquisition successful!')
                keep_trying = 0

        return g

    def _process_data(self):
        pass

    def _calculate_progress(self):
        """Calculates progress (in percent) and Estimated Completion Time.
        Uses the average of the preparation + measurement times

        Emits:
            progress (float): progress in percent
            ect (float): Estimated completion time as UNIX timestamp
        """
        progress = self.measurement_index / len(self.measurement_params['x'])
        ect = (time.time() + self.measurement_duration /
               (self.measurement_index + 1) *
               (len(self.measurement_params['x']) - (self.measurement_index + 1))
               )
        self.progress.emit(progress * 100)
        self.ect.emit(ect)
        logging.info('Progress: {} %'.format(progress * 100))
        logging.info('Completed at: {}'.format(time.ctime(ect)))

    @timed
    def _measure(self):
        pass

    @timed
    def _prepare(self):
        """Prepares for a measurement.

        Moves the XYStage to the next position.
        """
        try:
            x = self.measurement_params['x'][self.measurement_index]
            xp = self.measurement_params['x'][self.measurement_index-1]
            y = self.measurement_params['y'][self.measurement_index]
            yp = self.measurement_params['y'][self.measurement_index-1]
            # Only issue a move when neccesary
            if not (x == xp and y == yp and self.measurement_index > 0):
                t = time.time()
                self.xystage.move(x, y)
                logging.info('Movement took {} s to complete'.format(time.time() - t))
        except IndexError:
            raise IndexError


class TransmissionExperiment(Experiment):
    """ Experiment class to measure transmissions of thin films
    """
    def __init__(self):
        super().__init__(name='Transmission')
        # Some measurement data that can't be read out in storing step
        self.processedspectrum = None

        ## Devices
        self.spectrometer = QSpectrometer()
        self.instruments.append(self.spectrometer)

    def _process_data(self):
        """Process the data, if necessary, through interpolation"""
        self.processedspectrum = np.interp(self.emission_wavelengths,
                                           self.spectrometer.wavelengths,
                                           self.processedspectrum)

    def _parse_config(self):
        super()._parse_config()
        with open(self.configfile, 'r') as ymlfile:
            config = yaml.load(ymlfile)
        config = config[self.name]
        smconfig = config['spectrometer']
        self.spectrometer.integrationtime = smconfig['integrationtime']
        self.spectrometer.average_measurements = smconfig['average_measurements']
        self.spectrometer.correct_dark_counts = smconfig['correct_dark_counts']
        self.spectrometer.correct_nonlinearity = smconfig['correct_nonlinearity']
        self.emission_wavelengths = smconfig['emission_wavelengths']
        if smconfig['all_wavelengths']:
            self.emission_wavelengths = self.spectrometer.wavelengths

    def _open_file(self):
        super()._open_file()
        # Diagnostic info
        self.dataset.createGroup('spectrometer')
        self.dataset['spectrometer'].integrationtime = self.spectrometer.integrationtime
        self.dataset['spectrometer'].average_measurements = self.spectrometer.average_measurements

        self.dataset.createDimension('emission_wavelengths', len(
            self.emission_wavelengths))
        self.dataset.createDimension('spectrometer_intervals',
                                     self.spectrometer.average_measurements * 2)
        self.dataset.createDimension('excitation_wavelengths', 1)

    @timed
    def _write_file(self):
        g = super()._write_file()

        try:
            em_wl = g['emission']
            spectrum = g['spectrum']
            spectrum_t = g['spectrum_t']
        except IndexError:
            em_wl = g.createVariable('emission', 'f8', 'emission_wavelengths',
                                     fill_value=np.nan)
            em_wl.units = 'nm'
            spectrum = g.createVariable('spectrum', 'f8',
                                        ('excitation_wavelengths', 'emission_wavelengths'),
                                        fill_value=np.nan)
            spectrum.units = 'a.u.'
            spectrum_t = g.createVariable('spectrum_t', 'f8',
                                          ('excitation_wavelengths',
                                           'spectrometer_intervals'),
                                          fill_value=np.nan)
            spectrum_t.units = 's'

        inx = 0
        em_wl[:] = self.emission_wavelengths
        spectrum[inx, :] = self.processedspectrum
        spectrum_t[inx, :] = np.array(self.spectrometertimes) - self.startingtime

    @timed
    def _prepare(self):
        super()._prepare()

    @timed
    def _measure(self):
        # Measure with spectrometer
        logging.info('Measuring...')
        with wait_for_signal(self.spectrometer.measurement_complete):
            logging.info('Starting spectrometer...')
            QTimer.singleShot(0, self.spectrometer.measure)
        logging.info('Spectrometer complete.')

        logging.info('Reading out measurement data...')
        self.processedspectrum = self.spectrometer.last_intensity
        self.spectrometertimes = self.spectrometer.last_times
