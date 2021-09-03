from instruments.OceanOptics.spectrometer import QSpectrometer
from PyQt5.QtCore import QThread, QTimer, QObject, pyqtSignal, pyqtSlot
from PyQt5 import QtWidgets
import instruments.CAEN as CAENlib
from instruments.Thorlabs.shuttercontrollers import QShutterControl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys
import numpy as np
import time
from matplotlib import pyplot as plt
import random
import logging
logging.basicConfig(level=logging.INFO)


class Spectrometer(QSpectrometer):

    measurement_complete_result = pyqtSignal(np.ndarray)
    measurement_complete_signal = pyqtSignal()
    measurement_complete_dark_result = pyqtSignal(np.ndarray)
    measurement_complete_dark_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def measure_spectrum(self):
        spectrum, _ = self.measure()
        self.measurement_complete_result.emit(spectrum)
        self.measurement_complete_signal.emit()

    @pyqtSlot()
    def measure_dark_spectrum(self):
        darkspectrum, _ = self.measure_dark()
        self.measurement_complete_dark_result.emit(darkspectrum)
        self.measurement_complete_dark_signal.emit()
        logging.info('Took darkspectrum')

    @pyqtSlot(int)
    def set_integration_time(self, number_of_pulses):
        # frequency of laser is 101 Hz, integration time is in ms
        integration_time = 1000 / 101 * number_of_pulses
        self.integrationtime = integration_time


class Digitizer(CAENlib.Digitizer):
    # subclussing digitizer to add some additional signals
    measurement_complete_single_result = pyqtSignal(np.ndarray)
    measurement_complete_single_signal = pyqtSignal()
    measurement_complete_multiple_result = pyqtSignal(np.ndarray)
    measurement_complete_multiple_signal = pyqtSignal()

    def __init__(self, digitizer_handle=CAENlib.list_available_devices()[0]):
        CAENlib.Digitizer.__init__(self, digitizer_handle)
        self.number_of_pulses = 30

    @pyqtSlot()
    def measure_digi(self):
        # subtracts average of first 50 samples, inverts data
        data = self.measure()[list(self.active_channels)][0][0]
        data = -(data - np.mean(data[0:50]))
        return data

    @pyqtSlot()
    def measure_digi_emit(self):
        data = self.measure_digi()
        self.measurement_complete_single_result.emit(data)
        self.measurement_complete_single_signal.emit()
        return data

    @pyqtSlot()
    def measure_multiple_digi(self):
        data = []
        for i in range(self.number_of_pulses):
            if i == 0:
                data = self.measure_digi()
            else:
                data = np.vstack((data, self.measure_digi()))
        self.measurement_complete_multiple_result.emit(data)
        self.measurement_complete_multiple_signal.emit()
        return data


class MultipleSignal(QObject):

    measurements_done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.sp_done = False
        self.digi_done = False

    @pyqtSlot()
    def set_sp_done(self):
        self.sp_done = True
        self.check_measurements_done()

    @pyqtSlot()
    def set_digi_done(self):
        self.digi_done = True
        self.check_measurements_done()

    @pyqtSlot()
    def check_measurements_done(self):
        if self.sp_done and self.digi_done:
            self.measurements_done.emit()
            self.sp_done = False
            self.digi_done = False
            logging.info('both signals done, emitted global done')

    @pyqtSlot()
    def reset(self):
        self.sp_done = False
        self.digi_done = False


