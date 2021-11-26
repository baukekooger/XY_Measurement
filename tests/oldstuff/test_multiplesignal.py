from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class MultipleSignal(QObject):
    """ class that emits a signal when all desired signals have arrived

        accepts up to 6 signals, can be easily extended
        """
    measurements_done = pyqtSignal()

    def __init__(self, number_of_signals=1):
        super().__init__()
        self.signals_done = [False for _ in range(6)]
        self.number_of_signals = number_of_signals

    @pyqtSlot()
    def set_signal_1_done(self):
        self.signals_done[0] = True
        self.check_global_done()

    @pyqtSlot()
    def set_signal_2_done(self):
        self.signals_done[1] = True
        self.check_global_done()

    @pyqtSlot()
    def set_signal_3_done(self):
        self.signals_done[2] = True
        self.check_global_done()

    @pyqtSlot()
    def set_signal_4_done(self):
        self.signals_done[1] = True
        self.check_global_done()

    @pyqtSlot()
    def set_signal_5_done(self):
        self.signals_done[1] = True
        self.check_global_done()

    @pyqtSlot()
    def set_signal_6_done(self):
        self.signals_done[1] = True
        self.check_global_done()

    @pyqtSlot()
    def check_global_done(self):
        if sum(self.signals_done) == self.number_of_signals:
            self.measurements_done.emit()
            self.reset()

    @pyqtSlot()
    def reset(self):
        self.signals_done = [False for _ in range(6)]
