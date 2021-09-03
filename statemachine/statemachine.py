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
from instruments.Thorlabs.shuttercontrollers import QShutterControl
from instruments.Thorlabs.powermeters import QPowermeter
from instruments.Ekspla import QLaser
from instruments.CAEN.Qdigitizer import QDigitizer
from pathlib import Path
from netCDF4 import Dataset

logging.basicConfig(level=logging.INFO)

instrument_parser = {
    'xystage': QXYStage,
    'spectrometer': QSpectrometer,
    'shuttercontrol': QShutterControl,
    'powermeter': QPowermeter,
    'laser': QLaser,
    'digitzer': QDigitizer
}


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

    signalstatechange = pyqtSignal(str)         # signal that emits the state
    progress = pyqtSignal(int)                  # signal emitting the progress of the measurement
    ect = pyqtSignal(int)                       # estimated completion time
    connecting_done = pyqtSignal()              # done connecting to all instruments
    signal_return_setexperiment = pyqtSignal()  # signal for returning gui to set experiment state
    save_configuration = pyqtSignal()           # signal to start saving the current instrument config
    state = pyqtSignal(str)                     # signal emitting current statemachine state

    def __init__(self, parent=None):
        super().__init__()
        pathstateconfig = Path(__file__).parent / 'config_statemachine.yaml'
        with pathstateconfig.open() as f:
            self.stateconfig = yaml_safe_load(f)
        self.stateconfig['model'] = self
        self.machine = Machine(**self.stateconfig)
        pathconfig = Path(__file__).parent.parent / 'config_main.yaml'
        with pathconfig.open() as f:
            self.config = yaml_safe_load(f)
        self.experiment = None
        self.settings_ui = None
        self.instruments = {}
        self.measurement_parameters = {}
        self.timeout = 60
        self._reset_experiment()
        self._init_poll()
        self._init_xystages()

    def _reset_experiment(self):
        self.measurement_duration = 0
        self.measurement_index = 0
        self.laserstable = True
        self.processedspectrum = None
        self.spectrometertimes = None
        self.experimentdate = None
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
            self.xmax = 85
            self.ymax = 150

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
        self._connect_signals_instruments()

    def _connect_all(self):
        for inst in self.instruments.keys():
            if self.instruments[inst].connected:
                logging.info(f'{inst} already connected')
            else:
                logging.info(f'connecting {inst}')
                self.instruments[inst].connect()
                self.instruments[inst].timeout = self.timeout

    def disconnect_all(self):
        for inst in self.instruments.keys():
            logging.info(f'disconnecting {inst}')
            self.instruments[inst].disconnect()

    def _connect_signals_instruments(self):
        self.heartbeat_xystage.timeout.connect(self.instruments['xystage'].settled)
        self.instruments['xystage'].stage_settled.connect(self.measure)
        if 'spectrometer' in self.instruments.keys():
            self.instruments['spectrometer'].measurement_done.connect(self.process_data)

    def _align(self):
        self.heartbeat.start()

    def _stop_align(self):
        self.heartbeat.stop()
        # wait till laser is done measuring
        time.sleep(0.3)
        if self.experiment in ['excitation_emission', 'decay']:
            self.instruments['shuttercontrol'].disable()
            self.instruments['laser'].energylevel = 'Off'

    def _measure_instruments(self):
        for inst in self.instruments.keys():
            if not self.instruments[inst].measuring:
                QTimer.singleShot(0, self.instruments[inst].measure)

    # region parse config

    def _parse_config(self):
        # read in the ui settings
        path_settings = Path(__file__).parent.parent / 'settings_ui.yaml'
        with path_settings.open() as f:
            self.settings_ui = yaml_safe_load(f)
        # pick parsing routine
        if self.experiment == 'transmission':
            self._parse_config_transmission()
        elif self.experiment == 'excitation_emission':
            self._parse_config_excitation_emission()
        elif self.experiment == 'decay':
            self._parse_config_decay()

        self.start_experiment()

    def _parse_config_transmission(self):
        self._parse_xypositions()
        self._add_dark_measurement()
        self._add_lamp_measurement()
        self._parse_spectrometersettings()

    def _parse_config_excitation_emission(self):
        self._parse_xypositions()
        self._parse_excitation_wavelengths()
        self._add_dark_measurement()
        self._parse_spectrometersettings()
        self._parse_powermetersettings()
        self._parse_lasersettings()

    def _parse_xypositions(self):

        substratenum = self.settings_ui[self.experiment][f'widget_file_{self.experiment}']['comboBox_substrate']
        substrate = self.config['substrates'][substratenum]
        xysettings = self.settings_ui[self.experiment][f'widget_xystage_{self.experiment}']
        x_num = xysettings['spinBox_x_num']
        x_off_left = xysettings['spinBox_x_off_left']
        x_off_right = xysettings['spinBox_x_off_right']
        x_start = substrate[f'x_start_{self.experiment}']
        width_sample = substrate['whse']
        width_sample_usable = substrate['ws']
        x = self._define_positions(x_num, x_off_left, x_off_right, x_start, width_sample, width_sample_usable)
        y_num = xysettings['spinBox_y_num']
        y_off_bottom = xysettings['spinBox_y_off_bottom']
        y_off_top = xysettings['spinBox_y_off_top']
        y_start = substrate[f'y_start_{self.experiment}']
        height_sample = substrate['hhse']
        height_sample_usable = substrate['hs']
        y = self._define_positions(y_num, y_off_bottom, y_off_top, y_start, height_sample, height_sample_usable)
        self.measurement_parameters = {}
        self._add_measurement_parameter('x', x)
        self._add_measurement_parameter('y', y)

    def _parse_excitation_wavelengths(self):
        lasersettings = self.settings_ui[self.experiment][f'widget_laser_{self.experiment}']
        wl_start = lasersettings['spinBox_wavelength_start']
        wl_step = lasersettings['spinBox_wavelength_step']
        wl_stop = lasersettings['spinBox_wavelength_stop'] + 1
        wavelengths = np.arange(wl_start, wl_stop, wl_step)
        self._add_measurement_parameter('wl', wavelengths)

    def _add_measurement_parameter(self, name, parameter):
        length = None
        for keys, values in self.measurement_parameters.items():
            length = len(values)
            self.measurement_parameters[keys] = np.repeat(values, len(parameter))
        if length:
            parameter = np.tile(parameter, length)
        self.measurement_parameters[name] = parameter
        return parameter

    def _add_dark_measurement(self):
        # adds location to take a dark spectrum
        dark_lamp_x = np.array(20)
        dark_lamp_y = np.array(80)
        self.measurement_parameters['x'] = np.hstack((dark_lamp_x, self.measurement_parameters['x']))
        self.measurement_parameters['y'] = np.hstack((dark_lamp_y, self.measurement_parameters['y']))
        if 'wl' in self.measurement_parameters.keys():
            self.measurement_parameters['wl'] = np.hstack((300, self.measurement_parameters['wl']))

    def _add_lamp_measurement(self):
        # adds location to take a dark spectrum
        dark_lamp_x = np.array(0)
        dark_lamp_y = np.array(0)
        self.measurement_parameters['x'] = np.hstack((dark_lamp_x, self.measurement_parameters['x']))
        self.measurement_parameters['y'] = np.hstack((dark_lamp_y, self.measurement_parameters['y']))

    def _parse_spectrometersettings(self):
        # spectrometer settings
        smsettings = self.settings_ui[self.experiment][f'widget_spectrometer_{self.experiment}']
        self.instruments['spectrometer'].integrationtime = smsettings['spinBox_integration_time_experiment']
        self.instruments['spectrometer'].average_measurements = smsettings['spinBox_averageing_experiment']
        self.instruments['spectrometer'].clear_dark()
        self.instruments['spectrometer'].clear_lamp()

    def _parse_powermetersettings(self):
        # spectrometer settings
        smsettings = self.settings_ui[self.experiment][f'widget_powermeter_{self.experiment}']
        self.instruments['powermeter'].integrationtime = smsettings['spinBox_integration_time_experiment']

    def _parse_lasersettings(self):
        lasersettings = self.settings_ui[self.experiment][f'widget_laser_{self.experiment}']
        laserparse = self.config['laser'][lasersettings['comboBox_energy_level_experiment']]
        self.instruments['laser'].output = True
        self.instruments['laser'].energylevel = laserparse

    @staticmethod
    def _define_positions(num, off1, off2, start, sse, ss):
        # sse is sample size including edge of sample hodler, ss is visible part only
        bw = 3.5
        off1_mm = (ss - bw) * off1 / (100 + off2)
        off2_mm = (ss - bw) * off2 / (100 + off1)
        positions = [(sse + off1_mm - off2_mm) / 2 + start]
        positions = np.linspace((sse - ss + bw) / 2 + off1_mm + start,
                                sse - (sse - ss + bw) / 2 - off2_mm + start, num) if num > 1 else positions
        return positions

    #endregion

    #region open file

    def _open_file(self):
        # pick open file process
        if self.experiment == 'transmission':
            self._open_file_transmission()
        elif self.experiment == 'excitation_emission':
            self._open_file_excitation_emission()
        elif self.experiment == 'decay':
            self._open_file_decay()
        try:
            self.prepare()
        except Exception as e:
            self.abort()
        # new state

    def _open_file_transmission(self):
        self._load_create_file()
        self._write_positionsettings()
        self._write_spectrometersettings()
        self._create_dimensions()

    def _open_file_excitation_emission(self):
        self._load_create_file()
        self._write_positionsettings()
        self._write_lasersettings()
        self._write_powermetersettings()
        self._write_spectrometersettings()
        self._create_dimensions()

    def _load_create_file(self):
        # reads the storage directory and sample name from the settings, creates a file and directory
        filesettings = self.settings_ui[self.experiment][f'widget_file_{self.experiment}']
        storage_dir = filesettings['lineEdit_directory']
        sample = filesettings['lineEdit_sample']
        fname = f'{storage_dir}/{sample}'
        append = filesettings['checkBox_append_file']
        fname_append = str(filesettings['lineEdit_append_file'])
        comment = filesettings['plainTextEdit_comments']

        # check if append option was checked, append to selected file if so
        if append:
            self.dataset = Dataset(f'{fname_append}', 'a', format='NETCDF4')
        else:
            # open a new datafile
            self.dataset = Dataset(f'{fname}.hdf5', 'w', format='NETCDF4')

        self.startingtime = time.time()
        self.experimentdate = time.strftime("%y%m%d%H%M", time.localtime(self.startingtime))
        experiment = self.dataset.createGroup(f'{self.experiment}_{self.experimentdate}')
        # include comment on experiment
        experiment.comment = comment

        # Store configuration file
        # with pathconfig.open('r') as f:
        #     settings = yaml_safe_load(f)
        # with open(f'{fname}.yml', 'w') as outfile:
        #     yaml_dump(settings, outfile)

    def _write_positionsettings(self):
        positionsettings = self.dataset.createGroup(f'{self.experiment}_{self.experimentdate}/settings/xystage')
        # exclude positions of dark and lamp spectra where applicable.
        paramdict = {'transmission': 2, 'excitation_emission': 1, 'decay': 1}
        positionsettings.xnum = len(np.unique(self.measurement_parameters['x'][paramdict[self.experiment]:]))
        positionsettings.ynum = len(np.unique(self.measurement_parameters['y'][paramdict[self.experiment]:]))

    def _write_spectrometersettings(self):
        spectrometersettings = self.dataset.createGroup(f'{self.experiment}_{self.experimentdate}/settings/spectrometer')
        spectrometersettings.integrationtime = self.instruments['spectrometer'].integrationtime
        spectrometersettings.average_measurements = self.instruments['spectrometer'].average_measurements
        spectrometersettings.spectrometer = self.instruments['spectrometer'].name

    def _write_lasersettings(self):
        lasersettings = self.dataset.createGroup(f'{self.experiment}_{self.experimentdate}/settings/laser')
        lasersettings.energylevel = self.instruments['laser'].energylevel
        lasersettings.wlnum = len(np.unique(self.measurement_parameters['wl']))

    def _write_powermetersettings(self):
        pmsettings = self.dataset.createGroup(f'{self.experiment}_{self.experimentdate}/settings/powermeter')
        pmsettings.integrationtime = self.instruments['powermeter'].integrationtime

    def _create_dimensions(self):
        if self.experiment in ['transmission', 'excitation_emission']:
            self.dataset[f'{self.experiment}_{self.experimentdate}'].createDimension('xy_position', 2)
            self.dataset[f'{self.experiment}_{self.experimentdate}'].createDimension('emission_wavelengths',
                                                               len(self.instruments['spectrometer'].wavelengths))
            self.dataset[f'{self.experiment}_{self.experimentdate}'].createDimension('spectrometer_intervals',
                                                    self.instruments['spectrometer'].average_measurements * 2)
            self.dataset[f'{self.experiment}_{self.experimentdate}'].createDimension('single', 1)
        if self.experiment == 'excitation_emission':
            excitation_wavelenghts = len(np.unique(self.measurement_parameters['wl'][1:]))
            self.dataset[f'{self.experiment}_{self.experimentdate}'].createDimension('excitation_wavelengths',
                                                                                     excitation_wavelenghts)

    #endregion

    #region prepare measurement

    def _prepare_measurement(self):
        if self.experiment == 'transmission':
            self._prepare_measurement_transmission()
        elif self.experiment == 'excitation_emission':
            self._prepare_measurement_excitation_emission()
        elif self.experiment == 'decay':
            self._prepare_measurement_decay()

    def _prepare_measurement_transmission(self):
        self._prepare_move_stage()

    def _prepare_measurement_excitation_emission(self):
        self._prepare_move_stage()
        self._control_shutter()
        self._prepare_laser()

    def _prepare_move_stage(self):
        try:
            global tstartmove
            tstartmove = time.time()
            x = self.measurement_parameters['x'][self.measurement_index]
            y = self.measurement_parameters['y'][self.measurement_index]
            self.instruments['xystage'].move(x, y)
            time.sleep(0.2)
            self.heartbeat_xystage.start()
            # logging.info('Movement took {} s to complete'.format(time.time() - t))
        except IndexError:
            raise IndexError

    def _control_shutter(self):
        if self.measurement_index == 0:
            self.instruments['shuttercontrol'].disable()
        else:
            self.instruments['shuttercontrol'].enable()

    def _prepare_laser(self):
        self.laserstable = False
        self.instruments['laser'].wavelength = self.measurement_parameters['wl'][self.measurement_index]
        # shit to check if power stable
        time.sleep(1)
        self.laserstable = True
        logging.info('laser power stable')

    #endregion

    #region measure

    @timed
    def _measure(self):
        if self.experiment == 'transmission':
            self._measure_transmission()
        elif self.experiment == 'excitation_emission':
            self._measure_excitation_emission()
        elif self.experiment == 'decay':
            self._measure_decay()

    def _measure_transmission(self):
        self.heartbeat_xystage.stop()
        self.measurement_duration += time.time() - tstartmove
        # wait one integration time to make sure measurement is fully done on sample
        self._measure_spectrometer()

    def _measure_excitation_emission(self):
        self.heartbeat_xystage.stop()
        while not self.laserstable:
            time.sleep(0.1)
        self.measurement_duration += time.time() - tstartmove
        # wait one integration time to make sure measurement is fully done on sample
        self._measure_spectrometer()

    def _measure_spectrometer(self):
        # Measure with spectrometer
        logging.info('Measuring...')
        with wait_for_signal(self.instruments['spectrometer'].measurement_complete):
            logging.info('Starting spectrometer...')
            QTimer.singleShot(0, self.instruments['spectrometer'].measure)
        logging.info('Spectrometer complete.')
        logging.info('Reading out measurement data...')
        self.processedspectrum = self.instruments['spectrometer'].last_intensity
        self.spectrometertimes = self.instruments['spectrometer'].last_times

    #endregion

    #region process data
    def _process_data(self):
        self.write_file()
        pass
    #endregion

    # region write file

    @timed
    def _write_file(self):
        if self.experiment == 'transmission':
            self._write_file_transmission()
        elif self.experiment == 'excitation_emission':
            self._write_file_excitation_emission()
        elif self.experiment == 'decay':
            self._write_file_decay()

        self.measurement_index += 1
        self.calculate_progress()

    def _write_file_transmission(self):
        # make folders for each measurement position, includes dark folder and lamp folder
        # transmission has only one measurement per position so folders need to be created always
        if self.measurement_index == 0:
            datagroup = self.dataset.createGroup(f'{self.experiment}_{self.experimentdate}/dark')
        elif self.measurement_index == 1:
            datagroup = self.dataset.createGroup(f'{self.experiment}_{self.experimentdate}/lamp')
        else:
            x_inx, y_iny = self._variable_index()
            datagroup = self.dataset.createGroup(f'{self.experiment}_{self.experimentdate}/x{x_inx + 1}y{y_iny + 1}')

        xy_pos, em_wl, spectrum, spectrum_t = self._create_variables(datagroup)

        xy_pos[:] = self._write_position()
        em_wl[:] = self.instruments['spectrometer'].wavelengths
        spectrum[:] = self.processedspectrum
        spectrum_t[:] = np.array(self.spectrometertimes) - self.startingtime

    def _write_file_excitation_emission(self):
        # make folders for each measurement position, includes dark folder for dark measurement
        global wl_in_wl

        if self.measurement_index == 0:
            datagroup = self.dataset.createGroup(f'{self.experiment}_{self.experimentdate}/dark')
        else:
            x_inx, y_iny, wl_in_wl = self._variable_index()
            # check if folder with position index exists, otherwise create it
            try:
                datagroup = self.dataset[f'{self.experiment}_{self.experimentdate}/x{x_inx + 1}y{y_iny + 1}']
            except IndexError:
                datagroup = self.dataset.createGroup(f'{self.experiment}_{self.experimentdate}/x{x_inx + 1}y{y_iny + 1}')
        try:
            xy_pos = datagroup['position']
            em_wl = datagroup['emission']
            spectrum = datagroup['spectrum']
            spectrum_t = datagroup['spectrum_t']
            ex_wl = datagroup['excitation']
            power = datagroup['power']
        except IndexError:
            xy_pos, em_wl, spectrum, spectrum_t, ex_wl, power = self._create_variables(datagroup)

        if self.measurement_index == 0:
            em_wl[:] = self.instruments['spectrometer'].wavelengths
            spectrum[:] = self.processedspectrum
            spectrum_t[:] = np.array(self.spectrometertimes) - self.startingtime
            xy_pos[:] = self._write_position()
            ex_wl[:] = self.instruments['laser'].wavelength
            power[:] = self.instruments['powermeter'].measure()
        else:
            em_wl[:] = self.instruments['spectrometer'].wavelengths
            spectrum[wl_in_wl, :] = self.processedspectrum
            spectrum_t[wl_in_wl, :] = np.array(self.spectrometertimes) - self.startingtime
            xy_pos[:] = self._write_position()
            ex_wl[wl_in_wl] = self.instruments['laser'].wavelength
            power[wl_in_wl] = self.instruments['powermeter'].measure()

    def _variable_index(self):
        # creates an index for the variables for the folder name per measurement position and for indexing the
        # spectra per excitation wavelength
        x = self.measurement_parameters['x'][self.measurement_index]
        y = self.measurement_parameters['y'][self.measurement_index]
        # exclude positions of dark and lamp spectra where applicable.
        paramdict = {'transmission': 2, 'excitation_emission': 1, 'decay': 1}
        x_inx = list(np.unique(self.measurement_parameters['x'][paramdict[self.experiment]:])).index(x)
        y_iny = list(np.unique(self.measurement_parameters['y'][paramdict[self.experiment]:])).index(y)
        if self.experiment in ['excitation_emission', 'decay']:
            wl = self.measurement_parameters['wl'][self.measurement_index]
            wl_in_wls = list(np.unique(self.measurement_parameters['wl'][paramdict[self.experiment]:])).index(wl)
            return x_inx, y_iny, wl_in_wls
        else:
            return x_inx, y_iny

    def _create_variables(self, datagroup):
        xy_pos = datagroup.createVariable('position', 'f8', 'xy_position', fill_value=np.nan)
        xy_pos.units = 'mm'
        em_wl = datagroup.createVariable('emission', 'f8', 'emission_wavelengths', fill_value=np.nan)
        em_wl.units = 'nm'
        if self.experiment == 'transmission':
            spectrum = datagroup.createVariable('spectrum', 'f8', 'emission_wavelengths', fill_value=np.nan)
            spectrum_t = datagroup.createVariable('spectrum_t', 'f8', 'spectrometer_intervals', fill_value=np.nan)
            spectrum.units = 'a.u.'
            spectrum_t.units = 's'
            return xy_pos, em_wl, spectrum, spectrum_t
        elif self.experiment == 'excitation_emission' and self.measurement_index == 0:
            spectrum = datagroup.createVariable('spectrum', 'f8', 'emission_wavelengths', fill_value=np.nan)
            spectrum_t = datagroup.createVariable('spectrum_t', 'f8', 'spectrometer_intervals', fill_value=np.nan)
            ex_wl = datagroup.createVariable('excitation', 'f8', 'single', fill_value=np.nan)
            power = datagroup.createVariable('power', 'f8', 'single', fill_value=np.nan)
            spectrum.units = 'a.u.'
            spectrum_t.units = 's'
            ex_wl.units = 'nm'
            power.units = 'W'
            return xy_pos, em_wl, spectrum, spectrum_t, ex_wl, power
        elif self.experiment == 'excitation_emission':
            spectrum = datagroup.createVariable('spectrum', 'f8', ('excitation_wavelengths',
                                                                   'emission_wavelengths'), fill_value=np.nan)
            spectrum_t = datagroup.createVariable('spectrum_t', 'f8', ('excitation_wavelengths',
                                                                       'spectrometer_intervals'), fill_value=np.nan)
            ex_wl = datagroup.createVariable('excitation', 'f8', 'excitation_wavelengths', fill_value=np.nan)
            power = datagroup.createVariable('power', 'f8', 'excitation_wavelengths', fill_value=np.nan)
            spectrum.units = 'a.u.'
            spectrum_t.units = 's'
            ex_wl.units = 'nm'
            power.units = 'W'
            return xy_pos, em_wl, spectrum, spectrum_t, ex_wl, power

    def _write_position(self):
        # ugly and probably unnescessary way of getting the position, need to check if this actually happens
        keep_trying = 5
        while keep_trying:
            failed = False
            try:
                x, y = [self.instruments['xystage'].x, self.instruments['xystage'].y]
                return x, y
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

    # endregion

    # region calculate progress

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
        self.ect.emit(int(ect))
        self.progress.emit(int(progress * 100))
        logging.info('Progress: {} %'.format(progress * 100))
        logging.info('Completed at: {}'.format(time.ctime(ect)))
        if progress == 1:
            self.is_done = True
            self.measurement_complete()
        else:
            self.prepare()
    # endregion

    def _return_setexperiment(self):
        self.signal_return_setexperiment.emit()

    def _measurement_aborted(self):
        self.instruments['xystage'].stop_motors()
        self.dataset.close()
        self.is_done = True
        self.continue_experiment()
        self.return_setexperiment()
        pass

    def _measurement_completed(self):
        self.dataset.close()
        self.is_done = True
        self.continue_experiment()
        self.return_setexperiment()
        pass