class PlotWindow(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.canvas)

    @pyqtSlot(np.ndarray)
    def plot(self, ratio):
        self.ax.clear()
        self.ax.plot(ratio)
        self.ax.set_xlabel('Measurement number')
        self.ax.set_ylabel('Normalized ratio spectropower to laserpower')
        self.ax.set_title('Integrated spectrometer power relative to last measurement')
        self.figure.tight_layout()
        self.canvas.draw()

    @pyqtSlot(np.ndarray)
    def plot_spectrum(self, spectrum):
        self.ax.clear()
        self.ax.plot(spectrum)
        self.ax.set_xlabel('Wavelength')
        self.ax.set_ylabel('Counts')
        self.ax.set_title('Spectrometer spectrum')
        self.figure.tight_layout()
        self.canvas.draw()

    @pyqtSlot(np.ndarray)
    def plot_pulse(self, pulse):
        self.ax.clear()
        self.ax.plot(pulse)
        self.ax.set_xlabel('Sample nr')
        self.ax.set_ylabel('Counts')
        self.ax.set_title('Digitizer readout')
        self.figure.tight_layout()
        self.canvas.draw()

    @pyqtSlot()
    def clearplot(self):
        self.ax.clear()
        self.ax.set_xlabel('Measurement number')
        self.ax.set_ylabel('Normalized ratio spectropower to laserpower')
        self.ax.set_title('Power in spectrum versus laser power by integrating pulses')
        self.figure.tight_layout()
        self.canvas.draw()


