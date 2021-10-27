import logging
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QThread, pyqtSlot
from gui_design.main import Ui_MainWindow
from yaml import safe_load as yaml_safe_load, dump
from statemachine.statemachine import StateMachine
import time
import datetime


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Init mainwindow')
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.stackedWidget.setCurrentIndex(0)

        with open('config_main.yaml') as f:
            self.config = yaml_safe_load(f)

        self.threads = {}
        self.statemachine = StateMachine()
        self.statemachineThread = QThread()
        self.statemachine.moveToThread(self.statemachineThread)
        self.statemachineThread.start()
        self.statemachine.start()
        self.experiment = None
        self.connect_signals()
        self.beamsplitter = None
        self.filedir_calibration = None

    def connect_signals(self):
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

    def choose_experiment(self, page):
        self.experiment = self.config['experiments'][page]
        self.statemachine.choose_experiment(page)
        self.define_threads()
        self.move_to_threads()
        self.start_threads()
        self.add_instruments_to_guis()
        self.connect_signals_gui()
        self.connect_position_layout_plot()
        self.fill_ui()
        self.statemachine.align()
        self.alignment_experiment_gui()
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.stackedWidget_experiment.setCurrentIndex(page)

    def define_threads(self):
        instruments_threads = self.config['instruments'][self.experiment]
        to_quit = [inst for inst in self.threads.keys() if (inst not in instruments_threads)]
        to_add = [inst for inst in instruments_threads if (inst not in self.threads.keys())]
        for inst in to_quit:
            self.threads[inst].quit()
        for inst in to_add:
            self.threads[inst] = QThread()

    def move_to_threads(self):
        for inst in self.threads.keys():
            if not self.threads[inst].isRunning():
                self.statemachine.instruments[inst].moveToThread(self.threads[inst])

    def start_threads(self):
        for _, thread in self.threads.items():
            if not thread.isRunning():
                thread.start()

    def add_instruments_to_guis(self):
        # adds the threaded instruments from the statemachine to the relevant widgets
        for widget, inst in self.config['widgets'][self.experiment].items():
            if 'file' not in widget:
                widget_set = getattr(self.ui, widget)
                setattr(widget_set, inst, self.statemachine.instruments[inst])

    def connect_signals_gui(self):
        for widget, inst in self.config['widgets'][self.experiment].items():
            widget_set = getattr(self.ui, widget)
            widget_set.connect_signals_slots()
            if 'plot' in widget:
                self.ui.pushButton_fit_plots_to_screen.clicked.connect(widget_set.fit_plots)

    def disconnect_signals_gui(self):
        # disconnects the signals from the guis so they don't get doubly connected when rechoosing experiment
        for widget, inst in self.config['widgets'][self.experiment].items():
            widget_set = getattr(self.ui, widget)
            widget_set.disconnect_signals_slots()
        self.ui.pushButton_fit_plots_to_screen.clicked.disconnect()

    def quit_all_threads(self):
        self.statemachineThread.quit()
        for _, thread in self.threads.items():
            thread.quit()
        self.ui.stackedWidget_experiment.setEnabled(True)
        self.ui.stackedWidget.setEnabled(True)

    def return_home(self):
        # add something that quits all threads from the experiment such that a new experiment can be done
        self.store_ui()
        # self.alignment_experiment_gui()
        self.statemachine.return_home()
        QTimer.singleShot(300, self.disconnect_signals_gui)
        self.ui.stackedWidget.setCurrentIndex(0)

    def alignment_experiment(self):
        # finalize the current statemachine and load the new statemachine.
        self.statemachine.align_experiment()
        self.store_ui()
        self.handle_position_layout_plot()
        self.alignment_experiment_gui()

    def alignment_experiment_gui(self):
        # sets the correct instrument widget page and adjusts size policy to
        # the new page based on the current state of the statemachine.
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
        # writes widget settings for current experiment to file, overwrites previous settings for that experiment
        with open('settings_ui.yaml') as f:
            settings = yaml_safe_load(f)
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

        with open('settings_ui.yaml', 'w') as f:
            dump(settings, f)

    def fill_ui(self):
        # fills the user interface with the last values known for that experiment
        with open('settings_ui.yaml') as f:
            settings = yaml_safe_load(f)
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

    @pyqtSlot(bool)
    def set_spectrometeraxes(self, set_transmissionaxes):
        self.ui.widget_spectrometerplot_transmission.set_transmissionaxes = set_transmissionaxes

    def connect_position_layout_plot(self):
        # signals from xy stage widget
        widget = getattr(self.ui, f'widget_xystage_{self.experiment}')
        widget.ui.spinBox_x_num.valueChanged.connect(self.handle_position_layout_plot)
        widget.ui.spinBox_y_num.valueChanged.connect(self.handle_position_layout_plot)
        widget.ui.spinBox_x_off_left.valueChanged.connect(self.handle_position_layout_plot)
        widget.ui.spinBox_x_off_right.valueChanged.connect(self.handle_position_layout_plot)
        widget.ui.spinBox_y_off_bottom.valueChanged.connect(self.handle_position_layout_plot)
        widget.ui.spinBox_y_off_top.valueChanged.connect(self.handle_position_layout_plot)
        # signal from file widget (substrate change)
        widgetfile = getattr(self.ui, f'widget_file_{self.experiment}')
        widgetfile.ui.comboBox_substrate.currentTextChanged.connect(self.handle_substrate_layout)
        self.init_layout_plot()

    def handle_position_layout_plot(self):
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
        # sets the substrate and experiment attribute of the layout plot after choosing a measurement
        widgetplot = getattr(self.ui, f'widget_xystageplot_{self.experiment}')
        widgetplot.experiment = self.experiment
        widgetfile = getattr(self.ui, f'widget_file_{self.experiment}')
        substrate = widgetfile.ui.comboBox_substrate.currentText()
        widgetplot.substrate = substrate

    @pyqtSlot(str)
    def handle_substrate_layout(self, substrate):
        QtWidgets.QMessageBox.information(self, 'substrateholder changed', f'Changing substrateholder to '
                                        f'{substrate}, please make sure the substrateholder is mounted correctly')
        widgetplot = getattr(self.ui, f'widget_xystageplot_{self.experiment}')
        widgetplot.substrate = substrate
        if self.statemachine.state == 'setExperiment':
            self.handle_position_layout_plot()

    def start_experiment(self):
        # pop up with ask if the sampleholder is mounted in the correct position
        if not self._messagebox_substratecheck():
            return
        # check if motors are homed, issue warning otherwise.
        # then store ui settings and disable buttons that should not be pressed when experiment is run.
        self.statemachine.instruments['xystage'].measure_homing()
        if not all([self.statemachine.instruments['xystage'].xhomed, self.statemachine.instruments['xystage'].xhomed]):
            QtWidgets.QMessageBox.information(self, 'homing warning', 'not all stages homed, wait for home to complete')
            self.statemachine.instruments['xystage'].home()
        else:
            print(self.ui.widget_digitizer_decay.ui.listWidget_channels_experiment.selectedItems()[0].text())
            print(self.experiment)
            if self.experiment == 'decay' and not any(self.ui.widget_digitizer_decay.ui.listWidget_channels_experiment.selectedItems()):
                print(self.ui.widget_digitizer_decay.ui.listWidget_channels_experiment.selectedItems())
                if not self._messagebox_digitizer_channel_selected():
                    return
            self.start_experiment_ui()
            # reset spectrometer settings
            if self.experiment in ['transmission', 'excitation_emission']:
                widget_spectrometer = getattr(self.ui, f'widget_spectrometer_{self.experiment}')
                widget_spectrometer.handle_reset()
            self.statemachine.init_experiment()

    def start_experiment_ui(self):
        self.store_ui()
        self.ui.pushButton_start_experiment.setText('Stop')
        self.ui.pushButton_alignment_experiment.setDisabled(True)
        self.ui.stackedWidget_experiment.setDisabled(True)
        self.ui.pushButton_start_experiment.disconnect()
        self.ui.pushButton_start_experiment.clicked.connect(self.abort_experiment)

    def _messagebox_substratecheck(self):
        widgetfile = getattr(self.ui, f'widget_file_{self.experiment}')
        substratename = widgetfile.ui.comboBox_substrate.currentText()
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.Question)
        msgbox.setText(f'Selected substrateholder for {substratename}. Is this the correct holder and is '
                       f'the holder mounted in the right position?')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
        msgbox.setWindowTitle('check substrateholder')
        answer = msgbox.exec_()
        if answer == QtWidgets.QMessageBox.Yes:
            self.ui.widget_digitizer_decay.ui.listWidget_channels_experiment.setCurrentRow(0)
            return True
        if answer == QtWidgets.QMessageBox.No:
            return False

    def _messagebox_digitizer_channel_selected(self):
        if not any(self.ui.widget_digitizer_decay.ui.listWidget_channels_alignment.selectedItems()):
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setText(f'No channel(s) selected for digitizer.\n'
                           f'Press ok to continue with default channel (channel 0)')
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msgbox.setWindowTitle('No channels selected')
            answer = msgbox.exec_()
            if answer == QtWidgets.QMessageBox.Ok:
                return True
            if answer == QtWidgets.QMessageBox.Cancel:
                return False

    def new_beamsplitter_calibration(self):
        """ performs check if calibration can be started.
            Asks for user input on file name, and stores ui settings
            Calls statemachine start of calibration procedure
            """
        if not self._messagebox_calibrationcheck():
            return
        beamsplitters = ['BS20WR', 'Other Type']
        self.statemachine.beamsplitter, ok = QtWidgets.QInputDialog.getItem(self, 'beamsplitter',
                                    'please choose beamsplitter type or edit if type not available', beamsplitters)
        if not ok:
            return
        self.statemachine.storage_dir_calibration = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if not self.statemachine.storage_dir_calibration:
            return
        QtWidgets.QMessageBox.information(self, 'move powermeter', 'place powermeter in first position'
                                                                   '(in line with laser beam)')
        self.start_experiment_ui()
        QTimer.singleShot(0, self.statemachine.start_calibration)

    def beamsplitter_calibration_half(self):
        self.reset_progress()
        if not self._messagebox_calibrationhalfway():
            self.beamsplitter_calibration_complete()
            return
        else:
            QTimer.singleShot(0, self.statemachine.continue_calibration)

    def beamsplitter_calibration_complete(self):
        self.reset_setexperiment()
        self.reset_progress()
        self.ui.lineEdit_beamsplitter_calibration_file.setText(self.statemachine.beamsplitter_fname)

    def select_beamsplitter_calibration_file(self):
        file = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Calibration File', '*.csv')[0]
        self.ui.lineEdit_beamsplitter_calibration_file.setText(file)

    def _messagebox_calibrationcheck(self):
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
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setText(f'Calibration measurement at position 1 done. Move powermeter to '
                       f'position 2, then press ok. (position 2 is below sampleholder)')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.setWindowTitle('Beamsplitter calibration halfway')
        answer = msgbox.exec_()
        if answer == QtWidgets.QMessageBox.Ok:
            return True
        else:
            return False

    def abort_experiment(self):
        self.ui.stackedWidget_experiment.setDisabled(True)
        self.ui.pushButton_start_experiment.setDisabled(True)
        self.ui.pushButton_alignment_experiment.setDisabled(True)
        self.ui.pushButton_return.setDisabled(True)
        self.reset_progress()
        self.statemachine.abort()

    def reset_setexperiment(self):
        self.ui.pushButton_start_experiment.disconnect()
        self.ui.pushButton_start_experiment.clicked.connect(self.start_experiment)
        self.ui.pushButton_start_experiment.setText('Start')
        self.ui.pushButton_alignment_experiment.setEnabled(True)
        self.ui.stackedWidget_experiment.setEnabled(True)
        self.ui.pushButton_start_experiment.setEnabled(True)
        self.ui.pushButton_return.setEnabled(True)

    def experiment_finished(self):
        print('the experiment has finished')
        self.ui.pushButton_return.setEnabled(True)

    def closeEvent(self, event):
        self.ui.centralwidget.setDisabled(True)
        # QtWidgets.QMessageBox.information(self, 'Closing Application', 'Disconnecting all instruments, '
        #                                                                'closing application')
        if self.statemachine.state == 'align':
            self.alignment_experiment()
            time.sleep(self.statemachine.polltime)
        self.statemachine.abort()
        self.statemachine.disconnect_all()
        self.quit_all_threads()
        print('done closing')
        event.accept()

    @pyqtSlot(int)
    def update_progress(self, progress):
        self.ui.progressBar.setValue(progress)
        if progress == 100 and self.statemachine.state not in ['calibrateBeamsplitterPosition1',
                                                               'calibrateBeamsplitterPosition2']:
            self.show_complete()

    def show_complete(self):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)

        msg.setText("Measurement Complete")
        msg.setInformativeText("Press ok to continue")
        msg.setWindowTitle("Completion")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.buttonClicked.connect(self.reset_progress)
        msg.exec_()

    def reset_progress(self):
        self.ui.progressBar.setValue(0)
        self.ui.label_completion_time.setText(f'Estimated completion time {datetime.timedelta(seconds=0)}')

    @pyqtSlot(int)
    def update_completion_time(self, ect):
        self.ui.label_completion_time.setText(f'Estimated completion time {datetime.timedelta(seconds=ect)}')

    @pyqtSlot(str)
    def update_status_calibration(self, status):
        self.ui.label_completion_time.setText(status)


if __name__ == '__main__':
    import yaml
    import logging.config
    with open('loggingconfig.yml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
