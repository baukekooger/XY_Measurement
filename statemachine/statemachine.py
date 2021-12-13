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
    """ Wrapper function to be used as a decorator for timing functions. """
    def wrapper(self, *args, **kwargs):
        t1 = time.time()
        result = func(self, *args, **kwargs)
        t2 = time.time()
        self.measurement_duration += t2 - t1
        return result

    return wrapper


class StateMachine(QObject):
    """
    State Machine for the XY Setup

    For visualizing the states and transitions of the statemachine, refer to the PlotStateMachine class in
    statemachine_plot.py
    """

    signalstatechange = pyqtSignal(str)  # signal that emits the state
    progress = pyqtSignal(int)  # signal emitting the progress of the measurement
    ect = pyqtSignal(int)  # estimated completion time
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
        """ Reset certain attributes at the start of each experiment. """
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
        self.logger.info('initializing statemachine alignment measuring poll')
        self.polltime = 0.2
        self.heartbeat = QTimer()
        self.heartbeat.setInterval(int(self.polltime * 1000))
        self.heartbeat.timeout.connect(self._measure_instruments)

    def _start(self):
        pass

    def _define_experiment(self, page):
        """ Add the relevant instruments for the selected experiment. Remove unnecessary instruments. """
        self.experiment = self.config['experiments'][page]
        instruments_needed = self.config['instruments'][self.experiment]
        self.logger.info(f'defining instruments for statemachine. Experiment = {self.experiment}, '
                         f'instruments = {instruments_needed}')
        to_remove = [inst for inst in self.instruments.keys() if (inst not in instruments_needed)]
        self.logger.info(f'removing following instruments: {to_remove}')
        to_add = [inst for inst in instruments_needed if (inst not in self.instruments.keys())]
        self.logger.info(f'adding following instruments: {to_add}')
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
        self.logger.info('Connecting instrument signals to statemachine triggers for experiment routine')
        if self.calibration:
            self.instruments['xystage'].stage_settled.connect(self.start_experiment)
            self.instruments['laser'].laser_stable.connect(self.measure)
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
            self.instruments['laser'].laser_stable.disconnect(self.measure)
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
        self.logger.info('Align method called, starting polling heartbeat')
        if self.experiment == 'decay':
            self.instruments['digitizer'].polltime = self.polltime
            self.instruments['digitizer'].pulses_per_measurement = math.ceil(self.polltime * 101)
            self.instruments['digitizer'].polltime_enabled = True
        self.heartbeat.start()

    def _stop_align(self):
        """ Stop the repeated timer for reading out instruments. Shut down the laser. """
        self._disconnect_signals_align()
        self.logger.info('Stopping alignment polling heartbeat')
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
                self.logger.info(f'Calling measure method of {inst}')
                QTimer.singleShot(0, self.instruments[inst].measure)

    # region parse config

    def _parse_config(self):
        """ Pass the experiment configuration from the settings in the ui. """
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
        self._add_measurement_parameter('x', np.array([0]))
        self._add_measurement_parameter('y', np.array([0]))
        self._parse_excitation_wavelengths()
        self._parse_lasersettings('Max')
        self._parse_powermetersettings(3000)
        self.instruments['shuttercontrol'].disable()
        self.logger.info('Moving stage away for calibration')
        self.instruments['xystage'].setpoint_x = 0
        self.instruments['xystage'].setpoint_y = 0
        QTimer.singleShot(0, self.instruments['xystage'].move_to_setpoints)

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
        self.logger.info(f'x positions = {x}, y positions = {y}')
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
        """ Add a measurement parameter by repeating all existing measurement parameters for the new parameter """
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
        """
        Add a measurement position and excitation wavelength for a dark measurement.
        For transmission, this position blocks the light from the lamp. In excitation emission
        this blocking is done by the shutter
        """
        dark_lamp_x = np.array(20)
        dark_lamp_y = np.array(68)
        self.logger.info(f'adding a dark measurement at x = {dark_lamp_x}, y = {dark_lamp_y}')
        self.measurement_parameters['x'] = np.hstack((dark_lamp_x, self.measurement_parameters['x']))
        self.measurement_parameters['y'] = np.hstack((dark_lamp_y, self.measurement_parameters['y']))
        if 'wl' in self.measurement_parameters.keys():
            self.measurement_parameters['wl'] = np.hstack((300.123, self.measurement_parameters['wl']))

    def _add_lamp_measurement(self):
        """
        Add a lamp measurement position. This is only used for transmission measurements and reflects a positions
        where the light from the lamp goes directly through to the integrating sphere.
        """
        dark_lamp_x = np.array(0)
        # this y position makes sure it also works for the 22X22 sample
        dark_lamp_y = np.array(20)
        self.measurement_parameters['x'] = np.hstack((dark_lamp_x, self.measurement_parameters['x']))
        self.measurement_parameters['y'] = np.hstack((dark_lamp_y, self.measurement_parameters['y']))

    def _parse_spectrometersettings(self):
        """ Parse the spectrometer settings from the ui. """
        self.logger.info('parsing spectrometer settings')
        smsettings = self.settings_ui[self.experiment][f'widget_spectrometer_{self.experiment}']
        self.instruments['spectrometer'].integrationtime = smsettings['spinBox_integration_time_experiment']
        self.instruments['spectrometer'].average_measurements = smsettings['spinBox_averageing_experiment']
        self.instruments['spectrometer'].clear_dark()
        self.instruments['spectrometer'].clear_lamp()
        self.instruments['spectrometer'].transmission = False

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
        QTimer.singleShot(0, self.instruments['powermeter'].zero)

    def _parse_connect_spectrometer_powermeter(self):
        """
        Connect the 'cache-cleared' signal of the spectrometer to the measure method of the
        powermeter to synchronize measurements.
        """
        self.logger.info('connected spectrometer cache cleared to powermeter start measure')
        self.instruments['spectrometer'].cache_cleared.connect(self.instruments['powermeter'].measure)

    def _parse_lasersettings(self, *level):
        """
        Parse the laser settings from the ui or from user input.
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
        for writing these offsets to the file.
        """
        # sse is sample size including edge of sample hodler, ss is visible part only
        bw = 4  # beam width
        off1_mm = (ss - bw) * off1 / (100 + off2)
        off2_mm = (ss - bw) * off2 / (100 + off1)
        span = ss - bw - off1_mm - off2_mm
        self.logger.info(f'off1 = {off1_mm}, off2 = {off2_mm}, span = {span}, start = {start}')

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
        # write settings to dictionary for later retrieval. offsets here are with respect to sample outer edge
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
        self.logger.debug(f'position offset {param} = {self.position_offsets}')
        return positions

    # endregion

    # region open file

    def _open_file(self):
        """ Select the open file process depending on which experiment is run. """
        self.logger.info('opening file procedure started.')
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
        """
        Set the filename and open the calibration data file.
        Calibration file is a pandas dataframe which is written to csv at every measuement update.
        """
        lasersettings = self.settings_ui['excitation_emission']['widget_laser_excitation_emission']
        wlstart = lasersettings['spinBox_wavelength_start']
        wlstop = lasersettings['spinBox_wavelength_stop']
        wlstep = lasersettings['spinBox_wavelength_step']
        self.logger.info(f'opening calibration file, wlstart = {wlstart}, wlstep = {wlstep}, wlstop  = {wlstop}')
        self.startingtime = time.time()
        date = time.strftime("%y%m%d%H%M", time.localtime(self.startingtime))
        wl = f'{wlstart}_{wlstep}_{wlstop}_nm'
        self.calibration_fname = f'{self.storage_dir_calibration}/BSC_{self.beamsplitter}_{wl}_{date}.csv'
        self.calibration_position = 1
        self.calibration_dataframe = pd.DataFrame(columns=['Wavelength [nm]', 'Position', 'Power [W]', 'Time [s]'])

    def _open_file_transmission(self):
        """ Process for opening the transmission file and writing experiment setttings. """
        self.logger.info(f'opening file {self.experiment}')
        self._load_create_file()
        self._write_positionsettings()
        self._write_spectrometersettings()
        self._create_dimensions_transmission()

    def _open_file_excitation_emission(self):
        """ Process for opening the excitation emission file and writing experiment settings. """
        self.logger.info(f'opening file {self.experiment}')
        self._load_create_file()
        self._write_positionsettings()
        self._write_lasersettings()
        self._write_powermetersettings()
        self._write_spectrometersettings()
        self._write_beamsplitter_calibration()
        self._create_dimensions_excitation_emission()

    def _open_file_decay(self):
        """ Process for opening the excitation emission file and writing experiment settings. """
        self.logger.info(f'opening file {self.experiment}')
        self._load_create_file()
        self._write_positionsettings()
        self._write_lasersettings()
        self._write_digitizersettings()
        self._create_dimensions_decay()

    def _load_create_file(self):
        """
        Create an hdf5 file using the settings from the ui.
        Create a settings folder to store all the general settings as attributes to that folder.
        """
        filesettings = self.settings_ui[self.experiment][f'widget_file_{self.experiment}']
        storage_dir = filesettings['lineEdit_directory']
        sample = filesettings['lineEdit_sample']
        self.startingtime = time.time()
        self.experimentdate = time.strftime("%y%m%d%H%M", time.localtime(self.startingtime))
        fname = f'{storage_dir}/{sample}_{self.experiment}_{self.experimentdate}'
        self.logger.info(f'creating hdf5 dataset with filename: {fname}')
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
        """ Create a folder for position settings and write XY stage position settings as attributes of that folder. """
        self.logger.info('writing position settings')
        positionsettings = self.dataset.createGroup(f'settings/xystage')
        # exclude positions of dark and lamp spectra where applicable.
        paramdict = {'transmission': 2, 'excitation_emission': 1, 'decay': 0}
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
        """
        Create a spectrometer folder in the settings folder and write spectrometer settings as folder attributes.
        """
        self.logger.info('writing spectrometer settings')
        spectrometersettings = self.dataset.createGroup(f'settings/spectrometer')
        spectrometersettings.integrationtime = self.instruments['spectrometer'].integrationtime
        spectrometersettings.average_measurements = self.instruments['spectrometer'].average_measurements
        spectrometersettings.spectrometer = str(self.instruments['spectrometer'].spec)
        spectrometersettings.wlnum = len(self.instruments['spectrometer'].wavelengths)

    def _write_lasersettings(self):
        """ Create a laser folder in the settings folder and write laser settings as folder attributes. """
        self.logger.info('writing laser settings')
        lasersettings = self.dataset.createGroup(f'settings/laser')
        lasersettings.energylevel = self.instruments['laser'].energylevel
        lasersettings.wlnum = len(np.unique(self.measurement_parameters['wl']))

    def _write_powermetersettings(self):
        """ Create a powermeter folder in the settings folder and write laser settings as folder attributes. """
        self.logger.info('writing powermeter settings')
        pmsettings = self.dataset.createGroup(f'settings/powermeter')
        pmsettings.integrationtime = self.instruments['powermeter'].integration_time
        pmsettings.sensor = self.instruments['powermeter'].sensor['Model']
        pmsettings.sensor_serial_number = self.instruments['powermeter'].sensor['Serial_Number']
        pmsettings.sensor_calibration_date = self.instruments['powermeter'].sensor['Calibration_Date']

    def _write_digitizersettings(self):
        """ Create a digitizer folder in the settings folder and write laser settings as folder attributes. """
        self.logger.info('writing digitizer settings.')
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
        writes currently selected calibration file to main hdf5 file for automatic processing in matlab
        checks if file is selected and exists.
        Creates folder with attributes, dimensions, variables and data
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
        group_beamsplitter.filename = fname
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
        """ Create dimensions for the hdf5 file transmission data. """
        self.logger.info(f'creating dimensions for {self.experiment} data')
        self.dataset.createDimension('xy_position', 2)
        self.dataset.createDimension('emission_wavelengths', len(self.instruments['spectrometer'].wavelengths))
        self.dataset.createDimension('spectrometer_intervals',
                                     self.instruments['spectrometer'].average_measurements * 2)
        self.dataset.createDimension('single', 1)

    def _create_dimensions_excitation_emission(self):
        """ Create dimensions for the hdf5 file excitation emission data. """
        self.logger.info(f'creating dimensions for {self.experiment} data')
        self.dataset.createDimension('xy_position', 2)
        self.dataset.createDimension('emission_wavelengths', len(self.instruments['spectrometer'].wavelengths))
        self.dataset.createDimension('spectrometer_intervals',
                                     self.instruments['spectrometer'].average_measurements * 2)
        self.dataset.createDimension('single', 1)
        excitation_wavelenghts = len(np.unique(self.measurement_parameters['wl'][1:]))
        self.dataset.createDimension('excitation_wavelengths', excitation_wavelenghts)
        self.dataset.createDimension('power_measurements', self.instruments['powermeter'].measurements_multiple)

    def _create_dimensions_decay(self):
        """ Create dimensions for the hdf5 file decay data. """
        self.logger.info(f'creating dimensions for {self.experiment} data')
        self.dataset.createDimension('xy_position', 2)
        self.dataset.createDimension('single', 1)
        excitation_wavelenghts = len(np.unique(self.measurement_parameters['wl'][:]))
        self.dataset.createDimension('excitation_wavelengths', excitation_wavelenghts)
        samples = int(self.instruments['digitizer'].record_length)
        self.dataset.createDimension('samples', samples)

    # endregion
    # region prepare measurement

    def _prepare_measurement(self):
        """
        Prepare for the next measurement. This involves setting instruments to new values
        such as moving the xy stages or changing the laser wavelength. Some instrument signals
        are connected to the following 'measure' trigger of the statemachine.
        Therefore timing cannot be done with @timed function.
        """
        self.timekeeper = time.time()
        self.logger.info('prepare measurement routine started')
        if self.calibration:
            self._prepare_measurement_calibration()
        elif self.experiment == 'transmission':
            self._prepare_measurement_transmission()
        elif self.experiment == 'excitation_emission':
            self._prepare_measurement_excitation_emission()
        elif self.experiment == 'decay':
            self._prepare_measurement_decay()

    def _prepare_measurement_calibration(self):
        """ Set the laser and powermeter to the correct wavelength """
        self.logger.info(f'preparing beamsplitter calibration measurement {self.measurement_index} of '
                         f'{len(self.measurement_parameters)}')
        self._prepare_powermeter()
        self._control_shutter()
        self._prepare_laser()

    def _prepare_measurement_transmission(self):
        """ Prepare measurement transmission. For transmission this only involved moving the xy stages. """
        self.logger.info(f"preparing {self.experiment} measurement {self.measurement_index} of "
                         f"{len(self.measurement_parameters['x'])}")
        self._prepare_move_stage()

    def _prepare_measurement_excitation_emission(self):
        """ Prepare measurement excitation emission. """
        self.logger.info(f"preparing {self.experiment} measurement {self.measurement_index} of "
                         f"{len(self.measurement_parameters['x'])}")
        self.wait_signals_prepare_measurement.reset()
        self._prepare_powermeter()
        self._control_shutter()
        self._prepare_laser()
        self._prepare_move_stage()

    def _prepare_measurement_decay(self):
        self.logger.info(f"preparing {self.experiment} measurement {self.measurement_index} of "
                         f"{len(self.measurement_parameters['x'])}")
        self.wait_signals_prepare_measurement.reset()
        self._control_shutter()
        self._prepare_digitizer()
        self._prepare_laser()
        self._prepare_move_stage()

    def _prepare_move_stage(self):
        """ Move the stages to the next position. Set the setpoints, then call move to setpoints. """
        try:
            x = self.measurement_parameters['x'][self.measurement_index]
            y = self.measurement_parameters['y'][self.measurement_index]
            self.logger.info(f'moving stages to x = {x}, y = {y}')
            self.instruments['xystage'].setpoint_x = x
            self.instruments['xystage'].setpoint_y = y
            QTimer.singleShot(0, self.instruments['xystage'].move_to_setpoints)
        except IndexError as e:
            self.logger.error(f'position index out of range {e}')
            raise IndexError

    def _control_shutter(self):
        """
        Enable shutter except when a dark measurement is taken,
        which is only during excitation emission experiments.
        """
        if self.measurement_index == 0 and self.experiment == 'excitation_emission' and not self.calibration:
            self.logger.info('disabling shutter for dark measurement')
            self.instruments['shuttercontrol'].disable()
        else:
            self.logger.info('enabling shutter enabled')
            self.instruments['shuttercontrol'].enable()

    def _prepare_powermeter(self):
        """
        Set the powermeter to the new laser wavelength.
        At the first measurement, or at any new position during excitation,
        close the shutter and zero the powermeter to get the same starting power.
        """
        wl = self.measurement_parameters['wl'][self.measurement_index]
        self.logger.info(f'setting powermeter to {wl} nm')
        self.instruments['powermeter'].wavelength = wl

        if self._requires_zeroing():
            self.instruments['shuttercontrol'].disable()
            self.instruments['powermeter'].zero()

    def _requires_zeroing(self):
        """
        Determine if the powermeter needs to be zero'd before each measurement. This is necessary if there is more
        than one excitation wavelength, when the xystage moves to a new position. As there is always a specific
        wavelength set for the dark spectrum, excitation happens when number of wavelengths is larger than 2.
        """
        idx = self.measurement_index
        wavelengths = np.unique(self.measurement_parameters['wl'])

        if self.measurement_index == 0:
            self.logger.info('First measurement, zero powermeter')
            return True
        elif self.measurement_parameters['x'][idx] != self.measurement_parameters['x'][idx-1] and len(wavelengths) > 2:
            self.logger.info('New x posisition, zero powermeter')
            return True
        elif self.measurement_parameters['y'][idx] != self.measurement_parameters['y'][idx-1] and len(wavelengths) > 2:
            self.logger.info('New y position, zero powermeter')
            return True
        else:
            return False


    def _prepare_digitizer(self):
        """ Clear the average measurements from the digitizer. """
        self.logger.info('clearing digitizer for new measurement')
        self.instruments['digitizer'].clear_measurement()

    def _prepare_laser(self):
        """
        Set the a new setpoint for the laser wavelength and call the set to setpoint method in the laser thread.
        """
        wl = self.measurement_parameters['wl'][self.measurement_index]
        self.logger.info(f'setting laser to {wl} nm for next measurement')
        self.instruments['laser'].setpoint_wavelength = wl
        QTimer.singleShot(0, self.instruments['laser'].set_wavelength_to_setpoint)

    # endregion

    # region measure

    def _measure(self):
        """
        Perform the actual measurements on the instruments. Since these are threaded processes, can't time the
        function but must time when the next process starts.
        """
        self.logger.info('measure routine started')
        time_measuring = time.time() - self.timekeeper
        self.measurement_duration += time_measuring
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
        self.instruments['powermeter'].plotinfo = f'Power Calibration at Position {self.calibration_position}, ' \
                                                  f'wavelength {self.measurement_index + 1} of {wlnum} ({wl} nm)'
        QTimer.singleShot(0, self.instruments['powermeter'].measure)

    def _measure_transmission(self):
        """
        Measure the spectrometer.
        The first measurement is a dark measurement, the second one a lamp measurement. The next spectra are all
        transmission spectra.

        The plotinfo attribute of the spectrometer needs to be set prior to calling the measure function.
        """
        if self.measurement_index == 0:
            self.logger.info('Measuring dark spectrum transmission experiment')
            QTimer.singleShot(0, self.instruments['spectrometer'].measure_dark)
        elif self.measurement_index == 1:
            self.logger.info('Measuring lamp spectrum transmission experiment')
            QTimer.singleShot(0, self.instruments['spectrometer'].measure_lamp)
        else:
            x_inx, y_iny = self._variable_index()
            xnum = len(np.unique(self.measurement_parameters['x'][2:]))
            ynum = len(np.unique(self.measurement_parameters['y'][2:]))
            self.logger.info(f'Transmission Spectrum. X = {x_inx + 1} of {xnum}, Y = {y_iny + 1} of {ynum}')
            self.instruments['spectrometer'].plotinfo = f'Transmission Spectrum - X = {x_inx + 1} of {xnum}, ' \
                                                        f'Y = {y_iny + 1} of {ynum}'
            self.instruments['spectrometer'].set_transmission()
            QTimer.singleShot(0, self.instruments['spectrometer'].measure)

    def _measure_excitation_emission(self):
        """
        Measure the spectrometer. 'Cache cleared' signal of spectrometer
        is connected to the powermeter such that power measurement starts when cache is cleared.

        First measurement is a dark measurement.
        """
        if self.measurement_index == 0:
            self.logger.info('Measuring dark spectrum excitation emission experiment')
            QTimer.singleShot(0, self.instruments['spectrometer'].measure_dark)
        else:
            x_inx, y_iny, wl_inwl = self._variable_index()
            xnum = len(np.unique(self.measurement_parameters['x'][1:]))
            ynum = len(np.unique(self.measurement_parameters['y'][1:]))
            wlnum = len(np.unique(self.measurement_parameters['wl'][1:]))
            wl = self.measurement_parameters['wl'][self.measurement_index]
            self.logger.info(f'Measuring spectrum excitation emission experiment. X = {x_inx + 1} of {xnum}, '
                             f'Y = {y_iny + 1} of {ynum}\nWavelength = {wl_inwl + 1} of {wlnum} ({wl} nm)')
            self.instruments['spectrometer'].plotinfo = f'Spectrum minus dark at X = {x_inx + 1} of {xnum}, ' \
                                                        f'Y = {y_iny + 1} of {ynum}, ' \
                                                        f'Wavelength = {wl_inwl + 1} of {wlnum} ({wl} nm)'
            QTimer.singleShot(0, self.instruments['spectrometer'].measure)

    def _measure_decay(self):
        """ Call the measure function of the digitizer with relevant plotinfo. """
        x_inx, y_iny, wl_inwl = self._variable_index()
        xnum = len(np.unique(self.measurement_parameters['x'][:]))
        ynum = len(np.unique(self.measurement_parameters['y'][:]))
        wlnum = len(np.unique(self.measurement_parameters['wl'][:]))
        wl = self.measurement_parameters['wl'][self.measurement_index]
        self.logger.info(f'Measuring Decay Spectrum. X = {x_inx + 1} of {xnum}, '
                         f'Y = {y_iny + 1} of {ynum}\nWavelength = {wl_inwl + 1} of {wlnum} ({wl} nm)')
        self.instruments['digitizer'].plotinfo = f'X = {x_inx + 1} of {xnum}, Y = {y_iny + 1} of {ynum} \n' \
                                                 f'Wavelength = {wl_inwl + 1} of {wlnum} ({wl} nm)'
        QTimer.singleShot(0, self.instruments['digitizer'].measure)

    # endregion

    # region process data
    @timed
    def _process_data(self):
        """ Currently an empty method but can be used to do any type of data processing before writing data to file. """
        time_measuring = time.time() - self.timekeeper
        self.measurement_duration += time_measuring
        self.logger.info(f'processing data {self.experiment}, measurement time = {time_measuring}')
        self.write_file()

    # endregion

    # region write file

    @timed
    def _write_file(self):
        """ Routine for writing the measurement data to file. """
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
        self.logger.info(f"writing power to calibration csv, position = {self.calibration_position}, "
                         f"wl = {self.measurement_parameters['wl'][self.measurement_index]}")
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
        Make folders for each measurement position. Separate dark spectrum folder and lamp spectrum folder. Transmission
        has only one measurement per position so folders need to be created for every measurement.
        """
        if self.measurement_index == 0:
            self.logger.info('creating folder for dark spectrum and writing data')
            datagroup = self.dataset.createGroup('dark')
        elif self.measurement_index == 1:
            self.logger.info('creating folder for lamp spectrum and writing data')
            datagroup = self.dataset.createGroup('lamp')
        else:
            x_inx, y_iny = self._variable_index()
            self.logger.info(f'creating folder for xidx = {x_inx} and yidx = {y_iny}')
            datagroup = self.dataset.createGroup(f'x{x_inx + 1}y{y_iny + 1}')

        xy_pos, em_wl, spectrum, spectrum_t = self._create_variables_transmission(datagroup)

        xy_pos[:] = self._write_position()
        em_wl[:] = self.instruments['spectrometer'].wavelengths
        spectrum[:] = self.instruments['spectrometer'].last_intensity
        spectrum_t[:] = np.array(self.instruments['spectrometer'].last_times) - self.startingtime

    def _write_file_excitation_emission(self):
        """
        Write the measured spectrum and power to file.
        Data is organized in folders per measurement position. Multiple excitation wavelengths are stored
        in the same position folder. Therefore check if folder is there, otherwise create it. Also separate folder for
        dark spectrum.
        """
        if self.measurement_index == 0:
            self.logger.info('creating dark spectrum folder for writing data')
            datagroup = self.dataset.createGroup('dark')
        else:
            x_inx, y_iny, wl_in_wl = self._variable_index()
            # check if folder with position index exists, otherwise create it
            try:
                datagroup = self.dataset[f'x{x_inx + 1}y{y_iny + 1}']
                self.logger.info(f'folder xidx {x_inx}, yidx {y_iny}, wlidx {wl_in_wl} exists, writing data '
                                 f'to existing folder')
            except IndexError:
                self.logger.info(f'folder xidx {x_inx}, yidx {y_iny}, wlidx {wl_in_wl} doesnt exist, creating folder '
                                 f'and writing data')
                datagroup = self.dataset.createGroup(f'x{x_inx + 1}y{y_iny + 1}')
        # check if variables exist, otherwise create them
        try:
            xy_pos = datagroup['position']
            em_wl = datagroup['emission']
            spectrum = datagroup['spectrum']
            spectrum_t = datagroup['spectrum_t']
            ex_wl = datagroup['excitation']
            t_power = datagroup['power_t']
            power = datagroup['power']
            self.logger.info('variables exist in folder, appending data to variables')
        except IndexError:
            self.logger.info('variables non-existent in current folder, creating variables')
            xy_pos, em_wl, spectrum, spectrum_t, ex_wl, t_power, power = \
                self._create_variables_excitation_emission(datagroup)

        # write data to variables with distinction between first measurement (dark spectrum) and the rest.
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
        """
        Write the measured decay spectrum to a file.
        Data again sorted in folders per position. Check if folder exists, otherwise create it.
        """
        x_inx, y_iny, wl_in_wl = self._variable_index()
        # check if folder with position index exists, otherwise create it
        try:
            datagroup = self.dataset[f'x{x_inx + 1}y{y_iny + 1}']
            self.logger.info(f'folder xidx {x_inx}, yidx {y_iny}, wlidx {wl_in_wl} exists, writing data '
                             f'to existing folder')
        except IndexError:
            self.logger.info(f'folder xidx {x_inx}, yidx {y_iny}, wlidx {wl_in_wl} doesnt exist, creating folder '
                             f'and writing data')
            datagroup = self.dataset.createGroup(f'x{x_inx + 1}y{y_iny + 1}')
        try:
            xy_pos = datagroup['position']
            ex_wl = datagroup['excitation']
            pulses = datagroup['pulses']
            self.logger.info('variables exist in folder, appending to variables')
        except IndexError:
            self.logger.info('variables dont exist, create variables')
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
            self.logger.info(f'creating indexes for data file for x = {x}, y = {y} and wl = {wl}')
            wl_in_wls = list(np.unique(self.measurement_parameters['wl'][paramdict[self.experiment]:])).index(wl)
            return x_inx, y_iny, wl_in_wls
        else:
            self.logger.info(f'creating indexes for data file for x = {x}, y = {y}.')
            return x_inx, y_iny

    def _create_variables_transmission(self, datagroup):
        """ Create variable for the transmission data. """
        self.logger.info('creating variables for transmission data')
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
        """ Create variable for the excitation emission data. """
        self.logger.info('creating variables for excitation emission data')
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

    def _create_variables_decay(self, datagroup):
        """ Create variable for the decay data. """
        self.logger.info('create variables for the decay data')
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
        """ Get the x and y position"""
        keep_trying = 5
        while keep_trying:
            failed = False
            try:
                x, y = [self.instruments['xystage'].x, self.instruments['xystage'].y]
                self.logger.info('getting position values to write to data file')
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
        - Emit progress and completion time

        - Depending on the conditions, following calls at the end:
            Notify user calibration is halfway
            Calibration or experiment complete
            Prepare next measurement step.
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
            self.logger.info('Part one of calibration complete, prompting user')
            self.wait_for_user()
        elif progress == 1:
            self.logger.info(f'Measurement Completed at: {time.ctime(ect)}')
            self.is_done = True
            self.measurement_complete()
        else:
            self.logger.info('progress calculated, starting prepare next measurement')
            self.prepare()

    # endregion

    def _notify_user_calibration(self):
        """
        Shut the shutter so the powermeter can be put into position without burning it in the focal point.
        Emit signal which opens the dialog prompting the user to change the position of the power sensor.
        Set position attribute to two, reset measurement index.
        """
        self.logger.info('First part of beamsplitter calibration complete')
        self.instruments['shuttercontrol'].disable()
        self.measurement_index = 0
        self.calibration_position = 2
        self.calibration_half_signal.emit()

    def _return_setexperiment(self):
        """ Emit signal to the main gui to switch back to the set experiment layout. """
        self.logger.info('emitting return setexperiment signal')
        self.signal_return_setexperiment.emit()

    def _measurement_aborted(self):
        """
        Abort automated measurement routine. Close datasets, stop motors, reset instruments and call the finish
        experiment triggers.
        """
        self.logger.warning('experiment aborted')
        if not self.calibration:
            self.dataset.close()
        else:
            self.calibration_complete_signal.emit()
        # QTimer.singleShot(0, self.instruments['xystage'].stop_motors)
        self.reset_instruments()
        self.is_done = True
        self.finish_experiment()
        self.return_setexperiment()

    def _measurement_completed(self):
        """ Measurement completed. Close datasets, reset instuments. """
        self.logger.info('measurement completed!')
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
            self.logger.info('calibration done - resetting instruments for align mode')
            self.instruments['powermeter'].integration_time = 200
            self.instruments['powermeter'].plotinfo = None
            self.instruments['laser'].energylevel = 'Off'
            self.instruments['shuttercontrol'].disable()
        elif self.experiment == 'transmission':
            self.logger.info(f'{self.experiment} done - resetting instruments for align mode')
            self.instruments['spectrometer'].plotinfo = None
        elif self.experiment == 'excitation_emission':
            self.logger.info(f'{self.experiment} done - resetting instruments for align mode')
            self.instruments['spectrometer'].plotinfo = None
            self.instruments['spectrometer'].cache_cleared.disconnect()
            self.instruments['powermeter'].plotinfo = None
            self.instruments['powermeter'].integration_time = 200
            self.instruments['laser'].energylevel = 'Off'
        elif self.experiment == 'decay':
            self.logger.info(f'{self.experiment} done - resetting instruments for align mode')
            self.instruments['digitizer'].polltime = self.polltime
            self.instruments['digitizer'].pulses_per_measurement = math.ceil(self.polltime * 101)
            self.instruments['digitizer'].polltime_enabled = True
            self.instruments['digitizer'].plotinfo = None
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
