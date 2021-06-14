# -*- coding: utf-8 -*-
"""
Created on Thu Aug 24 16:33:42 2017

@author: epjmerkx
"""

from instruments.Thorlabs.xystages import XYStage
from PyQt5.QtCore import QObject, QMutexLocker, QMutex, pyqtSignal, pyqtSlot
import logging

logging.basicConfig(level=logging.INFO)


class QInstrument(QObject):
    """Base class for threadable PyQt instruments
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.mutex = QMutex(QMutex.Recursive)


class QXYStage(QInstrument, XYStage):
    """PyQt5 implementation of XYStage Instrument

    pyqtSignals:
        measurement_complete (float, float):
            The x-, and y-positions of the XYStage.
        ready:
            The XYStage has finished moving
    """
    measurement_complete = pyqtSignal(float, float)
    ready = pyqtSignal()

    def __init__(self, parent=None):
        QInstrument.__init__(self, parent=parent)
        XYStage.__init__(self)

    @pyqtSlot(float, float)
    def move(self, x, y):
        """
        Emits:
            ready: the XYStage is in position
        """
        x, y = XYStage.move(self, x, y)
        self.measurement_complete.emit(x, y)
        self.ready.emit()
        return x, y

    @pyqtSlot()
    @pyqtSlot(float, float)
    def measure(self, *args):
        """
        Emits:
            measurement_complete (float, float): x-position, y-position
        """
        with(QMutexLocker(self.mutex)):
            x, y = XYStage.measure(self)
        self.measurement_complete.emit(x, y)
        return x, y

    def disconnect(self):
        try:
            QInstrument.disconnect(self)
        except:
            pass
        XYStage.disconnect(self)
