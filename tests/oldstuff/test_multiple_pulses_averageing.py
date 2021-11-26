from instruments.CAEN.Qdigitizer import QDigitizer
import pickle

test = QDigitizer()
test.connect()

test.active_channels = [0]
multiple_singlechan = test.measure_multiple()
single_singlechan = test.measure()

test.active_channels = [0, 1]
multiple_multiplechan = test.measure_multiple()
single_multiplechan = test.measure()

with open('digimeaus.pkl', 'wb') as f:
    pickle.dump([multiple_singlechan, multiple_multiplechan, single_multiplechan, single_singlechan], f)


