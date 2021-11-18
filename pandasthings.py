import pandas as pd
import numpy as np

wl = np.repeat(210, 10)
position = np.repeat(1, 10)
power = np.random.randint(0, 10, 10)
times = np.arange(0, 10)


df_empty = pd.DataFrame(columns=['Wavelength [nm]', 'Position', 'Power [W]', 'Time [s]'])

df_add = pd.DataFrame({'Wavelength [nm]': wl, 'Position': position, 'Power [W]': power, 'Time [s]': times})

df_total = df_empty.append(df_add)