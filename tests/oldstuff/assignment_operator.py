import numpy as np

a = np.ones(1000)
if (samples := len(a)) > 100:
    print(samples)

data = np.array([1, 2, 3])
if maxdata := np.max(data):
    data = data/maxdata

a = np.zeros(1000)
b = np.random.randint(0, 6, 1000)
c = np.vstack((a, b))


data, jitter = (c[0], c[1]) if any(c[0]) else (0, 0)



