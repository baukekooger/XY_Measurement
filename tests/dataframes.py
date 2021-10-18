import numpy as np
import pandas as pd


df = pd.read_csv('C:/Users/bauke/OneDrive/Bureaublad/BeamSplitter_Calibrations/BS20WR_250_10_270_nm_2109211742.csv')

power = df[df.keys()[1]]

power = [powerstring.replace('[', '') for powerstring in power]
power = [powerstring.replace(']', '') for powerstring in power]
power = [powerstring.split(',') for powerstring in power]
# power = list(power)

power = [[float(powervalue) for powervalue in row] for row in power]
