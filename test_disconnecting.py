from instruments.Thorlabs.qpowermeter import QPowerMeter
from PyQt5.QtCore import pyqtSlot

pm = QPowerMeter()
pm.connect()


@pyqtSlot()
def testfunction():
    print('shizzle measurement done')



