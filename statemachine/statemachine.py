from transitions.extensions import HierarchicalGraphMachine as Machine
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot, QEventLoop
import logging
import time
import numpy as np
import math
from yaml import safe_load as yaml_safe_load
from yaml import dump as yaml_dump
from instruments.OceanOptics.spectrometer import QSpectrometer
from instruments.Thorlabs import apt
from instruments.Thorlabs.xystage import QXYStage
from instruments.Thorlabs.shuttercontrollers import QShutterControl
from instruments.Thorlabs.qpowermeter import QPowerMeter
from instruments.Ekspla import QLaser
from instruments.CAEN.Qdigitizer import QDigitizer
from instruments.CAEN.definitions import TIMERANGES, COMPRESSIONFACTORS
from pathlib import Path
import multitimer
from netCDF4 import Dataset
import pandas as pd
from statemachine.multiple_signals import MultipleSignal

instrument_parser = {
    'xystage': QXYStage,
    'spectrometer': QSpectrometer,
    'shuttercontrol': QShutterControl,
    'powermeter': QPowerMeter,
    'laser': QLaser,
    'digitizer': QDigitizer
}


def timed(func):
    def wrapper(self, *args, **kwargs):
        t1 = time.time()
        result = func(self, *args, **kwargs)
        t2 = time.time()
        self.measurement_duration += t2 - t1
        return result

    return wrapper


