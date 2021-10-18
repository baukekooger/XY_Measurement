import numpy as np
import scipy.ndimage as sp
import time


treshold = 5
channels = 3
samples = 1000

data = np.random.randint(10, dtype=np.ushort, size=samples)
data = np.tile(data, (channels, 1))
tnpbf = time.perf_counter_ns()
data_treshold = data > treshold
filter_sp = np.tile([1, 0], (channels, 1))
data_corrected = data_treshold > sp.maximum_filter(
    data_treshold, footprint=filter_sp, mode='constant', cval=-np.inf)

# filter_check = np.asarray([1, 1])
# data_check = data_corrected > sp.maximum_filter(data_corrected,
#                                                 footprint=filter_check, mode='constant', cval=-np.inf)



