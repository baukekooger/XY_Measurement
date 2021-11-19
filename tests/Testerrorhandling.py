from instruments.Thorlabs.qpowermeter import QPowerMeter
from instruments.CAEN.Qdigitizer import QDigitizer
from instruments.Thorlabs.shuttercontrollers import QShutterControl
from instruments.Ekspla.lasers import QLaser

test = QLaser()

condition = True


def testfunction():
    for number in range(2):
        print(number)
        if condition:
            try:
                test.connect()
            except ConnectionError as e:
                print(e)
            return



