import numpy as np
import pandas
import csv
import pandas as pd
from pathlib import Path

xdata = np.zeros(100)

df = pd.DataFrame({'xdata': xdata})
df.to_csv('C:/Users/bauke/OneDrive/Bureaublad/TestfilesXY/yoyo.csv', index=False)

try:
    df1 = pd.read_csv('C:/Users/bauke/OneDrive/Bureaublad/BeamSplitter_Calibrations/BS20WR_300_350_nm_2109151617.csv')
except FileNotFoundError as e:
    print('file not found')
