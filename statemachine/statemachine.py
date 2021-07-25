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
        self.experiment = None
        self.instruments = {}
        self.measurement_parameters = {}
        self.timeout = 60
        self._reset_experiment()
        self._init_poll()
        self._init_xystages()

    def _reset_experiment(self):
        self.measurement_duration = 0
        self.measurement_index = 0
        self.processedspectrum = None
        self.spectrometertimes = None
        self.is_done = False
        self.storage_dir = None
        self.startingtime = time.time()

    def _init_poll(self):
        self.polltime = 0.2
        self.heartbeat = QTimer()
        self.heartbeat.setInterval(int(self.polltime * 1000))
        self.heartbeat.timeout.connect(self._measure_instruments)
        self.heartbeat_xystage = QTimer()
        self.heartbeat_xystage.setInterval(int(self.polltime * 1000))

    def _init_xystages(self):
        self.xstage_serial = None
        self.ystage_serial = None
        self.xmax = None
        self.ymax = None

    def _from_state(self, *args):
        self.signalstatechange.emit(f'from state {self.state}')

    def _in_state(self, *args):
        self.signalstatechange.emit(f'finished in state {self.state}')

    def _start(self):
        serial = apt.list_available_devices()[0][1]
        if serial in [67844567, 67844568]:
            self.xstage_serial = 67844568
            self.ystage_serial = 67844567
            self.xmax = 100
            self.ymax = 100
        else:
            self.xstage_serial = 45951910
            self.ystage_serial = 45962470
            self.xmax = 100
            self.ymax = 100

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
            if inst == 'xystage':
                self.instruments[inst].xstage_serial = self.xstage_serial
                self.instruments[inst].ystage_serial = self.ystage_serial
                self.instruments[inst].xmax = self.xmax
                self.instruments[inst].ymax = self.ymax
        self.connect_all()
        self._init_triggers()

    def _init_triggers(self):
        self.heartbeat_xystage.timeout.connect(self.instruments['xystage'].settled)
        self.instruments['xystage'].stage_settled.connect(self.measure)
        self.instruments['spectrometer'].measurement_done.connect(self.process_data)

    def _parse_config(self):
        path_settings = Path.home() / 'PycharmProjects/XY_New/settings_ui.yaml'
        with path_settings.open() as f:
            settings = yaml_safe_load(f)
        substratenum = settings[self.experiment][f'widget_file_{self.experiment}']['comboBox_substrate']
        substrate = self.config['substrates'][substratenum]
        xysettings = settings[self.experiment][f'widget_xystage_{self.experiment}']
        x_num = xysettings['spinBox_x_num']
        x_off_left = xysettings['spinBox_x_off_left']
        x_off_right = xysettings['spinBox_x_off_right']
        x_start = substrate['x_start']
        width_sample = substrate['whse']
        width_sample_usable = substrate['ws']
        x = self._define_positions(x_num, x_off_left, x_off_right, x_start, width_sample, width_sample_usable)
        y_num = xysettings['spinBox_y_num']
        y_off_bottom = xysettings['spinBox_y_off_bottom']
        y_off_top = xysettings['spinBox_y_off_top']
        y_start = substrate['y_start']
        height_sample = substrate['hhse']
        height_sample_usable = substrate['hs']
        y = self._define_positions(y_num, y_off_bottom, y_off_top, y_start, height_sample, height_sample_usable)
        self.measurement_parameters = {}
        self._add_measurement_parameter('x', x)
        self._add_measurement_parameter('y', y)
        dark_lamp_x = np.array((20, 0))
        dark_lamp_y = np.array((80, 0))
        self.measurement_parameters['x'] = np.hstack((dark_lamp_x, self.measurement_parameters['x']))
        self.measurement_parameters['y'] = np.hstack((dark_lamp_y, self.measurement_parameters['y'])) 

        # spectrometer settings
        smsettings = settings[self.experiment][f'widget_spectrometer_{self.experiment}']
        self.instruments['spectrometer'].integrationtime = smsettings['spinBox_integration_time_experiment']
        self.instruments['spectrometer'].average_measurements = smsettings['spinBox_averageing_experiment']
        self.instruments['spectrometer'].clear_dark()
        self.instruments['spectrometer'].clear_lamp()

    def _add_measurement_parameter(self, name, parameter):
        length = None
        for keys, values in self.measurement_parameters.items():
            length = len(values)
            self. measurement_parameters[keys] = np.repeat(values, len(parameter))
        if length:
            parameter = np.tile(parameter, length)
        self.measurement_parameters[name] = parameter
        return parameter

    def _define_positions(self, num, off1, off2, start, sse, ss):
        # sse is sample size including edge of sample hodler, ss is visible part only
        bw = 3.5
        off1_mm = (ss - bw) * off1 / (100 + off2)
        off2_mm = (ss - bw) * off2 / (100 + off1)
        positions = [(sse + off1_mm - off2_mm) / 2 + start]
        positions = np.linspace((sse - ss + bw) / 2 + off1_mm + start,
                                sse - (sse - ss + bw) / 2 - off2_mm + start, num) if num > 1 else positions
        return positions

    def _connect_all(self):
        for inst in self.instruments.keys():
            if self.instruments[inst].connected:
                logging.info(f'{inst} already connected')
            else:
                logging.info(f'{inst} connecting')
                self.instruments[inst].connect()
                self.instruments[inst].timeout = self.timeout

    def disconnect_all(self):
        for inst in self.instruments.keys():
            self.instruments[inst].disconnect()

    def _align(self):
        self.heartbeat.start()

    def _stop_align(self):
        self.heartbeat.stop()

    def _measure_instruments(self):
        for inst in self.instruments.keys():
            if not self.instruments[inst].measuring:
                QTimer.singleShot(0, self.instruments[inst].measure)

    def run_experiment(self):
        self.init_experiment()
        self.start_experiment()
        try:
            self.prepare()
        except Exception as e:
            self.abort()
            raise e

    def _open_file(self):
        """Creates a new file (netCDF4 (*.hdf5)) in the storage directory.
        Copies config file to storage directory.
        """
        # Load directory
        pathconfig = Path.home() / 'PycharmProjects/XY_New/settings_ui.yaml'
        with pathconfig.open('r') as f:
            settings = yaml_safe_load(f)
        storage_dir = settings[self.experiment][f'widget_file_{self.experiment}']['lineEdit_directory']
        sample = settings[self.experiment][f'widget_file_{self.experiment}']['lineEdit_sample']

        self.startingtime = time.time()
        fname = f'{storage_dir}/{time.strftime("%y%m%d%H%M", time.localtime(self.startingtime))}' \
                f'_{sample}'
        # Store configuration file
        with pathconfig.open('r') as f:
            settings = yaml_safe_load(f)
        with open(f'{fname}.yml', 'w') as outfile:
            yaml_dump(settings, outfile)
        # Open a new datafile
        self.dataset = Dataset(f'{fname}.hdf5', 'w', format='NETCDF4')
        positionsettings = self.dataset.createGroup(f'{self.experiment}/settings/xystage')
        positionsettings.xnum = len(np.unique(self.measurement_parameters['x'][2:]))
        positionsettings.ynum = len(np.unique(self.measurement_parameters['y'][2:]))
        spectrometersettings = self.dataset.createGroup(f'{self.experiment}/settings/spectrometer')
        spectrometersettings.integrationtime = self.instruments['spectrometer'].integrationtime
        spectrometersettings.average_measurements = self.instruments['spectrometer'].average_measurements
        self.dataset[f'{self.experiment}'].createDimension('xy_position', 2)
        self.dataset[f'{self.experiment}'].createDimension('emission_wavelengths', len(self.instruments['spectrometer'].wavelengths))
        self.dataset[f'{self.experiment}'].createDimension('spectrometer_intervals', self.instruments['spectrometer'].
                                     average_measurements * 2)
        self.dataset[f'{self.experiment}'].createDimension('excitation_wavelengths', 1)
        # new state

    @timed
    def _write_file(self):
        if self.measurement_index == 0:
            datagroup = self.dataset.createGroup(f'{self.experiment}/dark')
        elif self.measurement_index == 1:
            datagroup = self.dataset.createGroup(f'{self.experiment}/lamp')
        else:
            x = self.measurement_parameters['x'][self.measurement_index]
            y = self.measurement_parameters['y'][self.measurement_index]
            x_inx = list(np.unique(self.measurement_parameters['x'][2:])).index(x)
            y_iny = list(np.unique(self.measurement_parameters['y'][2:])).index(y)
            datagroup = self.dataset.createGroup(f'{self.experiment}/x{x_inx+1}y{y_iny+1}')
        try:
            xy_pos = datagroup['position']
            em_wl = datagroup['emission']
            spectrum = datagroup['spectrum']
            spectrum_t = datagroup['spectrum_t']
        except IndexError:
            xy_pos = datagroup.createVariable('position', 'f8', 'xy_position', fill_value=np.nan)
            xy_pos.units = 'mm'
            em_wl = datagroup.createVariable('emission', 'f8', 'emission_wavelengths', fill_value=np.nan)
            em_wl.units = 'nm'
            spectrum = datagroup.createVariable('spectrum', 'f8', ('excitation_wavelengths', 'emission_wavelengths'),
                                                fill_value=np.nan)
            spectrum.units = 'a.u.'
            spectrum_t = datagroup.createVariable('spectrum_t', 'f8', ('excitation_wavelengths',
                                                                       'spectrometer_intervals'), fill_value=np.nan)
            spectrum_t.units = 's'

        inx = 0
        em_wl[:] = self.instruments['spectrometer'].wavelengths
        spectrum[inx, :] = self.processedspectrum
        spectrum_t[inx, :] = np.array(self.spectrometertimes) - self.startingtime

        # ugly and probably unnescessary way of getting the position
        keep_trying = 5
        while keep_trying:
            failed = False
            try:
                xy_pos[:] = [self.instruments['xystage'].x, self.instruments['xystage'].y]
            except Exception:
                keep_trying -= 1
                failed = True
                logging.info('Getting position failed. Retrying {}'.format(keep_trying))
                logging.info('Reconnecting...')
                time.sleep(5 - keep_trying)
                self.instruments['xystage'].reconnect()
            if not failed:
                logging.info('Position acquisition successful!')
                keep_trying = 0

        self.measurement_index += 1
        self.calculate_progress()

    def _prepare_measurement(self):
        try:
            global tstartmove
            tstartmove = time.time()
            x = self.measurement_parameters['x'][self.measurement_index]
            y = self.measurement_parameters['y'][self.measurement_index]
            self.heartbeat_xystage.start()
            self.instruments['xystage'].move(x, y)
            # logging.info('Movement took {} s to complete'.format(time.time() - t))
        except IndexError:
            raise IndexError

    @timed
    def _measure(self):
        self.heartbeat_xystage.stop()
        self.measurement_duration += time.time() - tstartmove
        # Measure with spectrometer
        logging.info('Measuring...')
        with wait_for_signal(self.instruments['spectrometer'].measurement_complete):
            logging.info('Starting spectrometer...')
            QTimer.singleShot(0, self.instruments['spectrometer'].measure)
        logging.info('Spectrometer complete.')
        logging.info('Reading out measurement data...')
        self.processedspectrum = self.instruments['spectrometer'].last_intensity
        self.spectrometertimes = self.instruments['spectrometer'].last_times

    def _print_ready(self):
        print('movement is ready')

    def _process_data(self):
        self.write_file()
        pass

    def _calculate_progress(self):
        """Calculates progress (in percent) and Estimated Completion Time.
        Uses the average of the preparation + measurement times

        Emits:
            progress (float): progress in percent
            ect (float): Estimated completion time as UNIX timestamp
        """
        progress = self.measurement_index / len(self.measurement_parameters['x'])
        ect = (self.measurement_duration /
               self.measurement_index *
               (len(self.measurement_parameters['x']) - self.measurement_index)
               )
        self.progress.emit(progress * 100)
        self.ect.emit(ect)
        logging.info('Progress: {} %'.format(progress * 100))
        logging.info('Completed at: {}'.format(time.ctime(ect)))
        if progress == 1:
            self.is_done = True
            self.measurement_complete()
        else:
            self.prepare()

    def _load_configuration(self):
        pass

    def _save_configuration(self):
        pass

    def _return_setexperiment(self):
        self.signal_return_setexperiment.emit()

    def _measurement_aborted(self):
        self.instruments['xystage'].disable()
        self.dataset.close()
        self.is_done = True
        self.instruments['xystage'].enable()
        self.continue_experiment()
        self.return_setexperiment()
        pass

    def _measurement_completed(self):
        self.dataset.close()
        self.is_done = True
        self.continue_experiment()
        self.return_setexperiment()
        pass

