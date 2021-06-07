import logging
from . import apt
import numpy as np
import time
from math import ceil, floor
import asyncio


class XYStage:
    """
    Abstraction class to control both Thorlabs stages at once
    """

    def __init__(self, xstage_serial, ystage_serial, polltime=0.1):
        self.polltime = polltime
        # Position extremes
        self._xmax = 150
        self._xmin = 0
        self._ymax = 150
        self._ymin = 0
        # XYStage status
        self.xstage_serial = xstage_serial
        self.ystage_serial = ystage_serial
        self.xstage = apt.Motor(xstage_serial)
        self.ystage = apt.Motor(ystage_serial)
        
    def list_available_devices():
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

    def close(self):
        self.xstage = None
        self.ystage = None
        apt.close()

    def reconnect(self):
        connected = False
        while not connected:
            try:
                apt.reconnect()
                self.xstage = apt.Motor(self.xstage_serial)
                self.ystage = apt.Motor(self.ystage_serial)
                connected = True
            except Exception:
                logging.error('Failed to connect to XYStage... reattempting!')
                time.sleep(1)
    
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
