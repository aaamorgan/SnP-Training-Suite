from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import random
import time
import serial

ser = serial.Serial('/dev/ttyACM0', 9600)
s = [0]


app = QtGui.QApplication([])
x1 = np.array([-0.25, -0.25])
x2 = np.array([0.25, 0.25])
curve1 = np.array([0, 0.5])
curve2 = np.array([0, 0.5])
plot = pg.plot()
plot.setXRange(-0.5, 0.5)
plot.setYRange(0, 255)
plot.setLabel('left', 'Pressure', 'units')
# grid = pg.GridItem()
# plot.addItem(grid)
# x = np.linspace(0, 2)
curves1 = plot.plot(x=x1, y=curve1, pen='b')
curves2 = plot.plot(x=x2, y=curve2, pen='b')

zeroLine = pg.InfiniteLine(
    angle=0, pen=(127, 127, 127, 127), label='0', labelOpts={'position': 0.1})
zeroLine.setValue(0)
plot.addItem(zeroLine)
targetPressure = pg.InfiniteLine(
    angle=0, pen='g', label='Hard Puff', labelOpts={'position': 0.1})
targetPressure.setValue(200)
plot.addItem(targetPressure)

offloadThreshold = pg.InfiniteLine(
    angle=0, pen='y', label='Soft Puff', labelOpts={'position': 0.1})
offloadThreshold.setValue(150)
plot.addItem(offloadThreshold)

outOfSeatThreshold = pg.InfiniteLine(
    angle=0, pen='m', label='Soft Sip', labelOpts={'position': 0.1})
outOfSeatThreshold.setValue(110)
plot.addItem(outOfSeatThreshold)

hardSip = pg.InfiniteLine(
    angle=0, pen='r', label='Hard Sip', labelOpts={'position': 0.1})
hardSip.setValue(50)
plot.addItem(hardSip)

fill = pg.FillBetweenItem(curves1, curves2, brush=(0, 0, 255))
plot.addItem(fill)

if __name__ == '__main__':
    while True:
        read_serial = ser.readline()
        try:
            s[0] = int(ser.readline(), 16)
            print(s[0])
            time.sleep(0.002)
            # data = [0, random.uniform(-1, 1)]
            curves1.setData(x=x1, y=np.array([131, s[0]]))
            curves2.setData(x=x2, y=np.array([131, s[0]]))
            QtGui.QApplication.processEvents()
        except ValueError:
            pass
        # time.sleep(0.5)
# app.exec_()
