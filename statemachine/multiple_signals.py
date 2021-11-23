import logging
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class MultipleSignal(QObject):
    """
    Class that emits a signal when all signals connected to it have emitted. Used when waiting for instruments from
    multiple threads.

    Instantiate the class with a name and list of signal names. Connect the actual instrument signals to these signals.

    The reset method can be used to return all the signals state to unset.
    """
    global_done = pyqtSignal()

    def __init__(self, name: str = 'no_name', signals: list[str] = None):
        super().__init__()
        self.logger = logging.getLogger('statemachine')
        self.logger.info(f'init multiple signal {name}')
        self.name = name
        self.signals = self.init_signals(signals)

    def init_signals(self, signals: list[str]) -> dict:
        """
        Initialize the signals as a dictionary with the key the signal names as given in the constructor.

        :returns: Dictionary of SingleSignal instances
        """
        sigdict = {}
        for signal in signals:
            sigdict[signal] = SingleSignal(signal)
            sigdict[signal].check_signals.connect(self.check_signals)
        return sigdict

    def check_signals(self):
        """ Check the state of all connected single signals and emit when all are True. """
        for key, signal in self.signals.items():
            if not signal.state:
                return
        self.logger.info(f'multiple signal {self.name} emitting global done')
        self.global_done.emit()

    def reset(self):
        """ Set the state of all single signals to False. """
        for key, signal in self.signals.items():
            signal.reset()

    def __repr__(self):
        signals = list(self.signals.keys())
        return f'Multiple Signal Object With the following signals: {signals}'


class SingleSignal(QObject):
    """
     Class having only a single signal. Instances of this class are added to multiplesignal to enable
     waiting for multiple signals.

     Single signals have a state attribute which is set True when the instrument connected to it emits to this single
     signal. This single signal then emits to the multiple signal object which checks the state of all single signals.
     """
    check_signals = pyqtSignal()

    def __init__(self, name):
        super().__init__()
        self.logger = logging.getLogger('statemachine')
        self.logger.info(f'init single signal {name}')
        self.name = name
        self.state = False

    @pyqtSlot()
    def set_state(self):
        self.state = True
        self.logger.info(f'single signal {self.name} emitting')
        self.check_signals.emit()

    def reset(self):
        self.state = False


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers

    pathlogging = Path(__file__).parent.parent / 'logging/loggingconfig.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