class StateMachine(QObject):
    """
    State Machine for any Experiment

    Since this involves a State Machine, all methods are 'private'
    and should be accessed through this class' states
    """

    signalstatechange = pyqtSignal(str)  # signal that emits the state
    progress = pyqtSignal(int)  # signal emitting the progress of the measurement
    ect = pyqtSignal(int)  # estimated completion time
    connecting_done = pyqtSignal()  # done connecting to all instruments
    signal_return_setexperiment = pyqtSignal()  # signal for returning gui to set experiment state
    save_configuration = pyqtSignal()  # signal to start saving the current instrument config
    state = pyqtSignal(str)  # signal emitting current statemachine state
    calibration_half_signal = pyqtSignal()  # signal emitted halfway during beamsplitter calibration
    calibration_complete_signal = pyqtSignal()  # emitted when beamsplitter calibration complete
    calibration_status = pyqtSignal(str)  # status signal for the completion bar
    instrument_connect_successful = pyqtSignal()  # emits picked 'page' when all instruments are connected.
    instrument_connect_failed = pyqtSignal(dict)  # emitted when a connection error is raised at connecting instruments
    init_instrument_threads = pyqtSignal()
    enable_main_gui = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__()

        self.logger = logging.getLogger('statemachine')
        self.logger.info('init statemachine')
        pathstateconfig = Path(__file__).parent / 'config_statemachine.yaml'
        with pathstateconfig.open() as file:
            self.stateconfig = yaml_safe_load(file)
        self.stateconfig['model'] = self
        self.machine = Machine(**self.stateconfig)

        pathconfig = Path(__file__).parent.parent / 'config/config_main.yaml'
        with pathconfig.open() as f:
            self.config = yaml_safe_load(f)
        self.experiment = None
        self.calibration = False
        self.storage_dir_calibration = None
        self.beamsplitter = None
        self.calibration_fname = None
        self.settings_ui = None
        self.instruments = {}
        self.measurement_parameters = {}
        self.position_offsets = {}
        self.timekeeper = None
        self.timeout = 60
        self.wait_signals_prepare_measurement = None
        self.wait_signals_measurement = None
        self._reset_experiment()
        self._init_poll()

    def _reset_experiment(self):
        self.measurement_duration = 0
        self.measurement_index = 0
        self.laserstable = True
        self.processedspectrum = None
        self.spectrometertimes = None
        self.pulserecord = None
        self.experimentdate = None
        self.is_done = False
        self.storage_dir = None
        self.calibration_dataframe = None
        self.calibration_position = None
        self.startingtime = time.time()

    def _init_poll(self):
        """
        Initialze the timer that periodically polls the connected instruments.
        :return:
        """
        self.polltime = 0.2
        self.heartbeat = QTimer()
        self.heartbeat.setInterval(int(self.polltime * 1000))
        self.heartbeat.timeout.connect(self._measure_instruments)

    def _from_state(self, *args):
        self.signalstatechange.emit(f'from state {self.state}')

    def _in_state(self, *args):
        self.signalstatechange.emit(f'finished in state {self.state}')

    def _start(self):
        self.logger.info('Mysterious start function called')

    def _define_experiment(self, page):
        """ Check which instruments are needed for selected experiment, remove unnecessary instruments """
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
        self.connect_all(page)

    def _connect_all(self, page):
        """
        Connect all the instruments belonging to the experiment.

        If a connectionerror is raised in connecting any of the instruments, send a connection failed signal to the gui
        and send the connect_failed trigger.

        If all connections succesful, send a signal to the main gui to continue parsing the selected gui page.
        """
        for inst in self.instruments.keys():
            if self.instruments[inst].connected:
                self.logger.info(f'{inst} already connected')
            else:
                try:
                    self.logger.info(f'connecting {inst}')
                    self.instruments[inst].connect()
                    self.instruments[inst].timeout = self.timeout
                except ConnectionError as e:
                    self.logger.error(f'Failed to connect {inst}')
                    error = {'instrument': inst, 'error': e}
                    self.enable_main_gui.emit(False)
                    self.instrument_connect_failed.emit(error)
                    self.disconnect_all()
                    self.enable_main_gui.emit(True)
                    self.connect_failed()
                    return
        self.init_instrument_threads.emit()
        self.align()

    def _emit_init_gui(self):
        """
        Emits a signal to the main application to init the ui. This function is called by the statemachine after
        the transition from connecting to align state.
        """
        self.instrument_connect_successful.emit()

    def disconnect_all(self):
        """ Disconnect all the instruments belonging to the experiment, if they are connected. """
        for inst in self.instruments.keys():
            if not self.instruments[inst].connected:
                self.logger.info(f'{inst} already disconnected')
            else:
                self.logger.info(f'disconnecting {inst}')
                self.instruments[inst].disconnect()

    def _connect_signals_align(self):
        """ Connect instrument signals to each other for alignment. """
        if self.experiment == 'excitation_emission':
            self.logger.info('connecting laser wavelength to powermeter wavelength')
            self.instruments['laser'].wavelength_signal.connect(self.instruments['powermeter'].set_wavelength)
            # emit the wavelength by calling the property
            _ = self.instruments['laser'].wavelength

    def _disconnect_signals_align(self):
        """ Disconnect instrument signals from the align state. """
        if self.experiment == 'excitation_emission':
            self.logger.info('disconnecting laser wavelength to powermeter wavelength')
            self.instruments['laser'].wavelength_signal.disconnect(self.instruments['powermeter'].set_wavelength)

    def _connect_signals_experiment(self):
        """
        Connect the relevant instrument signals to statemachine triggers.
        """
        self.logger.info('Connecting instrument signals to statemachine triggers')
        if self.calibration:
            self.instruments['xystage'].stage_settled.connect(self.start_experiment)
            self.instruments['powermeter'].measurement_done.connect(self.process_data)
        elif self.experiment == 'transmission':
            self.instruments['xystage'].stage_settled.connect(self.measure)
            self.instruments['spectrometer'].measurement_done.connect(self.process_data)
        elif self.experiment == 'excitation_emission':
            self.wait_signals_prepare_measurement = MultipleSignal(name='prepare measurement',
                                                                   signals=['xystage', 'laser'])
            self.instruments['xystage'].stage_settled.connect(
                self.wait_signals_prepare_measurement.signals['xystage'].set_state)
            self.instruments['laser'].laser_stable.connect(
                self.wait_signals_prepare_measurement.signals['laser'].set_state)
            self.wait_signals_prepare_measurement.global_done.connect(self.measure)
            self.wait_signals_measurement = MultipleSignal(name='measurement',
                                                           signals=['spectrometer', 'powermeter'])
            self.instruments['spectrometer'].measurement_done.connect(
                self.wait_signals_measurement.signals['spectrometer'].set_state)
            self.instruments['powermeter'].measurement_done.connect(
                self.wait_signals_measurement.signals['powermeter'].set_state)
            self.wait_signals_measurement.global_done.connect(self.process_data)
        elif self.experiment == 'decay':
            self.wait_signals_prepare_measurement = MultipleSignal(name='prepare measurement',
                                                                   signals=['xystage', 'laser'])
            self.instruments['xystage'].stage_settled.connect(
                self.wait_signals_prepare_measurement.signals['xystage'].set_state)
            self.instruments['laser'].laser_stable.connect(
                self.wait_signals_prepare_measurement.signals['laser'].set_state)
            self.wait_signals_prepare_measurement.global_done.connect(self.measure)
            self.instruments['digitizer'].measurement_done.connect(self.process_data)

    def _disconnect_signals_experiment(self):
        """
        Disconnect the relevant signals from the instruments. Called when experiment or calibration is done.
        """
        self.logger.info('disconnecting instrument signals from statemachine triggers')
        if self.calibration:
            self.instruments['xystage'].stage_settled.disconnect(self.start_experiment)
            self.instruments['powermeter'].measurement_done.disconnect(self.process_data)
            self.calibration = False
        elif self.experiment == 'transmission':
            self.instruments['xystage'].stage_settled.disconnect(self.measure)
            self.instruments['spectrometer'].measurement_done.disconnect(self.process_data)
        elif self.experiment == 'excitation_emission':
            self.instruments['xystage'].stage_settled.disconnect(
                self.wait_signals_prepare_measurement.signals['xystage'].set_state)
            self.instruments['laser'].laser_stable.disconnect(
                self.wait_signals_prepare_measurement.signals['laser'].set_state)
            self.wait_signals_prepare_measurement.global_done.disconnect(self.measure)
            self.instruments['spectrometer'].measurement_done.disconnect(
                self.wait_signals_measurement.signals['spectrometer'].set_state)
            self.instruments['powermeter'].measurement_done.disconnect(
                self.wait_signals_measurement.signals['powermeter'].set_state)
            self.wait_signals_measurement.global_done.disconnect(self.process_data)
            self.wait_signals_prepare_measurement = None
            self.wait_signals_measurement = None
        elif self.experiment == 'decay':
            self.instruments['xystage'].stage_settled.disconnect(
                self.wait_signals_prepare_measurement.signals['xystage'].set_state)
            self.instruments['laser'].laser_stable.disconnect(
                self.wait_signals_prepare_measurement.signals['laser'].set_state)
            self.wait_signals_prepare_measurement.global_done.disconnect(self.measure)
            self.wait_signals_prepare_measurement = None
            self.instruments['digitizer'].measurement_done.connect(self.process_data)

    def _align(self):
        """
        Start the repeated timer for reading out instruments. For decay, set the digitizer readout mode to timed to
        make the readout time-efficient
        """
        self._connect_signals_align()
        if self.experiment == 'decay':
            self.instruments['digitizer'].polltime = self.polltime
            self.instruments['digitizer'].pulses_per_measurement = math.ceil(self.polltime * 101)
            self.instruments['digitizer'].polltime_enabled = True
        self.heartbeat.start()

    def _stop_align(self):
        self._disconnect_signals_align()
        """ Stop the repeated timer for reading out instruments. Shut down the laser. """
        self.heartbeat.stop()
        # wait till laser is done measuring
        time.sleep(0.3)
        if self.experiment in ['excitation_emission', 'decay']:
            self.instruments['shuttercontrol'].disable()
            self.instruments['laser'].energylevel = 'Off'

    def _measure_instruments(self):
        """ Measure the instruments. They all have a measure method. """
        for inst in self.instruments.keys():
            if not self.instruments[inst].measuring:
                QTimer.singleShot(0, self.instruments[inst].measure)

    # region parse config

    def _parse_config(self):
        # read in the ui settings
        self.logger.info('parsing instrument configuration started')
        path_settings = Path(__file__).parent.parent / 'config/settings_ui.yaml'
        with path_settings.open() as f:
            self.settings_ui = yaml_safe_load(f)
        # pick parsing routine
        if self.calibration:
            self._parse_config_calibration()
        elif self.experiment == 'transmission':
            self._parse_config_transmission()
            self.start_experiment()
        elif self.experiment == 'excitation_emission':
            self._parse_config_excitation_emission()
            self.start_experiment()
        elif self.experiment == 'decay':
            self._parse_config_decay()
            self.start_experiment()

    def _parse_config_calibration(self):
        """ Parse the configuration for beamsplitter calibration """
        self.logger.info('parsing configuration beamsplitter calibration')
        self.calibration_status.emit('started calibration')
        self.measurement_parameters = {}
        self._parse_excitation_wavelengths()
        self._parse_lasersettings('Max')
        self._parse_powermetersettings(3000)
        self.instruments['shuttercontrol'].disable()
        self.logger.info('Moving stage away for calibration')
        self.instruments['xystage'].move_with_wait(0, 0)

    def _parse_config_transmission(self):
        """ Parse transmission configuration """
        self.logger.info(f'parsing configuration {self.experiment}')
        self._parse_xypositions()
        self._add_lamp_measurement()
        self._add_dark_measurement()
        self._parse_spectrometersettings()

    def _parse_config_excitation_emission(self):
        """ Parse excitation emission configuration """
        self.logger.info(f'parsing configuration {self.experiment}')
        self._parse_xypositions()
        self._parse_excitation_wavelengths()
        self._add_dark_measurement()
        self._parse_spectrometersettings()
        self._parse_powermetersettings()
        self._parse_lasersettings()
        self._parse_connect_spectrometer_powermeter()

    def _parse_config_decay(self):
        """ Parse decay configuration. """
        self.logger.info('parsing decay configuration')
        self._parse_xypositions()
        self._parse_excitation_wavelengths()
        self._parse_digitizersettings()
        self._parse_lasersettings()

    def _parse_xypositions(self):
        """ Parse position settings from the ui to make the position measurement parameters. """
        self.logger.info('parse position settings')
        lightsource = 'lamp' if self.experiment == 'transmission' else 'laser'
        substrate = self.settings_ui[self.experiment][f'widget_file_{self.experiment}']['comboBox_substrate']
        substratesettings = self.config['substrates'][substrate]
        xysettings = self.settings_ui[self.experiment][f'widget_xystage_{self.experiment}']
        x_num = xysettings['spinBox_x_num']
        x_off_left = xysettings['spinBox_x_off_left']
        x_off_right = xysettings['spinBox_x_off_right']
        x_start = substratesettings[f'x_{lightsource}'] + substratesettings['dfhx']
        width_sample = substratesettings['whse']
        width_sample_usable = substratesettings['ws']
        x = self._define_positions(x_num, x_off_left, x_off_right, x_start, width_sample, width_sample_usable, 'x')
        y_num = xysettings['spinBox_y_num']
        y_off_bottom = xysettings['spinBox_y_off_bottom']
        y_off_top = xysettings['spinBox_y_off_top']
        y_start = substratesettings[f'y_{lightsource}'] + substratesettings['dfhy']
        height_sample = substratesettings['hhse']
        height_sample_usable = substratesettings['hs']
        y = self._define_positions(y_num, y_off_bottom, y_off_top, y_start, height_sample, height_sample_usable, 'y')
        self.measurement_parameters = {}
        self.logger.info(f'x = {x}, y = {y}')
        self._add_measurement_parameter('x', x)
        self._add_measurement_parameter('y', y)

    def _parse_excitation_wavelengths(self):
        """ Parse the laser excitation wavelength settings to measurement parameters. """
        self.logger.info('parse laser excitation wavelength settings')
        lasersettings = self.settings_ui[self.experiment][f'widget_laser_{self.experiment}']
        wl_start = lasersettings['spinBox_wavelength_start']
        wl_step = lasersettings['spinBox_wavelength_step']
        wl_stop = lasersettings['spinBox_wavelength_stop'] + 1
        wavelengths = np.arange(wl_start, wl_stop, wl_step)
        self._add_measurement_parameter('wl', wavelengths)

    def _add_measurement_parameter(self, name, parameter):
        """ Add a measurement parameters by repeating all existing measurement parameters for the new parameter """
        self.logger.debug('adding measurement parameter')
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
        dark_lamp_y = np.array(68)
        self.measurement_parameters['x'] = np.hstack((dark_lamp_x, self.measurement_parameters['x']))
        self.measurement_parameters['y'] = np.hstack((dark_lamp_y, self.measurement_parameters['y']))
        if 'wl' in self.measurement_parameters.keys():
            self.measurement_parameters['wl'] = np.hstack((300.123, self.measurement_parameters['wl']))

    def _add_lamp_measurement(self):
        # adds location to take a dark spectrum
        dark_lamp_x = np.array(0)
        dark_lamp_y = np.array(0)
        self.measurement_parameters['x'] = np.hstack((dark_lamp_x, self.measurement_parameters['x']))
        self.measurement_parameters['y'] = np.hstack((dark_lamp_y, self.measurement_parameters['y']))

    def _parse_spectrometersettings(self):
        """ Parse the spectrometer settings. """
        smsettings = self.settings_ui[self.experiment][f'widget_spectrometer_{self.experiment}']
        self.instruments['spectrometer'].integrationtime = smsettings['spinBox_integration_time_experiment']
        self.instruments['spectrometer'].average_measurements = smsettings['spinBox_averageing_experiment']
        self.instruments['spectrometer'].clear_dark()
        self.instruments['spectrometer'].clear_lamp()
        self.instruments['spectrometer'].transmission = False
        self.logger.info('parsed spectrometer settings')

    def _parse_powermetersettings(self, *integrationtime):
        """
        Parse the powermeter settings. Set integration time according to spectrometer or according to input.
        """
        if integrationtime:
            self.logger.info('Parsing powermeter settings beamsplitter calibration')
            self.instruments['powermeter'].prepare_measurement_multiple()
            self.instruments['powermeter'].integration_time = integrationtime[0]
            return
        # integration time of powermeter is the same as integration time of spectrometer
        self.logger.info(f'Parsing powermeter settings {self.experiment}')
        smsettings = self.settings_ui[self.experiment][f'widget_spectrometer_{self.experiment}']
        integration_time_sm = smsettings['spinBox_integration_time_experiment']
        averageing_sm = smsettings['spinBox_averageing_experiment']
        self.instruments['powermeter'].prepare_measurement_multiple()
        self.instruments['powermeter'].integration_time = integration_time_sm * averageing_sm

    def _parse_connect_spectrometer_powermeter(self):
        """
        connect the 'cache-cleared' signal of the spectrometer to the measure method of the
        powermeter to synchronize measurements
        """
        self.instruments['spectrometer'].cache_cleared.connect(self.instruments['powermeter'].measure)
        self.logger.info('connected spectrometer cache cleared to powermeter start measure')

    def _parse_lasersettings(self, *level):
        """
        Parse the laser settings
        """
        self.logger.info('parsing laser settings')
        lasersettings = self.settings_ui[self.experiment][f'widget_laser_{self.experiment}']
        self.instruments['laser'].output = True
        if level:
            self.instruments['laser'].energylevel = level[0]
        else:
            self.instruments['laser'].energylevel = lasersettings['comboBox_energy_level_experiment']

    def _parse_digitizersettings(self):
        """ Parse the digitizer settings from the ui to the digitizer """
        self.logger.debug('parsing digitizersettings')

        digitizersettings = self.settings_ui[self.experiment][f'widget_digitizer_{self.experiment}']

        self.instruments['digitizer'].data_channel = int(digitizersettings['comboBox_data_channel_experiment'])
        self.instruments['digitizer'].jitter_channel = int(digitizersettings['comboBox_jitter_channel_experiment'])
        self.instruments['digitizer'].jitter_correction_enabled = digitizersettings[
            'checkBox_jitter_correction_experiment']
        self.instruments['digitizer'].measurement_mode = digitizersettings['comboBox_measurement_mode_experiment']
        self.instruments['digitizer'].polltime_enabled = False
        self.instruments['digitizer'].pulses_per_measurement = digitizersettings['spinBox_number_pulses_experiment']
        self.instruments['digitizer'].post_trigger_size = digitizersettings['spinBox_post_trigger_size_experiment']

        timerange = TIMERANGES[self.instruments['digitizer'].model].index(digitizersettings[
                                                                              'comboBox_time_range_experiment'])
        self.instruments['digitizer'].record_length = timerange
        self.instruments['digitizer'].single_photon_counting_treshold = digitizersettings[
            'spinBox_single_photon_treshold_experiment']
        self.instruments['digitizer'].set_dc_offset_data_channel(digitizersettings['spinBox_dc_offset_experiment'])

        self.instruments['digitizer'].set_active_channels()

    def _define_positions(self, num, off1, off2, start, sse, ss, param: str):
        """
        Return the x and y positions where the stage should measure. Also populate the offset and sample size dict
        for writing these offsets to the file
        """
        # sse is sample size including edge of sample hodler, ss is visible part only
        bw = 4
        off1_mm = (ss - bw) * off1 / (100 + off2)
        off2_mm = (ss - bw) * off2 / (100 + off1)
        span = ss - bw - off1_mm - off2_mm
        self.logger.info(f'off1 = {off1_mm}, off2 = {off2_mm}, span = {span}')

        # need the left offset from x and the top offset from y

        if num == 1:
            if param == 'x':
                positions = np.array([(ss + off1_mm - off2_mm) / 2])
            else:
                positions = np.array([(ss - off1_mm + off2_mm) / 2])
            positions = positions + start
        else:
            positions = np.linspace(0, span, num)
            offset = off1_mm if param == 'x' else off2_mm
            positions = positions + start + bw / 2 + offset

        self.logger.debug(f'positions = {positions}')

        # write settings to dictionary for later retrieval offset here are with respect to sample outer edge
        self.position_offsets[param] = {}
        self.position_offsets['beam_width'] = 4
        if param == 'x':
            self.position_offsets[param]['sample_width'] = sse
            self.position_offsets[param]['sample_width_effective'] = ss
            self.position_offsets[param]['offset_left'] = off1_mm + bw / 2 + (sse - ss) / 2
            self.position_offsets[param]['offset_right'] = off2_mm + bw / 2 + (sse - ss) / 2
        elif param == 'y':
            self.position_offsets[param]['sample_height'] = sse
            self.position_offsets[param]['sample_height_effective'] = ss
            self.position_offsets[param]['offset_bottom'] = off1_mm + bw / 2 + (sse - ss) / 2
            self.position_offsets[param]['offset_top'] = off2_mm + bw / 2 + (sse - ss) / 2

            self.logger.debug(f'position offset  = {self.position_offsets}')
        return positions

    # endregion

    # region open file

    def _open_file(self):
        # pick open file process
        if self.calibration:
            self._open_file_calibration()
            self.logger.info('waiting 5 seconds for powermeter to reach equilibrium temperature')
            self.calibration_status.emit('calibration started, waiting for temperature equilibrium')
            QTimer.singleShot(5000, self.prepare)
        elif self.experiment == 'transmission':
            self._open_file_transmission()
            self.prepare()
        elif self.experiment == 'excitation_emission':
            self._open_file_excitation_emission()
            self.prepare()
        elif self.experiment == 'decay':
            self._open_file_decay()
            self.prepare()

    def _open_file_calibration(self):
        """ Set the filename for the calibration file and open the dataframe. """

        lasersettings = self.settings_ui['excitation_emission']['widget_laser_excitation_emission']
        wlstart = lasersettings['spinBox_wavelength_start']
        wlstop = lasersettings['spinBox_wavelength_stop']
        wlstep = lasersettings['spinBox_wavelength_step']

        self.startingtime = time.time()
        date = time.strftime("%y%m%d%H%M", time.localtime(self.startingtime))

        wl = f'{wlstart}_{wlstep}_{wlstop}_nm'
        self.calibration_fname = f'{self.storage_dir_calibration}/{self.beamsplitter}_{wl}_{date}.csv'
        self.calibration_position = 1
        self.calibration_dataframe = pd.DataFrame(columns=['Wavelength [nm]', 'Position', 'Power [W]', 'Time [s]'])

    def _open_file_transmission(self):
        self._load_create_file()
        self._write_positionsettings()
        self._write_spectrometersettings()
        self._create_dimensions_transmission()

    def _open_file_excitation_emission(self):
        self._load_create_file()
        self._write_positionsettings()
        self._write_lasersettings()
        self._write_powermetersettings()
        self._write_spectrometersettings()
        self._write_beamsplitter_calibration()
        self._create_dimensions_excitation_emission()

    def _open_file_decay(self):
        self._load_create_file()
        self._write_positionsettings()
        self._write_lasersettings()
        self._write_digitizersettings()
        self._create_dimensions_decay()

    def _load_create_file(self):
        # reads the storage directory and sample name from the settings, creates a file and directory
        filesettings = self.settings_ui[self.experiment][f'widget_file_{self.experiment}']
        storage_dir = filesettings['lineEdit_directory']
        sample = filesettings['lineEdit_sample']
        self.startingtime = time.time()
        self.experimentdate = time.strftime("%y%m%d%H%M", time.localtime(self.startingtime))
        fname = f'{storage_dir}/{sample}_{self.experiment}_{self.experimentdate}'
        comment = filesettings['plainTextEdit_comments']
        substrate = filesettings['comboBox_substrate']
        ndfilter = filesettings['comboBox_nd_filter']
        longpassfilter = filesettings['comboBox_longpass_filter']
        bandpassfilter = filesettings['comboBox_bandpass_filter']

        self.dataset = Dataset(f'{fname}.hdf5', 'w', format='NETCDF4')

        gensettings = self.dataset.createGroup(f'settings/general')
        gensettings.experiment = self.experiment
        gensettings.sample = sample
        gensettings.comment = comment
        gensettings.substrate = substrate
        gensettings.filter_nd = ndfilter
        gensettings.filter_longpass = longpassfilter
        gensettings.filter_bandpass = bandpassfilter

    def _write_positionsettings(self):
        positionsettings = self.dataset.createGroup(f'settings/xystage')
        # exclude positions of dark and lamp spectra where applicable.
        paramdict = {'transmission': 2, 'excitation_emission': 1, 'decay': 1}
        positionsettings.xnum = len(np.unique(self.measurement_parameters['x'][paramdict[self.experiment]:]))
        positionsettings.ynum = len(np.unique(self.measurement_parameters['y'][paramdict[self.experiment]:]))
        positionsettings.sample_width = self.position_offsets['x']['sample_width']
        positionsettings.sample_width_effective = self.position_offsets['x']['sample_width_effective']
        positionsettings.offset_left = self.position_offsets['x']['offset_left']
        positionsettings.offset_right = self.position_offsets['x']['offset_right']
        positionsettings.sample_height = self.position_offsets['y']['sample_height']
        positionsettings.sample_height_effective = self.position_offsets['y']['sample_height_effective']
        positionsettings.offset_bottom = self.position_offsets['y']['offset_bottom']
        positionsettings.offset_top = self.position_offsets['y']['offset_top']

    def _write_spectrometersettings(self):
        spectrometersettings = self.dataset.createGroup(f'settings/spectrometer')
        spectrometersettings.integrationtime = self.instruments['spectrometer'].integrationtime
        spectrometersettings.average_measurements = self.instruments['spectrometer'].average_measurements
        spectrometersettings.spectrometer = str(self.instruments['spectrometer'].spec)
        spectrometersettings.wlnum = len(self.instruments['spectrometer'].wavelengths)

    def _write_lasersettings(self):
        lasersettings = self.dataset.createGroup(f'settings/laser')
        lasersettings.energylevel = self.instruments['laser'].energylevel
        lasersettings.wlnum = len(np.unique(self.measurement_parameters['wl']))

    def _write_powermetersettings(self):
        pmsettings = self.dataset.createGroup(f'settings/powermeter')
        pmsettings.integrationtime = self.instruments['powermeter'].integration_time
        pmsettings.sensor = self.instruments['powermeter'].sensor['Model']
        pmsettings.sensor_serial_number = self.instruments['powermeter'].sensor['Serial_Number']
        pmsettings.sensor_calibration_date = self.instruments['powermeter'].sensor['Calibration_Date']

    def _write_digitizersettings(self):
        digitizersettings = self.dataset.createGroup(f'settings/digitizer')
        digitizersettings.active_channels = list(self.instruments['digitizer'].active_channels)
        digitizersettings.samples = self.instruments['digitizer'].record_length
        digitizersettings.post_trigger_size = self.instruments['digitizer'].post_trigger_size
        digitizersettings.samplerate = self.instruments['digitizer'].sample_rate
        digitizersettings.model = self.instruments['digitizer'].model
        digitizersettings.pulses = self.instruments['digitizer'].pulses_per_measurement
        digitizersettings.measurement_mode = self.instruments['digitizer'].measurement_mode
        digitizersettings.jitter_correction = str(self.instruments['digitizer'].jitter_correction_enabled)
        digitizersettings.jitter_channel = self.instruments['digitizer'].jitter_channel
        digitizersettings.single_photon_counting_treshold = \
            self.instruments['digitizer'].single_photon_counting_treshold
        digitizersettings.dc_offset = self.instruments['digitizer'].get_dc_offset(
            self.instruments['digitizer'].data_channel)
        digitizersettings.data_channel = self.instruments['digitizer'].data_channel

    def _write_beamsplitter_calibration(self):
        """
        writes calibration file to main file for automatic processing in matlab
        checks if file is selected and exists
        creates folder with attributes, dimensions, variables and data
        """
        fname = self.settings_ui['lineEdit_beamsplitter_calibration_file']

        if not fname:
            self.logger.info('No calibration file was selected')
            return
        try:
            df = pd.read_csv(fname)
            self.logger.info(f'Adding calibration file {fname}')
        except FileNotFoundError as e:
            self.logger.info(f'No calibration file with name {fname} found - {e}')
            return

        wavelength = list(df['Wavelength [nm]'])
        position = list(df['Position'])
        power = list(df['Power [W]'])
        times = list(df['Time [s]'])

        group_beamsplitter = self.dataset.createGroup(f'calibration_beamsplitter')
        group_beamsplitter.createDimension('powermeasurements', len(times))
        wl = group_beamsplitter.createVariable('wavelength', 'f8', 'powermeasurements', fill_value=np.nan)
        wl.units = 'nm'
        pos = group_beamsplitter.createVariable('position', 'f8', 'powermeasurements', fill_value=np.nan)
        p = group_beamsplitter.createVariable('power', 'f8', 'powermeasurements', fill_value=np.nan)
        p.units = 'W'
        t = group_beamsplitter.createVariable('times', 'f8', 'powermeasurements', fill_value=np.nan)
        t.units = 's'
        wl[:] = wavelength
        pos[:] = position
        p[:] = power
        t[:] = times

    def _create_dimensions_transmission(self):
        self.dataset.createDimension('xy_position', 2)
        self.dataset.createDimension('emission_wavelengths', len(self.instruments['spectrometer'].wavelengths))
        self.dataset.createDimension('spectrometer_intervals',
                                     self.instruments['spectrometer'].average_measurements * 2)
        self.dataset.createDimension('single', 1)

    def _create_dimensions_excitation_emission(self):
        self.dataset.createDimension('xy_position', 2)
        self.dataset.createDimension('emission_wavelengths', len(self.instruments['spectrometer'].wavelengths))
        self.dataset.createDimension('spectrometer_intervals',
                                     self.instruments['spectrometer'].average_measurements * 2)
        self.dataset.createDimension('single', 1)
        excitation_wavelenghts = len(np.unique(self.measurement_parameters['wl'][1:]))
        self.dataset.createDimension('excitation_wavelengths', excitation_wavelenghts)
        self.dataset.createDimension('power_measurements', self.instruments['powermeter'].measurements_multiple)

    def _create_dimensions_decay(self):
        self.dataset.createDimension('xy_position', 2)
        self.dataset.createDimension('single', 1)
        excitation_wavelenghts = len(np.unique(self.measurement_parameters['wl'][1:]))
        self.dataset.createDimension('excitation_wavelengths', excitation_wavelenghts)
        samples = int(self.instruments['digitizer'].record_length)
        self.dataset.createDimension('samples', samples)

    # endregion
    # region prepare measurement

    @timed
    def _prepare_measurement(self):
        if self.calibration:
            self._prepare_measurement_calibration()
            self.measure()
        elif self.experiment == 'transmission':
            self._prepare_measurement_transmission()
        elif self.experiment == 'excitation_emission':
            self._prepare_measurement_excitation_emission()
        elif self.experiment == 'decay':
            self._prepare_measurement_decay()

    def _prepare_measurement_calibration(self):
        """ Set the laser and powermeter to the correct wavelength """
        self._control_shutter()
        self._prepare_laser()
        self._prepare_powermeter()

    def _prepare_measurement_transmission(self):
        self._prepare_move_stage()

    def _prepare_measurement_excitation_emission(self):
        self.wait_signals_prepare_measurement.reset()
        self._control_shutter()
        self._prepare_powermeter()
        self._prepare_laser()
        self._prepare_move_stage()

    def _prepare_measurement_decay(self):
        self.wait_signals_prepare_measurement.reset()
        self._control_shutter()
        self._prepare_digitizer()
        self._prepare_laser()
        self._prepare_move_stage()

    def _prepare_move_stage(self):
        """ Move the stages to the new position. """
        try:
            x = self.measurement_parameters['x'][self.measurement_index]
            y = self.measurement_parameters['y'][self.measurement_index]
            self.logger.info(f'moving stages to x = {x}, y = {y}')
            QTimer.singleShot(0, lambda xval=x, yval=y: self.instruments['xystage'].move_with_wait(xval, yval))
        except IndexError:
            raise IndexError

    def _control_shutter(self):
        """ Enable shutter except when a dark measurement is taken. """
        if self.measurement_index == 0 and self.experiment == 'excitation_emission' and not self.calibration:
            self.instruments['shuttercontrol'].disable()
            self.logger.info('shutter disabled for dark measurement')
        else:
            self.instruments['shuttercontrol'].enable()
            self.logger.info('shutter enabled')

    def _prepare_powermeter(self):
        """ Set the powermeter to the new laser wavelength. """
        wl = self.measurement_parameters['wl'][self.measurement_index]
        self.instruments['powermeter'].wavelength = wl
        self.logger.info(f'powermeter set to {wl} nm')

    def _prepare_digitizer(self):
        """ Clear the average measurements from the digitizer. """
        self.instruments['digitizer'].clear_measurement()

    def _prepare_laser(self):
        """ Set the laser to the new wavelength. """
        wl = self.measurement_parameters['wl'][self.measurement_index]
        QTimer.singleShot(0, lambda wavlength=wl: self.instruments['laser'].set_wavelength_wait_stable(wl))

    # endregion

    # region measure

    def _measure(self):
        """
        Perform the actual measurements on the instruments. Since these are threaded processes can't time the
        function but must time when the next process starts.
        """
        self.timekeeper = time.time()
        if self.calibration:
            self._measure_calibration()
        elif self.experiment == 'transmission':
            self._measure_transmission()
        elif self.experiment == 'excitation_emission':
            self.wait_signals_measurement.reset()
            self._measure_excitation_emission()
        elif self.experiment == 'decay':
            self._measure_decay()

    def _measure_calibration(self):
        """ Measure the powermeter and pass the plotinfo to the powermeter for plotting. """
        wlnum = len(self.measurement_parameters['wl'])
        wl = self.measurement_parameters['wl'][self.measurement_index]
        self.logger.info(f'Started measuring power calibration. '
                         f'Wavelength {self.measurement_index + 1} of {wlnum} - ({wl} nm)')
        plotinfo = f'Power Calibration at Position {self.calibration_position}, ' \
                   f'wavelength {self.measurement_index + 1} of {wlnum} ({wl} nm)'
        QTimer.singleShot(0, lambda pi=plotinfo: self.instruments['powermeter'].measure(plotinfo))

    def _measure_transmission(self):
        """
        Measure the spectrometer.
        The first measurement is a dark measurement, the second one a lamp measurement. The next spectra are all
        transmission spectra, so set the spectrometer transmission attribute to true.
        """
        if self.measurement_index == 0:
            self.logger.info('Measuring dark spectrum transmission experiment')
            plotinfo = f'Dark Spectrum Experiment'
            QTimer.singleShot(0, lambda pi=plotinfo: self.instruments['spectrometer'].measure_dark(pi))
        elif self.measurement_index == 1:
            self.logger.info('Measuring lamp spectrum transmission experiment')
            plotinfo = f'Lamp Spectrum Experiment'
            QTimer.singleShot(0, lambda pi=plotinfo: self.instruments['spectrometer'].measure_lamp(pi))
        else:
            x_inx, y_iny = self._variable_index()
            xnum = len(np.unique(self.measurement_parameters['x'][2:]))
            ynum = len(np.unique(self.measurement_parameters['y'][2:]))
            self.logger.info(f'Transmission Spectrum. X = {x_inx + 1} of {xnum}, Y = {y_iny + 1} of {ynum}')
            plotinfo = f'Transmission Spectrum - X = {x_inx + 1} of {xnum}, Y = {y_iny + 1} of {ynum}'
            self.instruments['spectrometer'].transmission = True
            QTimer.singleShot(0, lambda pi=plotinfo: self.instruments['spectrometer'].measure(pi))

    def _measure_excitation_emission(self):
        """
        Measure the spectrometer. 'Cache cleared' signal of spectrometer
        is connected to the powermeter such that power measurement starts when cache is cleared.

        First measurement is a dark measurement.
        """
        if self.measurement_index == 0:
            self.logger.info('Measuring dark spectrum excitation emission experiment')
            plotinfo = 'Dark Spectrum'
            QTimer.singleShot(0, lambda pi=plotinfo: self.instruments['spectrometer'].measure_dark(pi))
        else:
            x_inx, y_iny, wl_inwl = self._variable_index()
            xnum = len(np.unique(self.measurement_parameters['x'][1:]))
            ynum = len(np.unique(self.measurement_parameters['y'][1:]))
            wlnum = len(np.unique(self.measurement_parameters['wl'][1:]))
            wl = self.measurement_parameters['wl'][self.measurement_index]
            self.logger.info(f'Measuring spectrum excitation emission experiment. X = {x_inx + 1} of {xnum}, '
                             f'Y = {y_iny + 1} of {ynum}\nWavelength = {wl_inwl + 1} of {wlnum} ({wl} nm)')
            plotinfo = f'Spectrum minus dark at X = {x_inx + 1} of {xnum}, Y = {y_iny + 1} of {ynum}, ' \
                       f'Wavelength = {wl_inwl + 1} of {wlnum} ({wl} nm)'
            QTimer.singleShot(0, lambda pi=plotinfo: self.instruments['spectrometer'].measure(pi))

    def _measure_decay(self):
        """ Call the measure function of the digitizer with relevant plotinfo. """
        x_inx, y_iny, wl_inwl = self._variable_index()
        xnum = len(np.unique(self.measurement_parameters['x'][1:]))
        ynum = len(np.unique(self.measurement_parameters['y'][1:]))
        wlnum = len(np.unique(self.measurement_parameters['wl'][1:]))
        wl = self.measurement_parameters['wl'][self.measurement_index]

        self.logger.info(f'Measuring Decay Spectrum. X = {x_inx + 1} of {xnum}, '
                         f'Y = {y_iny + 1} of {ynum}\nWavelength = {wl_inwl + 1} of {wlnum} ({wl} nm)')
        plotinfo = f'X = {x_inx + 1} of {xnum}, Y = {y_iny + 1} of {ynum}, ' \
                   f'Wavelength = {wl_inwl + 1} of {wlnum} ({wl} nm)'
        QTimer.singleShot(0, lambda pi=plotinfo: self.instruments['digitizer'].measure(pi))

    # endregion

    # region process data
    def _process_data(self):
        time_measuring = time.time() - self.timekeeper
        self.measurement_duration += time_measuring
        self.logger.info(f'processing data {self.experiment}, measurement time = {time_measuring}')
        self.write_file()

    # endregion

    # region write file

    @timed
    def _write_file(self):
        self.logger.info(f'writing data to file')
        if self.calibration:
            self._write_file_calibration()
        elif self.experiment == 'transmission':
            self._write_file_transmission()
        elif self.experiment == 'excitation_emission':
            self._write_file_excitation_emission()
        elif self.experiment == 'decay':
            self._write_file_decay()

        self.measurement_index += 1
        self.calculate_progress()

    def _write_file_calibration(self):
        """ Write the power data to a csv file """

        self.logger.info('writing power to calibration csv')
        times = self.instruments['powermeter'].last_times
        powers = self.instruments['powermeter'].last_powers
        samples = len(times)
        positions = np.repeat(self.calibration_position, samples)
        wavelengths = np.repeat(self.measurement_parameters['wl'][self.measurement_index], samples)
        dataframe = pd.DataFrame({'Wavelength [nm]': wavelengths, 'Position': positions,
                                  'Power [W]': powers, 'Time [s]': times})
        self.calibration_dataframe = self.calibration_dataframe.append(dataframe, ignore_index=True)
        self.calibration_dataframe.to_csv(self.calibration_fname)

    def _write_file_transmission(self):
        """
        Make folders for each measurement position. Includes dark folder and lamp folder. Transmission has only
        one measurement per position so folders need to be created always.
        """
        if self.measurement_index == 0:
            datagroup = self.dataset.createGroup('dark')
        elif self.measurement_index == 1:
            datagroup = self.dataset.createGroup('lamp')
        else:
            x_inx, y_iny = self._variable_index()
            datagroup = self.dataset.createGroup(f'x{x_inx + 1}y{y_iny + 1}')

        xy_pos, em_wl, spectrum, spectrum_t = self._create_variables_transmission(datagroup)

        xy_pos[:] = self._write_position()
        em_wl[:] = self.instruments['spectrometer'].wavelengths
        spectrum[:] = self.instruments['spectrometer'].last_intensity
        spectrum_t[:] = np.array(self.instruments['spectrometer'].last_times) - self.startingtime

    def _write_file_excitation_emission(self):
        # make folders for each measurement position, includes dark folder for dark measurement
        global wl_in_wl

        if self.measurement_index == 0:
            datagroup = self.dataset.createGroup('dark')
        else:
            x_inx, y_iny, wl_in_wl = self._variable_index()
            # check if folder with position index exists, otherwise create it
            try:
                datagroup = self.dataset[f'x{x_inx + 1}y{y_iny + 1}']
            except IndexError:
                datagroup = self.dataset.createGroup(f'x{x_inx + 1}y{y_iny + 1}')
        try:
            xy_pos = datagroup['position']
            em_wl = datagroup['emission']
            spectrum = datagroup['spectrum']
            spectrum_t = datagroup['spectrum_t']
            ex_wl = datagroup['excitation']
            t_power = datagroup['power_t']
            power = datagroup['power']
        except IndexError:
            xy_pos, em_wl, spectrum, spectrum_t, ex_wl, t_power, power = \
                self._create_variables_excitation_emission(datagroup)

        if self.measurement_index == 0:
            em_wl[:] = self.instruments['spectrometer'].wavelengths
            spectrum[:] = self.instruments['spectrometer'].last_intensity
            spectrum_t[:] = np.array(self.instruments['spectrometer'].last_times) - self.startingtime
            xy_pos[:] = self._write_position()
            ex_wl[:] = self.instruments['laser'].wavelength
            t_power[:] = self.instruments['powermeter'].last_times
            power[:] = self.instruments['powermeter'].last_powers
        else:
            em_wl[:] = self.instruments['spectrometer'].wavelengths
            spectrum[wl_in_wl, :] = self.instruments['spectrometer'].last_intensity
            spectrum_t[wl_in_wl, :] = np.array(self.instruments['spectrometer'].last_times) - self.startingtime
            xy_pos[:] = self._write_position()
            ex_wl[wl_in_wl] = self.instruments['laser'].wavelength
            t_power[:] = self.instruments['powermeter'].last_times
            power[wl_in_wl] = self.instruments['powermeter'].last_powers

    def _write_file_decay(self):
        x_inx, y_iny, wl_in_wl = self._variable_index()
        # check if folder with position index exists, otherwise create it
        try:
            datagroup = self.dataset[f'x{x_inx + 1}y{y_iny + 1}']
        except IndexError:
            datagroup = self.dataset.createGroup(f'x{x_inx + 1}y{y_iny + 1}')
        try:
            xy_pos = datagroup['position']
            ex_wl = datagroup['excitation']
            pulses = datagroup['pulses']
        except IndexError:
            xy_pos, ex_wl, pulses = self._create_variables_decay(datagroup)

        xy_pos[:] = self._write_position()
        ex_wl[wl_in_wl] = self.instruments['laser'].wavelength
        if self.instruments['digitizer'].measurement_mode == 'averageing':
            pulses[wl_in_wl] = self.instruments['digitizer'].average_pulses
        elif self.instruments['digitizer'].measurement_mode == 'single photon counting':
            pulses[wl_in_wl] = self.instruments['digitizer'].single_photon_counts

    def _variable_index(self):
        """
        Create an index for the variables for the folder name per measurement position and for indexing the
        spectra per excitation wavelength.
        """
        x = self.measurement_parameters['x'][self.measurement_index]
        y = self.measurement_parameters['y'][self.measurement_index]
        # exclude positions of dark and lamp spectra where applicable.
        paramdict = {'transmission': 2, 'excitation_emission': 1, 'decay': 0}
        x_inx = list(np.unique(self.measurement_parameters['x'][paramdict[self.experiment]:])).index(x)
        y_iny = list(np.unique(self.measurement_parameters['y'][paramdict[self.experiment]:])).index(y)
        if self.experiment in ['excitation_emission', 'decay']:
            wl = self.measurement_parameters['wl'][self.measurement_index]
            wl_in_wls = list(np.unique(self.measurement_parameters['wl'][paramdict[self.experiment]:])).index(wl)
            return x_inx, y_iny, wl_in_wls
        else:
            return x_inx, y_iny

    @staticmethod
    def _create_variables_transmission(datagroup):
        xy_pos = datagroup.createVariable('position', 'f8', 'xy_position', fill_value=np.nan)
        xy_pos.units = 'mm'
        em_wl = datagroup.createVariable('emission', 'f8', 'emission_wavelengths', fill_value=np.nan)
        em_wl.units = 'nm'
        spectrum = datagroup.createVariable('spectrum', 'f8', 'emission_wavelengths', fill_value=np.nan)
        spectrum_t = datagroup.createVariable('spectrum_t', 'f8', 'spectrometer_intervals', fill_value=np.nan)
        spectrum.units = 'a.u.'
        spectrum_t.units = 's'
        return xy_pos, em_wl, spectrum, spectrum_t

    def _create_variables_excitation_emission(self, datagroup):
        xy_pos = datagroup.createVariable('position', 'f8', 'xy_position', fill_value=np.nan)
        xy_pos.units = 'mm'
        em_wl = datagroup.createVariable('emission', 'f8', 'emission_wavelengths', fill_value=np.nan)
        em_wl.units = 'nm'
        if self.measurement_index == 0:
            spectrum = datagroup.createVariable('spectrum', 'f8', 'emission_wavelengths', fill_value=np.nan)
            spectrum_t = datagroup.createVariable('spectrum_t', 'f8', 'spectrometer_intervals', fill_value=np.nan)
            ex_wl = datagroup.createVariable('excitation', 'f8', 'single', fill_value=np.nan)
            t_power = datagroup.createVariable('power_t', 'f8', 'power_measurements', fill_value=np.nan)
            power = datagroup.createVariable('power', 'f8', 'power_measurements', fill_value=np.nan)
            spectrum.units = 'a.u.'
            spectrum_t.units = 's'
            ex_wl.units = 'nm'
            t_power.units = 's'
            power.units = 'W'
            return xy_pos, em_wl, spectrum, spectrum_t, ex_wl, t_power, power
        else:
            spectrum = datagroup.createVariable('spectrum', 'f8', ('excitation_wavelengths',
                                                                   'emission_wavelengths'), fill_value=np.nan)
            spectrum_t = datagroup.createVariable('spectrum_t', 'f8', ('excitation_wavelengths',
                                                                       'spectrometer_intervals'), fill_value=np.nan)
            ex_wl = datagroup.createVariable('excitation', 'f8', 'excitation_wavelengths', fill_value=np.nan)
            t_power = datagroup.createVariable('power_t', 'f8', ('excitation_wavelengths', 'power_measurements')
                                               , fill_value=np.nan)
            power = datagroup.createVariable('power', 'f8', ('excitation_wavelengths', 'power_measurements')
                                             , fill_value=np.nan)
            spectrum.units = 'a.u.'
            spectrum_t.units = 's'
            ex_wl.units = 'nm'
            t_power.units = 's'
            power.units = 'W'
            return xy_pos, em_wl, spectrum, spectrum_t, ex_wl, t_power, power

    @staticmethod
    def _create_variables_decay(datagroup):
        xy_pos = datagroup.createVariable('position', 'f8', 'xy_position', fill_value=np.nan)
        xy_pos.units = 'mm'
        ex_wl = datagroup.createVariable('excitation', 'f8', 'excitation_wavelengths', fill_value=np.nan)
        ex_wl.units = 'nm'
        pulses = datagroup.createVariable('pulses', 'f8',
                                          ('excitation_wavelengths', 'samples'),
                                          fill_value=np.nan)
        pulses.units = 'normalized adc counts'
        return xy_pos, ex_wl, pulses

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
                self.logger.info('Getting position failed. Retrying {}'.format(keep_trying))
                self.logger.info('Reconnecting...')
                time.sleep(5 - keep_trying)
                self.instruments['xystage'].reconnect()
            if not failed:
                self.logger.info('Position acquisition successful!')
                keep_trying = 0

    # endregion

    # region calculate progress

    def _calculate_progress(self):
        """
        Calculate progress (in percent) and Estimated Completion Time.
        Uses the average of the preparation + measurement times

        Emit:
            progress (float): progress in percent
            ect (float): Estimated completion time as UNIX timestamp
        """
        keys = list(self.measurement_parameters.keys())
        progress = self.measurement_index / len(self.measurement_parameters[keys[0]])
        ect = (self.measurement_duration /
               self.measurement_index *
               (len(self.measurement_parameters[keys[0]]) - self.measurement_index)
               )
        self.ect.emit(int(ect))
        self.progress.emit(int(progress * 100))
        self.logger.info(f'Progress Measurement: {progress * 100} %')

        if progress == 1 and self.calibration_position == 1:
            self.wait_for_user()
            self.logger.info('Part one of calibration complete, prompting user')
        elif progress == 1:
            self.is_done = True
            self.measurement_complete()
            self.logger.info(f'Measurement Completed at: {time.ctime(ect)}')
        else:
            self.prepare()

    # endregion

    def _notify_user_calibration(self):
        """
        Shut the shutter so the powermeter can be put into position without burning it in the focal point.
        Emit signal which opens the dialog prompting the user to change the position of the power sensor.
        Set position attribute to two, reset measurement index.
        """
        self.instruments['shuttercontrol'].disable()
        self.logger.info('First part of beamsplitter calibration complete')
        self.measurement_index = 0
        self.calibration_position = 2
        self.calibration_half_signal.emit()
        pass

    def _return_setexperiment(self):
        self.signal_return_setexperiment.emit()

    def _measurement_aborted(self):
        if not self.calibration:
            self.dataset.close()
        else:
            self.calibration_complete_signal.emit()
        self.instruments['xystage'].stop_motors()
        self.reset_instruments()
        self.is_done = True
        self.finish_experiment()
        self.return_setexperiment()

    def _measurement_completed(self):
        if not self.calibration:
            self.dataset.close()
        else:
            self.calibration_complete_signal.emit()
        self.is_done = True
        self.reset_instruments()
        self.finish_experiment()
        self.return_setexperiment()

    def reset_instruments(self):
        """ Reset instrument settings for align state. """
        if self.calibration:
            self.instruments['powermeter'].integration_time = 200
            self.instruments['laser'].energylevel = 'Off'
            self.instruments['shuttercontrol'].disable()
            self.logger.info('setting instruments back to alignment/setexperiment settings')
        elif self.experiment == 'transmission':
            self.instruments['spectrometer'].integrationtime = 100
            self.logger.info('transmission ready, set spectrometer back to shorter integration time')
        elif self.experiment == 'excitation_emission':
            self.logger.info('excitation emission ready, disconnected cache cleared and set shorter integration'
                             'times for powermeter and spectrometer, turning off laser')
            self.instruments['spectrometer'].integrationtime = 100
            self.instruments['spectrometer'].cache_cleared.disconnect()
            self.instruments['powermeter'].integration_time = 200
            self.instruments['laser'].energylevel = 'Off'
        elif self.experiment == 'decay':
            self.logger.info('decay ready, reverting digitizer settings to align state, turning off laser')
            self.instruments['digitizer'].polltime = self.polltime
            self.instruments['digitizer'].pulses_per_measurement = math.ceil(self.polltime * 101)
            self.instruments['digitizer'].polltime_enabled = True
            self.instruments['laser'].energylevel = 'Off'


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers

    pathlogging = Path(__file__).parent.parent / 'logging/loggingconfig_testing.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