class SpectroPower(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.running = False
        self.number_of_pulses = 30
        self.measurement_spectrometer_last = np.empty(0)
        self.measurement_spectrometer_sum = np.empty(0)
        self.measurement_spectrometer_dark_last = np.empty(0)
        self.measurement_spectrometer_dark_sum = np.empty(0)
        self.measurement_digitizer_last = np.empty(0)
        self.measurement_digitizer_sum = np.empty(0)

        # create workers
        self.sp = Spectrometer()
        self.digitizer = Digitizer()
        self.shuttercontrol = QShutterControl()
        self.signalchecker = MultipleSignal()
        self.plotwindow = PlotWindow()

        # setup ui
        self.startbutton = QtWidgets.QPushButton('start/restart')
        self.stopbutton = QtWidgets.QPushButton('stop')
        self.clearbutton = QtWidgets.QPushButton('clear')
        self.horizontallayout_buttons = QtWidgets.QHBoxLayout()
        self.horizontallayout_buttons.addWidget(self.startbutton)
        self.horizontallayout_buttons.addWidget(self.stopbutton)
        self.horizontallayout_buttons.addWidget(self.clearbutton)

        self.ratiobutton = QtWidgets.QPushButton('ratio')
        self.pulsebutton = QtWidgets.QPushButton('pulse')
        self.spectrometerbutton = QtWidgets.QPushButton('spectrometer')
        self.horizontallayout_buttons_experiment = QtWidgets.QHBoxLayout()
        self.horizontallayout_buttons_experiment.addWidget(self.ratiobutton)
        self.horizontallayout_buttons_experiment.addWidget(self.pulsebutton)
        self.horizontallayout_buttons_experiment.addWidget(self.spectrometerbutton)

        self.pulses_label = QtWidgets.QLabel('number of pulses')
        self.pulses = QtWidgets.QSpinBox()
        self.pulses.setMinimum(3)
        self.pulses.setMaximum(1000)
        self.pulses.setValue(self.number_of_pulses)
        self.pulses_indicator = QtWidgets.QLabel('set pulses')
        self.horizontallayout_pulses = QtWidgets.QHBoxLayout()
        self.horizontallayout_pulses.addWidget(self.pulses_label)
        self.horizontallayout_pulses.addWidget(self.pulses)
        self.horizontallayout_pulses.addWidget(self.pulses_indicator)

        self.gridlayout = QtWidgets.QGridLayout()
        self.gridlayout.addLayout(self.plotwindow.layout, 0, 0)
        self.gridlayout.addLayout(self.horizontallayout_pulses, 1, 0)
        self.gridlayout.addLayout(self.horizontallayout_buttons_experiment, 2, 0)
        self.gridlayout.addLayout(self.horizontallayout_buttons, 3, 0)
        self.setLayout(self.gridlayout)

        # create threads for workers and move workers to threads, then start threads
        self.sp_thread = QThread()
        self.digitizer_thread = QThread()
        self.shuttercontrol_thread = QThread()
        self.signalchecker_thread = QThread()
        self.plot_thread = QThread()
        self.sp.moveToThread(self.sp_thread)
        self.digitizer.moveToThread(self.digitizer_thread)
        self.shuttercontrol.moveToThread(self.shuttercontrol_thread)
        self.signalchecker.moveToThread(self.signalchecker_thread)
        self.plotwindow.moveToThread(self.plot_thread)

        # create timers for periodic signals
        self.timer_measurement = QTimer()
        self.timer_plot = QTimer()

        # connect signals
        self.startbutton.clicked.connect(self.start)
        self.stopbutton.clicked.connect(self.stop)
        self.clearbutton.clicked.connect(self.clear)
        self.ratiobutton.clicked.connect(self.measure_ratio)
        self.pulsebutton.clicked.connect(self.measure_pulse)
        self.spectrometerbutton.clicked.connect(self.measure_spectrum)

        self.timer_plot.timeout.connect(self.plot_ratio)

        self.sp.measurement_complete_result.connect(self.process_spectrometer)
        self.sp.measurement_complete_signal.connect(self.signalchecker.set_sp_done)
        self.sp.measurement_complete_dark_result.connect(self.process_spectrometer_dark)
        self.digitizer.measurement_complete_multiple_result.connect(self.process_digitizer_multiple)
        self.digitizer.measurement_complete_multiple_signal.connect(self.signalchecker.set_digi_done)
        self.digitizer.measurement_complete_single_result.connect(self.process_digitizer_single)

        self.stopbutton.setEnabled(False)
        self.startbutton.setEnabled(False)
        self.clearbutton.setEnabled(False)

        # initialize instruments
        self.init_sp()
        self.init_shuttercontrol()
        self.init_digitizer()

        # start instrument threads
        self.sp_thread.start()
        self.digitizer_thread.start()
        self.shuttercontrol_thread.start()
        self.plot_thread.start()
        self.signalchecker_thread.start()

    def init_sp(self):
        self.sp.connect()
        pass

    def init_shuttercontrol(self):
        self.shuttercontrol.connect()

    def init_digitizer(self):
        powermeter_channel = 1
        powermeter_dc_offset = 10
        self.digitizer.set_channel_gain(channel=powermeter_channel, value=1)
        self.digitizer.record_length = 0
        self.digitizer.max_num_events = 1
        self.digitizer.post_trigger_size = 90
        self.digitizer.acquisition_mode = CAENlib.AcqMode.SW_CONTROLLED
        channels = {powermeter_channel: powermeter_dc_offset}
        # Program the Digitizer
        self.digitizer.active_channels = channels.keys()
        for channel, dc_offset in channels.items():
            self.digitizer.set_dc_offset(channel, dc_offset)

        self.digitizer.external_trigger_mode = CAENlib.TriggerMode.ACQ_ONLY
        self.digitizer.external_trigger_level = CAENlib.IOLevel.TTL

    @pyqtSlot(np.ndarray)
    def process_digitizer_multiple(self, result):
        pulse_sum = np.sum(result)
        self.measurement_digitizer_sum = np.append(self.measurement_digitizer_sum, pulse_sum)

    @pyqtSlot(np.ndarray)
    def process_digitizer_single(self, result):
        self.measurement_digitizer_last = result

    @pyqtSlot(np.ndarray)
    def process_spectrometer(self, result):
        self.measurement_spectrometer_last = result
        spectrometer_sum = np.sum(result)
        self.measurement_spectrometer_sum = np.append(self.measurement_spectrometer_sum, spectrometer_sum)

    @pyqtSlot(np.ndarray)
    def process_spectrometer_dark(self, result):
        self.measurement_spectrometer_dark_last = result
        self.measurement_spectrometer_dark_sum = np.sum(result)

    @pyqtSlot()
    def pulses_changed(self):
        # closes the shutter, disconnects from doing new measurements and connects to wait for last measurement

        QTimer.singleShot(0, self.shuttercontrol.disable)

        try:
            self.pulses.editingFinished.disconnect()
            logging.info(f'disconnected edit pulses')
        except TypeError as e:
            logging.info(f'pulses {e}')

        self.pulses_indicator.setText(f'taking darkspectrum')
        self.number_of_pulses = self.pulses.value()
        self.toggle_all_buttons(False)
        if self.running:
            try:
                self.signalchecker.measurements_done.disconnect()
                self.signalchecker.measurements_done.connect(self.wait_for_last_measurement)
                logging.info(f'disconnected measurements done from new measurement')
            except TypeError as e:
                logging.info(f'signal: measurements done {e}')
        else:
            self.wait_for_last_measurement()

    @pyqtSlot()
    def wait_for_last_measurement(self):
        # takes new dark spectrum after last measurement has come in
        try:
            self.signalchecker.measurements_done.disconnect()
            logging.info(f'disconnected measurement done from await signal')
        except TypeError as e:
            logging.info(f'measurements done wait for last measurement{e}')

        self.clear()
        self.digitizer.number_of_pulses = self.number_of_pulses
        self.sp.set_integration_time(self.number_of_pulses)
        QTimer.singleShot(0, self.sp.measure_dark_spectrum)


    @pyqtSlot()
    def toggle_all_buttons(self, toggle):
        self.startbutton.setEnabled(toggle)
        self.stopbutton.setEnabled(toggle)
        self.clearbutton.setEnabled(toggle)
        self.ratiobutton.setEnabled(toggle)
        self.pulsebutton.setEnabled(toggle)
        self.spectrometerbutton.setEnabled(toggle)
        self.pulses.setEnabled(toggle)

    @pyqtSlot()
    def start(self):
        self.running = True
        # redo measurement at every integration time. Add in little extra time to make sure measurement is complete
        self.startbutton.setEnabled(False)
        self.stopbutton.setEnabled(True)
        self.signalchecker.measurements_done.connect(self.sp.measure_spectrum)
        self.signalchecker.reset()
        QTimer.singleShot(0, self.sp.measure_spectrum)
        self.timer_plot.start(500)

    @pyqtSlot()
    def stop(self):
        try:
            self.pulses.editingFinished.disconnect()
            logging.info(f'disconnected edit pulses from stop function')
        except TypeError as e:
            logging.info(f'pulses {e}')
        try:
            self.signalchecker.measurements_done.disconnect()
            logging.info(f'stopping, disconnected measurements done from new measurement')
        except TypeError as e:
            logging.info(f'signal: global done {e}')
        self.toggle_all_buttons(False)
        self.signalchecker.measurements_done.connect(self.reset_buttons)
        logging.info(f'connected measurement done to reset')

    @pyqtSlot()
    def reset_buttons(self):
        try:
            self.signalchecker.measurements_done.disconnect()
            logging.info(f'disconnected measurements done from reset buttons')
        except TypeError as e:
            logging.info(f'measurements done : {e}')
        self.toggle_all_buttons(True)
        self.stopbutton.setEnabled(False)
        self.ratiobutton.setEnabled(False)
        self.running = False
        self.pulses.editingFinished.connect(self.pulses_changed)

    @pyqtSlot()
    def clear(self):
        self.measurement_digitizer_sum = np.empty(0)
        self.measurement_spectrometer_sum = np.empty(0)
        try:
            self.signalchecker.measurements_done.disconnect(self.clear)
        except TypeError as e:
            logging.info(e)

    @pyqtSlot()
    def plot_ratio(self):
        cleaned_spectrum = self.measurement_spectrometer_sum - self.measurement_spectrometer_dark_sum
        minlength = min(len(cleaned_spectrum), len(self.measurement_digitizer_sum))
        if minlength > 0:
            ratio = cleaned_spectrum[:minlength]/self.measurement_digitizer_sum[:minlength]
            ratio_normalized = ratio/ratio[-1]
            cleaned_spectrum_ratio = cleaned_spectrum/cleaned_spectrum[-1]
            QTimer.singleShot(0, lambda x=cleaned_spectrum_ratio: self.plotwindow.plot(x))

    @pyqtSlot()
    def disconnect_signals(self):
        try:
            self.signalchecker.measurements_done.disconnect()
            logging.info('succesfully disconnected measurements done')
        except TypeError as e:
            logging.info(f'signal : measurements done - {e}')
        try:
            self.pulses.editingFinished.disconnect()
            logging.info('succesfully disconnected editingFinished')
        except TypeError as e:
            logging.info(f'signal : pulses editingfinished - {e}')
        try:
            self.timer_plot.stop()
            self.timer_plot.disconnect()
            logging.info('succesfully disconnected timer plot')
        except TypeError as e:
            logging.info(f'signal : timer plot - {e}')
        try:
            self.timer_measurement.stop()
            self.timer_measurement.disconnect()
            logging.info('succesfully disconnected timer measurement')
        except TypeError as e:
            logging.info(f'signal : timer measurement - {e}')
        try:
            self.sp.cache_cleared.disconnect()
            logging.info('succesfully disconnected cache cleared')
        except TypeError as e:
            logging.info(f'signal : cache cleared - {e}')
        try:
            self.sp.measurement_complete_dark_signal.disconnect()
            logging.info('succesfully disconnected measurement_dark')
        except TypeError as e:
            logging.info(f'signal : cache cleared - {e}')

    @pyqtSlot()
    def measure_ratio(self):
        self.disconnect_signals()
        self.clear()
        self.pulses_changed()
        self.sp.cache_cleared.connect(self.digitizer.measure_multiple_digi)
        self.pulses.editingFinished.connect(self.pulses_changed)
        self.sp.measurement_complete_dark_signal.connect(self.darkspectrum_taken)
        self.toggle_all_buttons(True)
        self.stopbutton.setEnabled(False)
        self.ratiobutton.setEnabled(False)

        self.timer_plot.timeout.connect(self.plot_ratio)
        self.timer_plot.start(500)

    def darkspectrum_taken(self):
        # opens shutter, sets the pulse indicator to current number of pulses.
        # Reconnects edit finished to pulses changed

        QTimer.singleShot(0, self.shuttercontrol.enable)
        pulses = self.number_of_pulses
        QTimer.singleShot(0, lambda x=pulses: self.pulses_indicator.setText(f'{x} pulses'))
        self.toggle_all_buttons(True)
        self.ratiobutton.setEnabled(False)
        self.stopbutton.setEnabled(False)
        self.pulses.setEnabled(True)
        self.pulses.lineEdit()
        self.pulses.editingFinished.connect(self.pulses_changed)

    @pyqtSlot()
    def measure_pulse(self):
        # todo include shutter signal to be open
        self.disconnect_signals()
        self.toggle_all_buttons(False)
        self.spectrometerbutton.setEnabled(True)
        self.ratiobutton.setEnabled(True)

        self.timer_measurement.timeout.connect(self.digitizer.measure_digi_emit)
        self.timer_plot.timeout.connect(self.plot_pulse)
        self.timer_measurement.start(100)
        self.timer_plot.start(100)

    @pyqtSlot()
    def plot_pulse(self):
        if any(self.measurement_digitizer_last):
            QTimer.singleShot(0, lambda x=self.measurement_digitizer_last: self.plotwindow.plot_pulse(x))
        else:
            QTimer.singleShot(0, self.plotwindow.clearplot)

    @pyqtSlot()
    def measure_spectrum(self):
        self.disconnect_signals()
        self.toggle_all_buttons(False)
        self.ratiobutton.setEnabled(True)
        self.pulsebutton.setEnabled(True)
        self.pulses.setEnabled(True)

        self.pulses.editingFinished.connect(self.set_pulses_spectrum)
        self.timer_measurement.timeout.connect(self.measure_sp)
        self.timer_plot.timeout.connect(self.plot_spectrum)
        self.timer_measurement.start(200)
        self.timer_plot.start(200)

    @pyqtSlot()
    def measure_sp(self):
        if not self.sp.measuring:
            QTimer.singleShot(0, self.sp.measure_spectrum)

    @pyqtSlot()
    def set_pulses_spectrum(self): 
        self.number_of_pulses = self.pulses.value()
        self.pulses_indicator.setText(f'{self.number_of_pulses} pulses')
        QTimer.singleShot(0, lambda x=self.number_of_pulses: self.sp.set_integration_time(x))

    @pyqtSlot()
    def plot_spectrum(self):
        if any(self.measurement_spectrometer_last):
            QTimer.singleShot(0, lambda x=self.measurement_spectrometer_last: self.plotwindow.plot_spectrum(x))
        else:
            QTimer.singleShot(0, self.plotwindow.clearplot)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = SpectroPower()
    main.show()
    sys.exit(app.exec_())
