from netCDF4 import Dataset
import time
import numpy as np


storage_dir = 'C:/Users/bauke/OneDrive/Bureaublad/TestfilesXY'
sample = 'BK77'

fname = f'{storage_dir}/{sample}'

startingtime = time.time()

experiment = 'decay'
experimentdate = time.strftime("%y%m%d%H%M", time.localtime(startingtime))
# Open a new datafile and create an experiment folder
dataset = Dataset(f'{fname}.hdf5', 'w', format='NETCDF4')
dataset.createGroup(f'{experiment}_{experimentdate}')

dataset.createDimension('x', 10)
dataset.createDimension('y', 20)
temp = dataset.createVariable('data', 'f8', ('x', 'y',))

temp[:, :] = np.zeros((10, 20))

