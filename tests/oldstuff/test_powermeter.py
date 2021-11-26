from instruments.Thorlabs.qpowermeter import QPowerMeter
from instruments.Ekspla import QLaser
import numpy as np
import time
from matplotlib import pyplot as plt


class PowerMeasurement:
    def __init__(self):
        self.laser = QLaser()
        self.powermeter = QPowerMeter()
        self.measurement = []
        self.measuring = False
        self.average_power = []
        self.average_power_wavelength = []
        self.average_power_multiple = []
        self.offset = None
        self.init_laser()
        self.init_powermeter()

    def init_laser(self):
        self.laser.connect()

    def init_powermeter(self):
        self.powermeter.connect()
        self.powermeter.integration_time = 5000

    def power_measurement(self, wl_start, wl_stop, wl_step):
        times = []
        powers = []
        wavelengths = np.arange(wl_start, wl_stop, wl_step)
        for count, wl in enumerate(wavelengths):
            self.laser.wavelength = wl
            self.powermeter.wavelength = wl
            while not self.laser.is_stable():
                time.sleep(0.1)
            print(f'laser stable at {wl} nm')
            if count == 0:
                times, powers = self.powermeter.measure()
            else:
                timesingle, powersingle = self.powermeter.measure()
                times = np.vstack((times, timesingle))
                powers = np.vstack((powers, powersingle))
        return times, powers, wavelengths


pm = PowerMeasurement()
