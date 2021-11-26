import instruments.CAEN as CAENlib
from instruments.Ekspla import QLaser
import numpy as np
import time
from matplotlib import pyplot as plt


def plot_single_measure(data, offset):
    fig, ax = plt.subplots()
    ax.plot(data, label='data')
    ax.set_xlabel('sample')
    ax.set_ylabel('adc value')
    ax.set_title(f'single measurement, adc offset = {offset:.0f}')


def sum_signal(data, active_channels):
    data = data[active_channels]
    m = np.mean(data[:, :, 0:50], axis=-1, keepdims=True)
    data = -(data - m)
    return np.sum(data, axis=-1)


def clean_signal(data, active_channels):
    # removes average and inverts data
    data = data[active_channels]
    offset = np.mean(data[:, :, 0:50], axis=-1, keepdims=True)
    data = -(data - offset)
    return data, offset


class PowerMeasurement:
    def __init__(self):
        self.laser = QLaser()
        self.digitizer = CAENlib.Digitizer(CAENlib.list_available_devices()[0])
        self.number_of_pulses = 200
        self.active_channels = []
        self.measurement = []
        self.measuring = False
        self.average_power = []
        self.average_power_wavelength = []
        self.average_power_multiple = []
        self.offset = None
        self.init_laser()
        self.init_digitizer()

    def init_laser(self):
        self.laser.connect()

    def init_digitizer(self):
        powermeter_channel = 1
        powermeter_dc_offset = 10
        self.digitizer.set_channel_gain(channel=powermeter_channel, value=1)
        self.digitizer.record_length = 0
        self.digitizer.max_num_events = 10
        self.digitizer.post_trigger_size = 90
        self.digitizer.acquisition_mode = CAENlib.AcqMode.SW_CONTROLLED
        channels = {powermeter_channel: powermeter_dc_offset}
        # Program the Digitizer
        self.digitizer.active_channels = channels.keys()
        for channel, dc_offset in channels.items():
            self.digitizer.set_dc_offset(channel, dc_offset)

        self.digitizer.external_trigger_mode = CAENlib.TriggerMode.ACQ_ONLY
        self.digitizer.external_trigger_level = CAENlib.IOLevel.TTL
        self.active_channels = list(self.digitizer.active_channels)

    def aver_measure(self):
        t1 = time.time()
        measurement = np.array([])
        while measurement.shape[-1] < self.number_of_pulses:
            data = self.digitizer.measure()
            processed_data = sum_signal(data, self.active_channels)
            if not len(measurement):
                measurement = processed_data
            else:
                measurement = np.hstack((measurement, processed_data))

        if not len(self.average_power):
            self.average_power = measurement
            self.average_power_wavelength = self.laser.wavelength
        else:
            self.average_power = np.vstack((self.average_power, measurement))
            self.average_power_wavelength = np.hstack((self.average_power_wavelength, self.laser.wavelength))
        t2 = time.time()
        print(f'time elapsed digitizer measurement = {t2-t1:.2f} seconds')

    def single_measure(self):
        data = self.digitizer.measure()
        data, offset = clean_signal(data, self.active_channels)
        self.measurement = data[0][0][:]
        self.offset = offset[0][0][0]

    def clear_average(self):
        self.average_power = []
        self.average_power_wavelength = []

    def power_measurement(self, wl_start, wl_stop, wl_step):
        wavelengths = np.arange(wl_start, wl_stop, wl_step)
        for wl in wavelengths:
            pm.laser.wavelength = wl
            while not self.laser.is_stable():
                time.sleep(0.1)
            print(f'laser stable at {wl} nm')
            self.aver_measure()

    def measure_continuously(self):
        fig, ax = plt.subplots()
        fig.canvas.mpl_connect('close_event', self.on_close)
        ax.set_xlabel('sample')
        ax.set_ylabel('adc value')
        self.measuring = True
        while self.measuring:
            ax.clear()
            self.single_measure()
            ax.plot(self.measurement, label='data')
            ax.set_title(f'single measurement, adc offset = {self.offset:.0f}')
            plt.pause(0.1)

    def on_close(self, event):
        self.measuring = False

    def multiple_aver_measure(self, wl_start, wl_stop, wl_step, repeat):
        repeat = repeat
        self.average_power_multiple = []
        for measurement in range(repeat):
            self.clear_average()
            self.power_measurement(wl_start, wl_stop, wl_step)
            if not len(self.average_power_multiple):
                self.average_power_multiple = np.mean(self.average_power, axis=1)
            else:
                self.average_power_multiple = np.vstack((self.average_power_multiple, np.mean(self.average_power, axis=1)))

    def multiple_aver_measure_plot(self):
        fig, ax = plt.subplots()
        ax.set_xlabel('wavelength [nm]')
        ax.set_ylabel('counts')
        ax.set_title(f'multiple power measurements, {self.number_of_pulses} pulses per wavelength')
        for index, _ in enumerate(pm.average_power_multiple[:, 0]):
            ax.plot(pm.average_power_wavelength, pm.average_power_multiple[index], label=f'measurement{index}')
        ax.legend()


pm = PowerMeasurement()
