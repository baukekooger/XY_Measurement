# -*- coding: utf-8 -*-
"""
Created on Thu Aug 24 16:33:42 2017

@author: epjmerkx
"""
from instruments.OceanOptics.spectrometer import Spectrometer
from PyQt5.QtCore import QObject, QMutexLocker, QMutex, pyqtSignal, pyqtSlot
import logging
import time

logging.basicConfig(level=logging.INFO)


class QInstrument(QObject):
    """Base class for threadable PyQt instruments
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.mutex = QMutex(QMutex.Recursive)


class QSpectrometer(QInstrument, Spectrometer):
    """PyQt5 implementation of Spectrometer Instrument

    pyqtSignals:
        measurement_complete (list, list)
            the intensities and the times of the spectromter measurement
    """
    measurement_complete = pyqtSignal(list, list)

    def __init__(self, parent=None, integrationtime=100, average_measurements=1):
        QInstrument.__init__(self, parent=parent)
        Spectrometer.__init__(self, integrationtime, average_measurements)
        self.last_intensity = []
        self.last_times = []

    @pyqtSlot()
    @pyqtSlot(list, list)
    def measure(self, *args):
        """Performs a mutex-locked measurement.

        Returns:
           | list: intensities [counts]
           | list: times measured over as
               [ [tstart0, tstart1,...], [tstop0, tstop1, ...] ]
        Emits:
            measurement_complete (list, list):
                | intensities [counts],
                | times measured over as
                    [ [tstart0, tstart1,...], [tstop0, tstop1, ...] ]
        """
        #        print('Spectrometer: {}'.format(threading.currentThread()))
        with(QMutexLocker(self.mutex)):
            intens, ts = Spectrometer.measure(self)
        logging.info('Measuring Spectrometer')
        self.measurement_complete.emit(intens, ts)
        logging.info('Spectrometer Done')
        self.last_intensity = intens
        self.last_times = ts
        return intens, ts

    @pyqtSlot()
    def measure_dark(self):
        """Performs a mutex-locked dark measurement.
        The result will be substracted from the reported intensities.
        """
        with(QMutexLocker(self.mutex)):
            dark, t = Spectrometer.measure_dark(self)
        self.measurement_complete.emit(dark, t)
        self.last_intensity = dark
        self.last_times = t
        return dark, t

    @pyqtSlot()
    def clear_dark(self):
        Spectrometer.clear_dark(self)

    def disconnect(self):
        try:
            QInstrument.disconnect(self)
        except:
            pass
        Spectrometer.disconnect(self)
