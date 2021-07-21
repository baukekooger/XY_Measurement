from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QThread, pyqtSlot
from gui_design.main import Ui_MainWindow
from yaml import safe_load as yaml_safe_load, dump
from experiments.statemachine import StateMachine
import time
import datetime


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

        self.ui.pushButton_transmission.clicked.connect(lambda state, page=0: self.choose_experiment(page))
        self.ui.pushButton_excitation_emission.clicked.connect(lambda state, page=1: self.choose_experiment(page))
        self.ui.pushButton_decay.clicked.connect(lambda state, page=2: self.choose_experiment(page))
        self.ui.pushButton_return.clicked.connect(self.return_home)
        self.ui.pushButton_start_experiment.clicked.connect(self.start_experiment)
        self.ui.pushButton_start_experiment.setEnabled(False)
        self.ui.pushButton_alignment_experiment.clicked.connect(self.alignment_experiment)
        self.statemachine.signal_return_setexperiment.connect(self.reset_setexperiment)
        self.statemachine.ect.connect(self.update_completion_time)
        self.statemachine.progress.connect(self.update_progress)

    def choose_experiment(self, page):
        self.experiment = self.config['experiments'][page]
        self.statemachine.choose_experiment(page)
        self.define_threads()
        self.move_to_threads()
        self.start_threads()
        self.add_instruments_to_guis()
        self.fill_ui()
        self.statemachine.align()
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
            thread.start()

    def add_instruments_to_guis(self):
        # adds the threaded instruments from the statemachine to the relevant widgets
        for widget, inst in self.config['widgets'][self.experiment].items():
            if 'file' not in widget:
                widget_set = getattr(self.ui, widget)
                setattr(widget_set, inst, self.statemachine.instruments[inst])
                widget_set.connect_signals_slots()

    def quit_all_threads(self):
        self.statemachineThread.quit()
        for _, thread in self.threads.items():
            thread.quit()
        self.ui.stackedWidget_experiment.setEnabled(True)
        self.ui.stackedWidget.setEnabled(True)

    def return_home(self):
        # add something that quits all threads from the experiment such that a new experiment can be done
        self.store_ui()
        self.alignment_experiment_gui()
        self.statemachine.return_home()
        self.ui.stackedWidget.setCurrentIndex(0)

    def alignment_experiment(self):
        # finalize the current statemachine and load the new statemachine.
        self.statemachine.align_experiment()
        self.alignment_experiment_gui()

    def alignment_experiment_gui(self):
        # sets the correct instrument widget page and adjusts size policy to
        # the new page
        stateconfig = self.config['instrument_pages'][self.statemachine.state]
        for inst in self.config['widgets'][self.experiment].keys():
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

    def store_ui(self):
        # writes widget settings for current experiment to file, overwrites previous settings for that experiment
        with open('settings_ui.yaml') as f:
            settings = yaml_safe_load(f)
        settings[self.experiment] = {}
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
                        settings[self.experiment][widget_inst][key] = widgethandle.currentIndex()
                    elif isinstance(widget_value, (QtWidgets.QPlainTextEdit, QtWidgets.QTextEdit)):
                        widgethandle = getattr(widget.ui, key)
                        settings[self.experiment][widget_inst][key] = widgethandle.toPlainText()
                    elif isinstance(widget_value, QtWidgets.QCheckBox):
                        widgethandle = getattr(widget.ui, key)
                        settings[self.experiment][widget_inst][key] = widgethandle.isChecked()
        with open('settings_ui.yaml', 'w') as f:
            dump(settings, f)

    def fill_ui(self):
        # fills the user interface with the last values known for that experiment.
        with open('settings_ui.yaml') as f:
            settings = yaml_safe_load(f)
        try:
            for widget in settings[self.experiment].keys():
                widget_handle = getattr(self.ui, widget)
                for subwidgetkey, value in settings[self.experiment][widget].items():
                    subwidgethandle = getattr(widget_handle.ui, subwidgetkey)
                    if isinstance(subwidgethandle, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                        subwidgethandle.setValue(value)
                    elif isinstance(subwidgethandle, QtWidgets.QLineEdit):
                        subwidgethandle.setText(value)
                    elif isinstance(subwidgethandle, QtWidgets.QComboBox):
                        subwidgethandle.setCurrentIndex(value)
                    elif isinstance(subwidgethandle, (QtWidgets.QPlainTextEdit, QtWidgets.QTextEdit)):
                        subwidgethandle.setPlainText(value)
                    elif isinstance(subwidgethandle, QtWidgets.QCheckBox):
                        subwidgethandle.setChecked(value)
        except AttributeError as e:
            print(f"Can't load UI, UI configuration has been modified. {e}")

    @pyqtSlot(bool)
    def set_spectrometeraxes(self, set_transmissionaxes):
        self.ui.widget_spectrometerplot_transmission.set_transmissionaxes = set_transmissionaxes

    def start_experiment(self):
        # check if motors are homed, issue warning otherwise.
        # then store ui settings and disable buttons that should not be pressed when experiment is run.
        self.statemachine.instruments['xystage'].measure()
        if not all([self.statemachine.instruments['xystage'].xhomed, self.statemachine.instruments['xystage'].xhomed]):
            QtWidgets.QMessageBox.information(self, 'homing warning', 'not all stages homed, wait for home to complete')
            self.statemachine.instruments['xystage'].home()
        else:
            self.store_ui()
            self.ui.pushButton_start_experiment.setText('Stop')
            self.ui.pushButton_alignment_experiment.setDisabled(True)
            self.ui.pushButton_start_experiment.disconnect()
            self.ui.pushButton_start_experiment.clicked.connect(self.abort_experiment)
            self.statemachine.run_experiment()

    def abort_experiment(self):
        self.ui.stackedWidget_experiment.setDisabled(True)
        self.ui.pushButton_start_experiment.setDisabled(True)
        self.ui.pushButton_alignment_experiment.setDisabled(True)
        self.ui.pushButton_return.setDisabled(True)
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

    @pyqtSlot(float)
    def update_progress(self, progress):
        self.ui.progressBar.setValue(progress)

    @pyqtSlot(float)
    def update_completion_time(self, ect):
        self.ui.label_completion_time.setText(f'Estimated completion time {datetime.timedelta(seconds=ect)}')


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
