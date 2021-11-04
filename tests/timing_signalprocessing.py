import time
import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage.interpolation as sp

veclen = 1_000

a_00 = np.ones(veclen)*8000
a_01 = np.ones(veclen)*6500
a_02 = np.ones(veclen)*8000

data = np.hstack((a_00, a_01, a_02))

fig, ax = plt.subplots()

shift = -3
tstart = time.perf_counter()
if shift == 0:
    pass
# data is shifted, data outside boundary replaced with neighbour value. This is acceptable because
# shift is maximum one sample
elif shift > 0:
    data = np.hstack((data[(shift - 1):-1], np.ones(shift) * data[-1]))
else:
    shift = abs(shift)
    data = np.hstack((np.ones(shift) * data[0], data[0:-shift]))

tstop = time.perf_counter()

