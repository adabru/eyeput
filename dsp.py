from collections import deque

import numpy as np

from settings import *

# registers a blink if eye was shortly invalid and revalidated
class BlinkFilter:
    # False = closed
    lid = (False, False)
    # timestamp of last closing/opening
    t_closed = [0, 0]
    t_opened = [0, 0]
    will_trigger = [False, False]

    def transform(self, t, l0, l1, r0, r1):
        lid = (l0 != 0.0 or l1 != 0.0, r0 != 0.0 or r1 != 0.0)
        blink = [False, False]
        for i in [0, 1]:
            if lid[i] and self.lid[i]:
                if self.will_trigger[i] and t - self.t_opened[i] > 0.05:
                    blink[i] = True
                    self.will_trigger[i] = False
            elif not lid[i] and self.lid[i]:
                self.t_closed[i] = t
                self.will_trigger[i] = False
            elif lid[i] and not self.lid[i]:
                self.t_opened[i] = t
                if t - self.t_closed[i] < 0.3:
                    self.will_trigger[i] = True
        # smooth both eyes blinking
        if blink[0] != blink[1] and self.will_trigger[0] != self.will_trigger[1]:
            blink[0] = True
            blink[1] = True
            self.will_trigger[0] = False
            self.will_trigger[1] = False
        self.lid = lid
        return blink


class _Filter:
    def __init__(self, window):
        self.window = window
        self.buffer = np.zeros(window)

    def transform(self, x):
        self.buffer = np.roll(self.buffer, -1)
        self.buffer[-1] = x
        return self._transform(x)


class MovingAverage(_Filter):
    def __init__(self, *args):
        super().__init__(*args)

    def _transform(self, x):
        return np.average(self.buffer)


class Median(_Filter):
    def __init__(self, *args):
        super().__init__(*args)

    def _transform(self, x):
        return np.median(self.buffer)


# assume measurements are distributed in a circle
class CircleFilter(_Filter):
    def __init__(self, radius, *args):
        super().__init__(*args)
        self.radius = radius
        self.last_center = 0.0

    def _transform(self, x):
        l = r = c = x
        for x in self.buffer[::-1]:
            if abs(c - x) > self.radius:
                break
            l = min(l, x)
            r = max(r, x)
            c = 0.5 * (l + r)
        # a little drift accommodation
        if abs(self.last_center - c) < self.radius:
            return self.last_center
        self.last_center = c
        return c


class LowFilter(_Filter):
    def __init__(self, *args):
        super().__init__(*args)

    def _transform(self, x):
        spectrum = np.fft.rfft(self.buffer)
        spectrum[-5:] = 0.0
        _buffer = np.fft.irfft(spectrum, len(self.buffer))
        return _buffer[-1]


# moving average
class GazeFilter:
    x = CircleFilter(0.005, 20)
    y = CircleFilter(0.01, 20)

    def transform(self, t, l0, l1, r0, r1):
        if l0 == 0.0 and l1 == 0.0:
            return (0.0, 0.0)
        else:
            return (self.x.transform(l0), self.y.transform(l1))
