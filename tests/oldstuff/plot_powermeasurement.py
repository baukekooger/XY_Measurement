import pickle
import matplotlib.pyplot as plt
import numpy as np

with open('powermeasurement.pkl', 'rb') as f:
    powers, times, wavelengths = pickle.load(f)

fig, ax = plt.subplots()


def plot_single_wl(wl):
    index = np.where(wavelengths == wl)[0][0]
    ax.plot(times[index, :], powers[index, :]*1000, label=wl)
    ax.set_xlabel('time [s]')
    ax.set_ylabel('power [mW]')
    ax.set_title('power over time for single wavelength measurement')
    ax.legend()


def plot_wavelength_average(**kwargs):
    if 'tstart' in kwargs and 'tstop' in kwargs:
        tstart = kwargs['tstart']
        tstop = kwargs['tstop']
    else:
        tstart = 0
        tstop = 5
    index_start = np.where(times[0, :] > tstart)[0][0]
    index_stop = np.where(times[0, :] < tstop)[-1][-1]
    mean_power = [1000*np.mean(powers[index_wl, index_start:index_stop]) for index_wl, _ in enumerate(wavelengths)]
    ax.plot(wavelengths, mean_power, label=f't = {tstart} till t = {tstop}')
    ax.set_title('Power over wavelength for different time spans')
    ax.set_ylabel('Power [mW]')
    ax.set_xlabel('Wavelength [nm]')
    ax.legend()
