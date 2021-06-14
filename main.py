from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QThread
from gui_design.main import Ui_MainWindow
from experiments.alignment_transmission import TransmissionAlignment
import time


class MainWindow(QtWidgets.QMainWindow):
    # define which experiments and instruments are present in the gui
    experiments_stacked = {
        0: 'transmission',
        1: 'excitation_emission',
        2: 'decay'
    }
    widgets_stacked = {
        'transmission': ['xystage', 'spectrometer'],
        'excitation_emission': ['xystage', 'spectrometer', 'laser', 'shuttercontrol'],
        'decay': ['xystage', 'digitizer', 'laser', 'shuttercontrol']
    }
    instruments_threads = {
            'transmission': ['xystage', 'spectrometer'],
            'excitation_emission': ['xystage', 'spectrometer', 'laser', 'shuttercontrol', 'powermeter'],
            'decay': ['xystage', 'digitizer', 'laser', 'shuttercontrol']
    }
    statemachines = {
        0: 'TransmissionAlignment()',
        1: 'ExcitationEmissionAlignment()',
        2: 'DecayAlignment()',
        3: 'TransmissionExperiment()',
        4: 'ExcitationEmissionAlignment()',
        5: 'DecayAlignment()'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.stackedWidget.setCurrentIndex(0)

        self.threads = {}
        self.statemachine = None
        self.statemachineThread = QThread()

        self.ui.pushButton_transmission.clicked.connect(lambda state, page=0: self.choose_experiment(page))
        self.ui.pushButton_excitation_emission.clicked.connect(lambda state, page=1: self.choose_experiment(page))
        self.ui.pushButton_decay.clicked.connect(lambda state, page=2: self.choose_experiment(page))
        self.ui.pushButton_return.clicked.connect(self.return_home)
        self.ui.pushButton_start_experiment.clicked.connect(self.start_experiment)
        self.ui.pushButton_start_experiment.setEnabled(False)
        self.ui.pushButton_alignment_experiment.clicked.connect(self.alignment_experiment)

    def choose_experiment(self, page):
        self.select_statemachine(page)

        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.stackedWidget_experiment.setCurrentIndex(page)

    def select_statemachine(self, page):
        if self.ui.pushButton_alignment_experiment.text() == 'Set Experiment':
            self.statemachine = eval(self.statemachines[page])
        else:
            self.statemachine = eval(self.statemachines[page+3])
        self.define_threads(self.experiments_stacked[page])

    def define_threads(self, experiment):
        for inst in self.instruments_threads[experiment]:
            self.threads[inst] = QThread()
        self.move_to_threads()

    def move_to_threads(self):
        self.statemachine.moveToThread(self.statemachineThread)
        for key, thread in self.threads.items():
            instrument = getattr(self.statemachine, key)
            instrument.moveToThread(thread)
        self.start_threads()
        self.statemachine.run()
        self.add_instruments_to_guis()

    def start_threads(self):
        self.statemachineThread.start()
        for _, thread in self.threads.items():
            thread.start()

    def add_instruments_to_guis(self):
        self.ui.widget_spectrometer_transmission.spectrometer = self.statemachine.spectrometer
        self.ui.widget_spectrometerplot_transmission.spectrometer = self.statemachine.spectrometer
        self.ui.widget_xystage_transmission.xystage = self.statemachine.xystage
        self.ui.widget_xystage_transmission.connect_signals_slots()
        self.ui.widget_spectrometerplot_transmission.connect_signals_slots()
        self.ui.widget_spectrometer_transmission.connect_signals_slots()

    def quit_threads(self):
        self.statemachineThread.quit()
        for _, thread in self.threads.items():
            thread.quit()

    def return_home(self):
        # add something that quits all threads from the experiment such that a new experiment can be done
        self.ui.stackedWidget.setCurrentIndex(0)

    def alignment_experiment(self):
        # finalize the current statemachine and load the new statemachine.
        self.alignment_experiment_gui()

    def alignment_experiment_gui(self):
        # switches to alignment mode by going to different pages in the instrument widgets
        # and adjusts their size. strict naming of widgets is necessary for this to work.
        # also calls initialization of either alignment or experiment mode

        if self.ui.pushButton_alignment_experiment.text() == 'Set Experiment':
            page_widget = 0
            page_preffered = 'page_experiment'
            page_ignored = 'page_alignment'
            text_button = 'Alignment'
            enable_start = True
        else:
            page_widget = 1
            page_preffered = 'page_alignment'
            page_ignored = 'page_experiment'
            text_button = 'Set Experiment'
            enable_start = False

        experiment = self.experiments_stacked[self.ui.stackedWidget_experiment.currentIndex()]

        for instrument in self.widgets_stacked[experiment]:
            eval(f'self.ui.widget_{instrument}_{experiment}.ui.stackedWidget.setCurrentIndex({page_widget})')
            eval(f'self.ui.widget_{instrument}_{experiment}.ui.{page_preffered}.setSizePolicy(QtWidgets.'
                 f'QSizePolicy.Preferred,QtWidgets.QSizePolicy.Fixed)')
            eval(f'self.ui.widget_{instrument}_{experiment}.ui.{page_ignored}.'
                 f'setSizePolicy(QtWidgets.QSizePolicy.Ignored,QtWidgets.QSizePolicy.Ignored)')

        self.ui.pushButton_alignment_experiment.setText(text_button)
        self.ui.pushButton_start_experiment.setEnabled(enable_start)

    def start_experiment(self):
        print('the experiment has started')
        self.ui.pushButton_return.setEnabled(False)
        QTimer.singleShot(1000, self.experiment_finished)

    def experiment_finished(self):
        print('the experiment has finished')
        self.ui.pushButton_return.setEnabled(True)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
