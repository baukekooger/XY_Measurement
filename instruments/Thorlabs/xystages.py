import logging
from instruments.Thorlabs import apt
import time


class Instrument:
    """Base class for all Instruments.

    Attributes:
        polltime (float): time in [s] between each call to an instrument if a measurement has completed.
        timeout (float): time in [s] before measurement is aborted and an error is returned.
    """

    def __init__(self, polltime=0.01, timeout=30):
        self.measuring = False
        self.polltime = polltime
        self.timeout = timeout

    @property
    def name(self):
        """Name of the Instrument"""
        return type(self).__name__

    def connect(self):
        raise NotImplementedError(
            'Instrument {} has not defined a connect method'.format(
                type(self).__name__))

    def disconnect(self):
        raise NotImplementedError(
            'Instrument {} has not defined a disconnect method'.format(
                type(self).__name__))

    def measure(self):
        raise NotImplementedError(
            'Instrument {} has not defined a measure method'.format(
                type(self).__name__))

    @classmethod
    def disconnect_all(cls):
        """Disconnects all connected Instruments"""
        for instrument in cls.objs:
            try:
                instrument.disconnect()
            except NotImplementedError:
                pass


class XYStage(Instrument):
    """
    Abstraction class to control both Thorlabs stages at once
    """

    def __init__(self, xstage_serial=67844568, ystage_serial=67844567, polltime=0.1):
        super().__init__()
        self.polltime = polltime
        # Position extremes
        self._xmax = 150
        self._xmin = 0
        self._ymax = 150
        self._ymin = 0
        # XYStage status
        # small stages: xstageserial=67844568, ystageserial=67844567
        # big stages: xstageserial=45962470, ystageserial=45951910):
        self.xstage_serial = xstage_serial
        self.ystage_serial = ystage_serial
        self.xstage = None
        self.ystage = None
        self.connected = False

    def list_available_devices(self):
        return [device[1] for device in apt.list_available_devices()]

    @property
    def x(self):
        """x-position of the XYStage """
        return self.xstage.position

    @x.setter
    def x(self, value):
        if not (self._xmin < value < self._xmax):
            logging.warning('Attempt to move x stage out of bounds')
            logging.warning('Retaining position x=%.2f mm', self.x)
            return
        self.xstage.move_to(value, blocking=False)

    @property
    def y(self):
        """y-position of the XYStage """
        return self.ystage.position

    @y.setter
    def y(self, value):
        if not (self._ymin < value < self._ymax):
            logging.warning('Attempt to move y stage out of bounds')
            logging.warning('Retaining position y=%.2f mm', self.y)
            return
        self.ystage.move_to(value, blocking=False)

    def connect(self):
        self.xstage = apt.Motor(self.xstage_serial)
        self.ystage = apt.Motor(self.ystage_serial)
        self.connected = True

    def disconnect(self):
        if not self.connected:
            return
        self.xstage = None
        self.ystage = None
        apt.reconnect()
        self.connected = False

    def reconnect(self):
        self.connected = False
        while not self.connected:
            try:
                apt.reconnect()
                self.xstage = apt.Motor(self.xstage_serial)
                self.ystage = apt.Motor(self.ystage_serial)
                self.connected = True
            except Exception as e:
                logging.error(f'Failed to connect to XYStage... reattempting! - error = {e}')
                time.sleep(1)

    def close(self):
        self.xstage = None
        self.ystage = None
        apt.close()
    
    def home(self):
        """ Homes the XYStage, setting x and y to (0,0)
        """
        self.xstage.move_home()
        self.ystage.move_home()
        while not (self.xstage.is_in_motion and self.ystage.is_in_motion):
            time.sleep(self.polltime)

    def move(self, x, y):
        """Moves the XYStage to the desired position.

        Args:
            | x (float): desired x-position
            | y (float): desired y-position

        Returns:
            | float: final x-position
            | float: final y-position
        """
        self.x = x
        self.y = y
        while (self.xstage.is_in_motion or self.ystage.is_in_motion):
            time.sleep(self.polltime)
        return self.x, self.y

    def measure(self):
        """Measure the current position of the XYStage

        Returns:
            | float: x-position
            | float: y-position
        Raises:
            ConnectionError: If the XYStage isn't connected
        """
        x = self.x
        y = self.y
        return x, y

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

