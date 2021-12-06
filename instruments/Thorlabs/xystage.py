import logging
from instruments.Thorlabs import apt
from instruments.Thorlabs.apt.core import APTError
import time
from PyQt5.QtCore import QObject, QMutexLocker, QMutex, pyqtSignal, pyqtSlot


class QXYStage(QObject):
    """
    XY stages as a QObject.
    Wraps thorlabs apt dll and provides additional functionality and signals for communicating to other threads.
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
        self.setpoint_x = 0
        self.setpoint_y = 0

    @property
    def name(self):
        return type(self).__name__

    @staticmethod
    def list_available_devices(self):
        """ List all the connected linear stages. """
        self.logger.info('Listing available devices.')
        return apt.list_available_devices()

    @property
    def x(self):
        """ Query the position of the x stage. """
        self.logger.info('Querying position x stage')
        return self.xstage.position

    @x.setter
    def x(self, value):
        """ Set the position of the x stage. """
        self.logger.info(f'Attempting to move x stage to {value}')
        if not (self.xmin <= value <= self.xmax):
            self.logger.warning('Attempt to move x stage out of bounds')
            self.logger.warning('Retaining position x=%.2f mm', self.x)
            return
        self.xstage.move_to(value, blocking=False)

    @property
    def y(self):
        """ Query the position of the y stage. """
        self.logger.info('Querying the position of the y stage.')
        return self.ystage.position

    @y.setter
    def y(self, value):
        """ Set the position of the y stage. """
        self.logger.info(f'Attempting to set the y position to {value}')
        if not (self.ymin <= value <= self.ymax):
            self.logger.warning('Attempt to move y stage out of bounds')
            self.logger.warning('Retaining position y=%.2f mm', self.y)
            return
        self.ystage.move_to(value, blocking=False)

    def connect(self):
        """ Connect the xy stages. """
        try:
            self.logger.info('Attempting to connect to XY stages.')
            self.xstage = apt.Motor(self.xstage_serial)
            self.ystage = apt.Motor(self.ystage_serial)
            self.connected = True
            self.xhomed = self.xstage.has_homing_been_completed
            self.yhomed = self.ystage.has_homing_been_completed
        except APTError as e:
            self.logger.error(f'Failed to connect stages. {e}')
            raise ConnectionError(e)

    def disconnect(self):
        """ Disconnect the xy stages. """
        if not self.connected:
            self.logger.info('xy stages already disconnected.')
            return
        self.logger.info('Disconnecting xy stages, cleaning up apt lib.')
        self.xstage = None
        self.ystage = None
        apt.reconnect()
        self.connected = False

    def stop_motors(self):
        """ Stop the motors slowly to prevent them losing their homing. """
        self.logger.info('Stopping the motors.')
        self.xstage.stop_profiled()
        self.ystage.stop_profiled()

    def reconnect(self):
        """ Reconnect to motors by reloading the apt library. """
        self.logger.info('Attempting to reconnect motors. ')
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
        """ Close the motors and the apt library. """
        self.logger.info('Closing the motors and apt library.')
        self.xstage = None
        self.ystage = None
        apt.close()

    def settled(self):
        """ Query if the stages are settled or not. """
        if not self.xstage.is_in_motion and not self.ystage.is_in_motion:
            self.logger.info('stages settled')
            self.stage_settled.emit()
            return True
        else:
            self.logger.info('stages moving')
            return False

    def disable(self):
        """ Disable the stages. """
        self.logger.info('Disabling xy stages. ')
        self.xstage.disable()
        self.ystage.disable()

    def enable(self):
        """ Enable xystages. """
        self.logger.info('Enabling xy stages. ')
        self.xstage.enable()
        self.ystage.enable()

    def home(self):
        """ Home the xy stage. """
        self.logger.info('Homing xy stage.')
        self.xstage.move_home()
        self.ystage.move_home()

    @pyqtSlot(float, float)
    def move(self, x, y):
        """ Move the stages to the given x and y positions. Function is non-blocking. """
        self.x = x
        self.y = y

    @pyqtSlot()
    def move_to_setpoints(self):
        """
        Move the stages to their setpoints.

        Keep checking status until stages settled. Function to be used in multithreaded applications where setpoints
        are set prior to calling this function.
        """
        self.x = self.setpoint_x
        self.y = self.setpoint_y
        while not self.settled():
            time.sleep(0.1)

    @pyqtSlot()
    @pyqtSlot(float, float)
    def measure(self, *args):
        """ Measure position and homing status, and emit values to widget. """
        self.logger.debug('measuring xy stage position and homing status')
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
        """ Measure and emit only the homing status. """
        self.logger.info('measuring and emitting only the homing status. ')
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
    pathlogging = Path(__file__).parent.parent.parent / 'logging/loggingconfig_testing.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)