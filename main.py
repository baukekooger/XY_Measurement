import logging
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QThread, pyqtSlot
from gui_design.main import Ui_MainWindow
from yaml import safe_load as yaml_safe_load, dump
from statemachine.statemachine import StateMachine
import time
import datetime
from os import path


class XYSetup(QtWidgets.QMainWindow):
    """
    XY Setup

    Control class for the XY Spectroscopy Setup.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Init mainwindow')
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.stackedWidget.setCurrentIndex(0)

        with open('config/config_main.yaml') as f:
            self.config = yaml_safe_load(f)

        self.threads = {}
        self.statemachine = StateMachine()
        self.statemachineThread = QThread()
        self.statemachine.moveToThread(self.statemachineThread)
        self.statemachineThread.start()
        self.statemachine.start()
        self.experiment = None
        self.page = None
        self.connect_signals()
        self.beamsplitter = None
        self.filedir_calibration = None

    def connect_signals(self):
        """ Connect signals of the main UI and the statemachine. """

        self.logger.info('connecting main ui button and statemachine signals')
        self.ui.pushButton_transmission.clicked.connect(lambda state, page=0: self.choose_experiment(page))
        self.ui.pushButton_excitation_emission.clicked.connect(lambda state, page=1: self.choose_experiment(page))
        self.ui.pushButton_decay.clicked.connect(lambda state, page=2: self.choose_experiment(page))
        self.ui.pushButton_return.clicked.connect(self.return_home)
        self.ui.pushButton_start_experiment.clicked.connect(self.start_experiment)
        self.ui.pushButton_start_experiment.setEnabled(False)
        self.ui.pushButton_alignment_experiment.clicked.connect(self.alignment_experiment)
        self.ui.pushButton_beamsplitter_calibration.clicked.connect(self.new_beamsplitter_calibration)
        self.ui.toolButton_beamsplitter_calibration_file.clicked.connect(self.select_beamsplitter_calibration_file)
        self.statemachine.signal_return_setexperiment.connect(self.reset_setexperiment)
        self.statemachine.ect.connect(self.update_completion_time)
        self.statemachine.progress.connect(self.update_progress)
        self.statemachine.calibration_half_signal.connect(self.beamsplitter_calibration_half)
        self.statemachine.calibration_complete_signal.connect(self.beamsplitter_calibration_complete)
        self.statemachine.calibration_status.connect(self.update_status_calibration)
        self.statemachine.init_instrument_threads.connect(self.init_instrument_threads)
        self.statemachine.instrument_connect_successful.connect(self.init_gui)
        self.statemachine.instrument_connect_failed.connect(self._messagebox_failedconnection)
        self.statemachine.enable_main_gui.connect(self.ui.centralwidget.setEnabled)

    def choose_experiment(self, page):
        """
        Choose the experiment and call the statemachine trigger to choose the measurement.
        The statemachine will try to connect the relevant instruments.
        """
        self.logger.info(f'picked experiment page {page}')
        self.experiment = self.config['experiments'][page]
        self.page = page
        self.statemachine.choose_experiment(page)

    @pyqtSlot()
    def init_instrument_threads(self):
        """
        Initialize instrument threads and the main gui.
        Called from statemachine if connection to instruments succesful, before the state change to align.
        """
        self.logger.info('initializing threads and moving instruments to threads')
        self.define_threads()
        self.move_to_threads()
        self.start_threads()

    @pyqtSlot()
    def init_gui(self):
        """
        Initialize the gui when the connection to all instruments is succesful.
        Is called after transitioning from connecting to align state.
        """
        self.logger.info('initializing main gui')
        self.set_title()
        self.add_instruments_to_guis()
        self.fill_ui()
        self.connect_signals_gui()
        self.connect_position_layout_plot()
        self.alignment_experiment_gui()
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.stackedWidget_experiment.setCurrentIndex(self.page)

    def define_threads(self):
        """
        Define a QThread for each instrument belonging to the experiment as defined in the config.main file.
        """
        instruments_threads = self.config['instruments'][self.experiment]
        self.logger.info(f'defining threads for the following instruments: {instruments_threads}')
        to_quit = [inst for inst in self.threads.keys() if (inst not in instruments_threads)]
        self.logger.info(f'quitting and removing following threads: {to_quit}')
        to_add = [inst for inst in instruments_threads if (inst not in self.threads.keys())]
        self.logger.info(f'adding the following threads: {to_add}')
        for inst in to_quit:
            self.threads[inst].quit()
            self.threads[inst].deleteLater()
            self.threads.pop(inst)
        for inst in to_add:
            self.threads[inst] = QThread()

    def move_to_threads(self):
        """ Move the instruments to their threads. """
        self.logger.info(f'moving instruments to threads. threads: {self.threads.keys()}')
        for inst in self.threads.keys():
            if not self.threads[inst].isRunning():
                self.statemachine.instruments[inst].moveToThread(self.threads[inst])

    def start_threads(self):
        """ Start the instrument threads. """
        self.logger.info('starting instrument threads')
        for _, thread in self.threads.items():
            if not thread.isRunning():
                thread.start()

    def add_instruments_to_guis(self):
        """ Add the threaded instruments to their respective widget or plot gui elements. """
        self.logger.info('adding threaded instruments to gui elements')
        for widget, inst in self.config['widgets'][self.experiment].items():
            if 'file' not in widget:
                widget_set = getattr(self.ui, widget)
                setattr(widget_set, inst, self.statemachine.instruments[inst])

    def connect_signals_gui(self):
        """ Connect the threaded instrument signals to gui widget or plot elements. """
        self.logger.info('connecting signals to gui elements')
        for widget, inst in self.config['widgets'][self.experiment].items():
            widget_set = getattr(self.ui, widget)
            widget_set.connect_signals_slots()
            if 'plot' in widget:
                self.ui.pushButton_fit_plots_to_screen.clicked.connect(widget_set.fit_plots)

    def disconnect_signals_gui(self):
        """
        Disconnect the threaded instrument signals from the gui widget or plot element
        to prevent double connections if another experiment is chosen
        """
        self.logger.info('disconnecting signals from gui elements')
        for widget, inst in self.config['widgets'][self.experiment].items():
            widget_set = getattr(self.ui, widget)
            widget_set.disconnect_signals_slots()
        self.ui.pushButton_fit_plots_to_screen.clicked.disconnect()

    def quit_all_threads(self):
        """ Quit all threads. """
        self.statemachineThread.quit()
        for _, thread in self.threads.items():
            thread.quit()
        self.ui.stackedWidget_experiment.setEnabled(True)
        self.ui.stackedWidget.setEnabled(True)

    def set_title(self):
        """ Set the title of the mainwindow. """
        self.logger.info(f'setting the title of the mainwindow to the correct experiment ({self.experiment})')
        title = 'XY Setup'
        if self.experiment == 'transmission':
            title = 'XY Transmission'
        elif self.experiment == 'excitation_emission':
            title = 'XY Excitation Emission'
        elif self.experiment == 'decay':
            title = 'XY Decay'
        self.setWindowTitle(title)

    def return_home(self):
        """
        Return to the starting screen.

        Store the ui and call return home on the statemachine. Also disconnect signals from the gui.
        """
        self.logger.info('return home button pressed')
        self.store_ui()
        self.statemachine.return_home()
        QTimer.singleShot(300, self.disconnect_signals_gui)
        self.ui.stackedWidget.setCurrentIndex(0)
        self.setWindowTitle('XY Setup')

    def alignment_experiment(self):
        """
        Switch between aligning mode and setting the experiment.

        Call the state machine align experiment, store the ui and change the gui appearance.
        """
        self.logger.info('alignment experiment button pressed')
        self.statemachine.align_experiment()
        self.store_ui()
        self.handle_position_layout_plot()
        self.alignment_experiment_gui()

    def alignment_experiment_gui(self):
        """ Set the gui to the alignment or set experiment layout based on the current state of the statemachine. """

        self.logger.info(f'changing the gui to current state ({self.statemachine.state})')
        stateconfig = self.config['instrument_pages'][self.statemachine.state]
        for inst in self.config['widgets'][self.experiment].keys():
            # changes only the instrument input widgets as they are all stacked widgets
            if not any([words in inst for words in ['plot', 'file']]):
                widget_set = getattr(self.ui, inst)
                widget_set.ui.stackedWidget.setCurrentIndex(stateconfig['page'])
                page_preffered = getattr(widget_set.ui, stateconfig['preffered'])
                page_preffered.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                             QtWidgets.QSizePolicy.Fixed)
                page_ignored = getattr(widget_set.ui, stateconfig['ignored'])
                page_ignored.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                           QtWidgets.QSizePolicy.Ignored)

        self.ui.pushButton_alignment_experiment.setText(stateconfig['text_button'])
        self.ui.pushButton_start_experiment.setEnabled(stateconfig['enable_start'])
        self.ui.groupBox_calibration_beamsplitter.setEnabled(stateconfig['beamsplitter_calibration'])
        self.ui.pushButton_beamsplitter_calibration.setText(stateconfig['text_button_beamsplitter'])

    def store_ui(self):
        """ Store the ui settings in the settings_ui.yml file. """
        self.logger.info('storing user interface in settinge_ui.yml')
        with open('config/settings_ui.yaml') as file:
            settings = yaml_safe_load(file)
        settings[self.experiment] = {}
        # store the last chosen beamsplitter calibration file
        settings['lineEdit_beamsplitter_calibration_file'] = self.ui.lineEdit_beamsplitter_calibration_file.text()
        for widget_inst in self.config['widgets'][self.experiment].keys():
            if 'plot' not in widget_inst:
                settings[self.experiment][widget_inst] = {}
                widget = getattr(self.ui, widget_inst)
                dictrep = widget.ui.__dict__
                for key, widget_value in dictrep.items():
                    if isinstance(widget_value, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                        widgethandle = getattr(widget.ui, key)
                        settings[self.experiment][widget_inst][key] = widgethandle.value()
                    elif isinstance(widget_value, QtWidgets.QLineEdit):
                        widgethandle = getattr(widget.ui, key)
                        settings[self.experiment][widget_inst][key] = widgethandle.text()
                    elif isinstance(widget_value, QtWidgets.QComboBox):
                        widgethandle = getattr(widget.ui, key)
                        settings[self.experiment][widget_inst][key] = widgethandle.currentText()
                    elif isinstance(widget_value, (QtWidgets.QPlainTextEdit, QtWidgets.QTextEdit)):
                        widgethandle = getattr(widget.ui, key)
                        settings[self.experiment][widget_inst][key] = widgethandle.toPlainText()
                    elif isinstance(widget_value, QtWidgets.QCheckBox):
                        widgethandle = getattr(widget.ui, key)
                        settings[self.experiment][widget_inst][key] = widgethandle.isChecked()
                    elif isinstance(widget_value, QtWidgets.QListWidget):
                        widgethandle = getattr(widget.ui, key)
                        items = widgethandle.selectedItems()
                        if any(items):
                            channels = [int(item.text()) for item in items]
                        else:
                            channels = []
                        settings[self.experiment][widget_inst][key] = channels

        with open('config/settings_ui.yaml', 'w') as file:
            dump(settings, file)

    def fill_ui(self):
        """ Fill the ui from a yml file. """
        self.logger.info('reading the user interface settings from settings_ui.yml')
        with open('config/settings_ui.yaml') as file:
            settings = yaml_safe_load(file)
        try:
            fname = settings['lineEdit_beamsplitter_calibration_file']
            self.ui.lineEdit_beamsplitter_calibration_file.setText(fname)
            for widget in settings[self.experiment].keys():
                widget_handle = getattr(self.ui, widget)
                for subwidgetkey, value in settings[self.experiment][widget].items():
                    subwidgethandle = getattr(widget_handle.ui, subwidgetkey)
                    if isinstance(subwidgethandle, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                        subwidgethandle.setValue(value)
                    elif isinstance(subwidgethandle, QtWidgets.QLineEdit):
                        subwidgethandle.setText(value)
                    elif isinstance(subwidgethandle, QtWidgets.QComboBox):
                        subwidgethandle.setCurrentText(value)
                    elif isinstance(subwidgethandle, (QtWidgets.QPlainTextEdit, QtWidgets.QTextEdit)):
                        subwidgethandle.setPlainText(value)
                    elif isinstance(subwidgethandle, QtWidgets.QCheckBox):
                        subwidgethandle.setChecked(value)
        except (AttributeError, KeyError) as e:
            print(f"Can't load UI, UI configuration has been modified. {e}")

    def connect_position_layout_plot(self):
        """
        Connect signals from the XYStage widget to plotting function of the XYPlot widget

        - Connect substrate changed signal from file widget to XYPlotwidget
        - Initialize the layout plot
        """
        self.logger.info('connecting the signals from the XYstage widget to XYplotwidget')
        widget = getattr(self.ui, f'widget_xystage_{self.experiment}')
        widget.ui.spinBox_x_num.valueChanged.connect(self.handle_position_layout_plot)
        widget.ui.spinBox_y_num.valueChanged.connect(self.handle_position_layout_plot)
        widget.ui.spinBox_x_off_left.valueChanged.connect(self.handle_position_layout_plot)
        widget.ui.spinBox_x_off_right.valueChanged.connect(self.handle_position_layout_plot)
        widget.ui.spinBox_y_off_bottom.valueChanged.connect(self.handle_position_layout_plot)
        widget.ui.spinBox_y_off_top.valueChanged.connect(self.handle_position_layout_plot)
        widgetfile = getattr(self.ui, f'widget_file_{self.experiment}')
        widgetfile.ui.comboBox_substrate.currentTextChanged.connect(self.handle_substrate_layout)
        self.init_layout_plot()

    def handle_position_layout_plot(self):
        """
        Handle to emit all the XYstage widget settings to the XYPlot widget
        when one of the XYstage widget changes
        """
        self.logger.info('positions plot handle called')
        widget = getattr(self.ui, f'widget_xystage_{self.experiment}')
        xnum = widget.ui.spinBox_x_num.value()
        ynum = widget.ui.spinBox_y_num.value()
        x_off_left = widget.ui.spinBox_x_off_left.value()
        x_off_right = widget.ui.spinBox_x_off_right.value()
        y_off_bottom = widget.ui.spinBox_y_off_bottom.value()
        y_off_top = widget.ui.spinBox_y_off_top.value()
        widgetplot = getattr(self.ui, f'widget_xystageplot_{self.experiment}')
        widgetplot.plot_layout(xnum, ynum, x_off_left, x_off_right, y_off_bottom, y_off_top)

    def init_layout_plot(self):
        """ Set the experiment and the substrate in the XYPlot widget. """
        self.logger.info('setting experiment and substrate in XYPlot widget')
        widgetplot = getattr(self.ui, f'widget_xystageplot_{self.experiment}')
        widgetplot.experiment = self.experiment
        widgetfile = getattr(self.ui, f'widget_file_{self.experiment}')
        substrate = widgetfile.ui.comboBox_substrate.currentText()
        widgetplot.substrate = substrate

    @pyqtSlot(str)
    def handle_substrate_layout(self, substrate):
        """
        Prompt the user that the substrate setting has changed and that they shall
        check it is mounted correctly by popping up a messagebox.
        """
        self.logger.info('substrate changed, notifiying user with messagebox')
        QtWidgets.QMessageBox.information(self, 'substrateholder changed', f'Changing substrateholder to '
                                        f'{substrate}, please make sure the substrateholder is mounted correctly')
        widgetplot = getattr(self.ui, f'widget_xystageplot_{self.experiment}')
        widgetplot.substrate = substrate
        if self.statemachine.state == 'setExperiment':
            self.handle_position_layout_plot()

    def start_experiment(self):
        """
        Start the automated measurement routine.

        - Perform checks if the automated measurement routine may be started.
        - Change the ui to experiment mode and call the statemachine init experiment trigger.
        """
        self.logger.info('start experiment button pressed, doing checks')
        if not self._directorycheck():
            return
        if not self._messagebox_substratecheck():
            return
        if not self._homingcheck():
            return
        self.logger.info('start checks passed, changing ui and starting experiment')
        self.start_experiment_ui()
        QTimer.singleShot(200, self.statemachine.init_experiment)

    def start_experiment_ui(self):
        """
        Disable most of the ui for the automated experiment routine.

        -Store the ui settings in settings.yml
        """
        self.logger.info('setting the ui for experiment mode')
        self.store_ui()
        self.ui.pushButton_start_experiment.setText('Stop')
        self.ui.pushButton_alignment_experiment.setDisabled(True)
        self.ui.pushButton_return.setDisabled(True)
        self.ui.stackedWidget_experiment.setDisabled(True)
        self.ui.pushButton_start_experiment.disconnect()
        self.ui.pushButton_start_experiment.clicked.connect(self.abort_experiment)

    def _messagebox_substratecheck(self):
        """ Make a messagebox which asks the user if the correct substrateholder is selected. """
        self.logger.info('showing messagebox substratecheck')
        widgetfile = getattr(self.ui, f'widget_file_{self.experiment}')
        substratename = widgetfile.ui.comboBox_substrate.currentText()
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.Question)
        msgbox.setText(f'Selected substrateholder for {substratename}. Is this the correct holder and is '
                       f'the holder mounted in the correct position?')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
        msgbox.setWindowTitle('check substrateholder')
        answer = msgbox.exec_()
        if answer == QtWidgets.QMessageBox.Yes:
            return True
        if answer == QtWidgets.QMessageBox.No:
            return False

    def _homingcheck(self):
        """ Perform a check if the motors are homed. """
        self.logger.info('checking if motors are homed before starting experiment')
        self.statemachine.instruments['xystage'].measure_homing()
        if not all([self.statemachine.instruments['xystage'].xhomed, self.statemachine.instruments['xystage'].xhomed]):
            self.logger.info('motors not homed, homing and notifying user')
            self._messagebox_homingcheck()
            self.statemachine.instruments['xystage'].home()
            return False
        else:
            return True

    def _messagebox_homingcheck(self):
        """ Make a messagebox informing the user the motors are not homed. """
        self.logger.info('showing messagebox motors not homed')
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setText(f'Motors not homed, please wait for homing to complete.')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
        msgbox.setWindowTitle('Wait for homing')
        msgbox.exec_()

    def new_beamsplitter_calibration(self):
        """
        Start a beamsplitter calibration
        - Perform check if calibration can be started.
        - Ask for user input on file name and store ui settings
        - Call statemachine start of calibration trigger
        """

        self.logger.info('new calibration button pressed, performing checks')
        if not self._homingcheck():
            return
        if not self._messagebox_substratecheck():
            return
        if not self._messagebox_calibrationcheck():
            return
        if not self._inputdialog_beamsplitter():
            return
        self.statemachine.storage_dir_calibration = \
            str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if not self.statemachine.storage_dir_calibration:
            return
        QtWidgets.QMessageBox.information(self, 'move powermeter', 'place powermeter in first position'
                                                                   '(in line with laser beam)')
        self.logger.info('checks passed, starting calibration procedure')
        self.start_experiment_ui()
        self.statemachine.calibration = True
        QTimer.singleShot(0, self.statemachine.init_experiment)

    def beamsplitter_calibration_half(self):
        """ Reset the progress bar, continue calibration if ok is clicked. """
        self.logger.info('beamsplitter calibration halfway')
        self.reset_progress()
        if not self._messagebox_calibrationhalfway():
            self.beamsplitter_calibration_complete()
            return
        else:
            QTimer.singleShot(0, self.statemachine.continue_experiment)

    def beamsplitter_calibration_complete(self):
        """ Calibration complete, reset ui and show popup. """
        self.logger.info('calibration completed, resetting ui')
        self.reset_setexperiment()
        self.reset_progress()
        self.ui.lineEdit_beamsplitter_calibration_file.setText(self.statemachine.calibration_fname)
        self._messagebox_calibrationcomplete()

    def select_beamsplitter_calibration_file(self):
        """ Select an existing beamsplitter calibration file. """
        self.logger.info('selecting existing calibration file')
        file = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Calibration File', '*.csv')[0]
        self.ui.lineEdit_beamsplitter_calibration_file.setText(file)

    def _directorycheck(self):
        """ Perform a check if the selected file directory exists. """
        self.logger.info('checking if file directory exists')
        widgetfile = getattr(self.ui, f'widget_file_{self.experiment}')
        directory = widgetfile.ui.lineEdit_directory.text()
        if not path.exists(directory):
            self.logger.error('selected file directory does not exist')
            self._messagebox_directorycheck()
            return False
        else:
            return True

    def _inputdialog_beamsplitter(self):
        """
        Show messagebox prompting the user to choose which beamsplitter is installed.

        Set the beamsplitter attribute of the statemachine.
        """
        self.logger.info('showing inputdialog beamsplitter')
        beamsplitters = ['BS20WR', 'BSW26R', 'Quartz', 'Other Type']
        self.statemachine.beamsplitter, ok = \
            QtWidgets.QInputDialog.getItem(self, 'beamsplitter',
                                           'please choose beamsplitter type or edit if type not available',
                                           beamsplitters)
        return ok

    def _messagebox_calibrationcheck(self):
        """
        Popup messagebox prompting the user to check if the settings for the beamsplitter
        calibration are correct.
        """
        self.logger.info('showing messagebox calibration settings check')
        wlstart = self.ui.widget_laser_excitation_emission.ui.spinBox_wavelength_start.value()
        wlstop = self.ui.widget_laser_excitation_emission.ui.spinBox_wavelength_stop.value()
        wlstep = self.ui.widget_laser_excitation_emission.ui.spinBox_wavelength_step.value()

        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.Question)
        msgbox.setText(f'New calibration requested. Current settings for calibration:\n\n    wavelength range = '
                       f'{wlstart} : {wlstop} nm\n    wavelength step = {wlstep} nm\n\n'
                       f'are these settings correct?')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
        msgbox.setWindowTitle('check beamsplitter calibration settings')
        answer = msgbox.exec_()
        if answer == QtWidgets.QMessageBox.Yes:
            return True
        if answer == QtWidgets.QMessageBox.No:
            return False

    def _messagebox_calibrationhalfway(self):
        """
        Messagebox informing the user the calibration is halfway and prompting
        them to move powermeter to position 2.
        """
        self.logger.info('messagebox calibration halfway')
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setText(f'Calibration measurement at position 1 done. Move powermeter to '
                       f'position 2, then press ok. '
                       f'Position 2 is below the sampleholder')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.setWindowTitle('Beamsplitter calibration halfway')
        answer = msgbox.exec_()
        if answer == QtWidgets.QMessageBox.Ok:
            return True
        else:
            return False

    def _messagebox_calibrationcomplete(self):
        """ Messagebox prompting the user the calibration procedure is completed. """
        self.logger.info('messagebox calibration complete')
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setText(f'Calibration completed')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.setWindowTitle('Beamsplitter calibration completed')
        answer = msgbox.exec_()
        if answer == QtWidgets.QMessageBox.Ok:
            return True
        else:
            return False

    def _messagebox_directorycheck(self):
        """ Messagebox prompting the user the selected file directory does not exist. """
        self.logger.info('messagebox directorycheck')
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setText('Invalid file directory selected, please select a valid directory')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.setWindowTitle('Invalid Directory')
        answer = msgbox.exec_()
        if answer == QtWidgets.QMessageBox.Ok:
            return True
        else:
            return False

    @pyqtSlot(dict)
    def _messagebox_failedconnection(self, errordict):
        """ Messagebox prompting the user connection between an instrument failed. """
        instrument = errordict['instrument']
        errormessage = errordict['error']
        self.logger.info(f'messagebox failed connection concerning instrument: '
                         f'{instrument}, errormessage: {errormessage}')
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.Warning)
        msgbox.setText(f"Error connecing to {instrument}. \nErrormessage: {errormessage}. \nFor the selected "
                       f"experiment, the following instruments need to be connected: "
                       f"\n{self.config['instruments'][self.experiment]}."
                       f"\nPlease check if all instruments are connected"
                       f" and turned on. \n\nTry again when check complete.")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.setWindowTitle('Connection error')
        msgbox.exec_()

    def abort_experiment(self):
        """
        Abort the currently running experiment
        - Disable remaining enabled ui buttons, reset progress bar and call statemachine abort trigger.
        """
        self.logger.info('stop button pushed')
        self.ui.stackedWidget_experiment.setDisabled(True)
        self.ui.pushButton_start_experiment.setDisabled(True)
        self.ui.pushButton_alignment_experiment.setDisabled(True)
        self.ui.pushButton_return.setDisabled(True)
        self.reset_progress()
        self.statemachine.abort()

    def reset_setexperiment(self):
        """ Reset the ui to a state where it is ready to start a new experiment. """
        self.logger.info('resetting ui to setExperiment state')
        self.ui.pushButton_start_experiment.disconnect()
        self.ui.pushButton_start_experiment.clicked.connect(self.start_experiment)
        self.ui.pushButton_start_experiment.setText('Start')
        self.ui.pushButton_alignment_experiment.setEnabled(True)
        self.ui.stackedWidget_experiment.setEnabled(True)
        self.ui.pushButton_start_experiment.setEnabled(True)
        self.ui.pushButton_return.setEnabled(True)

    def closeEvent(self, event):
        """
        Close event, called when closing the application.
        - Disable the main widget
        - Send abort signal to statemachine to disconnect all signals.
        - Disconnect all instruments (this takes time, hence the disabling of the widget)
        - Quit all threads.
        """

        self.logger.info('close event called')
        self.ui.centralwidget.setDisabled(True)
        if self.statemachine.state == 'align':
            self.alignment_experiment()
            time.sleep(self.statemachine.polltime)
        self.statemachine.abort()
        self.statemachine.disconnect_all()
        self.quit_all_threads()
        self.logger.info('close event finished')
        event.accept()

    @pyqtSlot(int)
    def update_progress(self, progress):
        """ Update the progressbar in the ui. """
        self.logger.info(f'setting progressbar to {progress}')
        self.ui.progressBar.setValue(progress)
        if progress == 100 and not self.statemachine.calibration:
            self._messagebox_experiment_completed()

    def _messagebox_experiment_completed(self):
        """ Messagebox prompting the user the experiment is completed. """
        self.logger.info('messagebox experiment completed')
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)

        msg.setText("Measurement Complete")
        msg.setInformativeText("Press ok to continue")
        msg.setWindowTitle("Completion")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.buttonClicked.connect(self.reset_progress)
        msg.exec_()

    def reset_progress(self):
        """ Reset the progressbar to 0. """
        self.logger.info('resetting progressbar')
        self.ui.progressBar.setValue(0)
        self.ui.label_completion_time.setText(f'Estimated completion time {datetime.timedelta(seconds=0)}')

    @pyqtSlot(int)
    def update_completion_time(self, ect):
        """ Set the estimated completion time in the ui. """
        self.logger.info(f'setting estimated completion time in ui to {datetime.timedelta(seconds=ect)}')
        self.ui.label_completion_time.setText(f'Estimated completion time {datetime.timedelta(seconds=ect)}')

    @pyqtSlot(str)
    def update_status_calibration(self, status):
        """ Update the calibration status """
        self.logger.info(f'setting calibration status in ui to {status}')
        self.ui.label_completion_time.setText(status)


if __name__ == '__main__':
    import yaml
    import logging.config
    import logging.handlers
    with open('logging/loggingconfig_main.yml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = XYSetup()
    window.show()
    sys.exit(app.exec_())
