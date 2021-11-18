import logging
from instruments.Thorlabs import apt
from instruments.Thorlabs.apt.core import APTError
import time
from PyQt5.QtCore import QObject, QMutexLocker, QMutex, pyqtSignal, pyqtSlot


class QXYStage(QObject):
    """
    Python implementation of XY stages as a QObject.
    Wraps thorlabs apt dll and provides additional functionality

    """
    measurement_complete = pyqtSignal(float, float)
    stage_settled = pyqtSignal()
    homing_status = pyqtSignal(bool, bool)

    def __init__(self, xstage_serial=45951910, ystage_serial=45962470, polltime=0.1, timeout=30, parent=None):
        super().__init__(parent=parent)
        self.logger = logging.getLogger('Qinstrument.QXYStage')
        self.logger.info('init QXYStage')
        self.mutex = QMutex(QMutex.Recursive)
        self.measuring = False
        self.timeout = timeout
        self.polltime = polltime
        # Position extremes
        self.xmax = 70
        self.xmin = 0
        self.ymax = 160
        self.ymin = 0
        # XYStage status
        # small stages: xstageserial=67844568, ystageserial=67844567
        # big stages: xstageserial=45951910, ystageserial=45962470):
        self.xstage_serial = xstage_serial
        self.ystage_serial = ystage_serial
        self.xstage = None
        self.ystage = None
        self.connected = False
        self.xhomed = None
        self.yhomed = None

    @property
    def name(self):
        return type(self).__name__

    @staticmethod
    def list_available_devices(self):
        return apt.list_available_devices()

    @property
    def x(self):
        return self.xstage.position

    @x.setter
    def x(self, value):
        if not (self.xmin <= value <= self.xmax):
            self.logger.warning('Attempt to move x stage out of bounds')
            self.logger.warning('Retaining position x=%.2f mm', self.x)
            return
        self.xstage.move_to(value, blocking=False)

    @property
    def y(self):
        return self.ystage.position

    @y.setter
    def y(self, value):
        if not (self.ymin <= value <= self.ymax):
            self.logger.warning('Attempt to move y stage out of bounds')
            self.logger.warning('Retaining position y=%.2f mm', self.y)
            return
        self.ystage.move_to(value, blocking=False)

    def connect(self):
        try:
            self.xstage = apt.Motor(self.xstage_serial)
            self.ystage = apt.Motor(self.ystage_serial)
            self.connected = True
            self.xhomed = self.xstage.has_homing_been_completed
            self.yhomed = self.ystage.has_homing_been_completed
        except APTError as e:
            self.logger.error(f'Failed to connect stages. {e}')
            raise ConnectionError(e)

    def disconnect(self):
        if not self.connected:
            return
        self.xstage = None
        self.ystage = None
        apt.reconnect()
        self.connected = False

    def stop_motors(self):
        # stops motors slowly such they don't loose their homing
        self.xstage.stop_profiled()
        self.ystage.stop_profiled()

    def reconnect(self):
        self.connected = False
        while not self.connected:
            try:
                apt.reconnect()
                self.xstage = apt.Motor(self.xstage_serial)
                self.ystage = apt.Motor(self.ystage_serial)
                self.connected = True
            except Exception as e:
                self.logger.error(f'Failed to connect to XYStage... reattempting! - error = {e}')
                time.sleep(1)

    def close(self):
        self.xstage = None
        self.ystage = None
        apt.close()

    def settled(self):
        if not self.xstage.is_in_motion and not self.ystage.is_in_motion:
            self.logger.info('stages settled')
            self.stage_settled.emit()
            return True
        else:
            self.logger.info('stages moving')
            return False

    def disable(self):
        self.xstage.disable()
        self.ystage.disable()

    def enable(self):
        self.xstage.enable()
        self.ystage.enable()

    def home(self):
        self.xstage.move_home()
        self.ystage.move_home()

    @pyqtSlot(float, float)
    def move(self, x, y):
        self.x = x
        self.y = y

    @pyqtSlot(float, float)
    def move_with_wait(self, x, y):
        self.x = x
        self.y = y
        while not self.settled():
            time.sleep(0.1)


    @pyqtSlot()
    @pyqtSlot(float, float)
    def measure(self, *args):
        # Emits positions and homing status
        with(QMutexLocker(self.mutex)):
            x = self.x
            y = self.y
            self.xhomed = self.xstage.has_homing_been_completed
            self.yhomed = self.ystage.has_homing_been_completed
        self.measurement_complete.emit(x, y)
        self.homing_status.emit(self.xhomed, self.yhomed)

        return x, y

    @pyqtSlot()
    def measure_homing(self, *args):
        # Emits homing status only
        with(QMutexLocker(self.mutex)):
            self.xhomed = self.xstage.has_homing_been_completed
            self.yhomed = self.ystage.has_homing_been_completed
        self.homing_status.emit(self.xhomed, self.yhomed)

        return self.xhomed, self.yhomed

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers
    pathlogging = Path(__file__).parent.parent.parent / 'loggingconfig.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)