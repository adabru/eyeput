import os.path

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QObject, pyqtSlot, pyqtSignal

from settings import *

cursor = 0
N = 50
data = {key: np.zeros(N) for key in ["l0", "l1", "x", "y"]}
plot_data = {key: None for key in ["l0", "l1", "l0l1", "x", "y", "xy"]}


class PixelRange:
    def __init__(self, range_setter, width, data):
        self.range_setter = range_setter
        self.data = data
        self.offset = 0
        self.width = width

    def update(self):
        self.range_setter(*self._get_range(), update=False)

    def _get_range(self):
        if self.data[cursor] > self.offset + self.width:
            self.offset = self.data[cursor] + self.width * 0.2
        if self.data[cursor] < self.offset:
            self.offset = self.data[cursor] - self.width * 0.2
        return [self.offset, self.offset + self.width]


class Graph(QObject):
    gaze_signal = pyqtSignal(float, float, float, float, float, float, float)

    def __init__(self):
        super().__init__()

    def setup(self):
        self.gaze_signal.connect(self.addPoint, Qt.QueuedConnection)

        self.win = pg.GraphicsLayoutWidget(show=True, title="GazeFilter")
        p1 = self.win.addPlot(row=0, col=0, title="x")
        p1.setXRange(0, N)
        p2 = self.win.addPlot(row=0, col=1, title="y")
        p2.setXRange(0, N)
        p3 = self.win.addPlot(row=1, col=0, colspan=2, title="xy")
        for p in [p1, p2, p3]:
            p.disableAutoRange()
            p.hideAxis("left")
            p.hideAxis("bottom")
        plot_data["l0"] = p1.plot(pen=pg.mkPen("#f88"))
        plot_data["l1"] = p2.plot(pen=pg.mkPen("#f88"))
        plot_data["l0l1"] = pg.ScatterPlotItem(
            size=2, pen=pg.mkPen(None), brush=pg.mkBrush("#f888")
        )
        p3.addItem(plot_data["l0l1"])
        plot_data["x"] = p1.plot(pen=pg.mkPen("#8f8"))
        plot_data["y"] = p2.plot(pen=pg.mkPen("#8f8"))
        plot_data["xy"] = pg.ScatterPlotItem(
            size=2, pen=pg.mkPen(None), brush=pg.mkBrush("#8f88")
        )
        p3.addItem(plot_data["xy"])

        self.ranges = [
            PixelRange(p1.setYRange, 0.1, data["l0"]),
            PixelRange(p2.setYRange, 0.1, data["l1"]),
            PixelRange(p3.setXRange, 0.4, data["l0"]),
            PixelRange(p3.setYRange, 0.2, data["l1"]),
        ]

        self.update()

    def update(self):
        for range in self.ranges:
            range.update()
        plot_data["l0l1"].setData(data["l0"], data["l1"])
        plot_data["l0"].setData(data["l0"])
        plot_data["l1"].setData(data["l1"])
        plot_data["xy"].setData(data["x"], data["y"])
        plot_data["x"].setData(data["x"])
        plot_data["y"].setData(data["y"])

    # must be called and qt thread to prevent concurrent data manipulation (setData)
    @pyqtSlot(float, float, float, float, float, float, float)
    def addPoint(self, t, l0, l1, r0, r1, x, y):
        # skip invalid points
        if l0 == 0.0 and l1 == 0.0:
            return
        global cursor
        data["l0"][cursor] = l0
        data["l1"][cursor] = l1
        data["x"][cursor] = x
        data["y"][cursor] = y
        cursor = (cursor + 1) % N
        self.update()
