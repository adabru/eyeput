from collections import deque

import numpy as np

from settings import *


class Buffer:
    def __init__(self, size):
        self.size = size
        self.buffer = np.zeros(size)

    def push(self, x):
        self.buffer = np.roll(self.buffer, -1)
        self.buffer[-1] = x

    def reset(self):
        self.buffer = np.zeros(self.size)


class _Filter(Buffer):
    def __init__(self, window):
        super().__init__(window)

    def transform(self, x):
        self.push(x)
        return self._transform(x)


# registers a blink if eye was shortly invalid and revalidated
class BlinkFilter:
    # just buffer
    left = Buffer(50)
    right = Buffer(50)

    def check_blink(self, buffer, n_closed, n_opened):
        from_behind = np.flip(buffer)
        n_non_zero = 0
        for i in range(len(from_behind)):
            if not from_behind[i]:
                break
            n_non_zero += 1
        if not (0 < n_non_zero and n_non_zero <= n_opened):
            return 0
        n_zero = 0
        for i in range(n_non_zero, len(from_behind) - n_non_zero):
            if from_behind[i]:
                break
            n_zero += 1
        if not (0 < n_zero and n_zero <= n_closed):
            return 0
        return n_non_zero
        # return (
        #     np.all(buffer[-n_opened :])
        #     and not buffer[-1 - n_opened]
        #     and np.any(buffer[-n_closed - n_opened : -n_opened])
        # )

    def is_closed(self, buffer):
        return buffer[-1] == 0

    def transform(self, t, l0, l1, r0, r1):
        self.left.push(l0)
        self.right.push(r0)
        left = self.left.buffer
        right = self.right.buffer
        # check if both eyes blinked
        if self.check_blink(left, 25, 5) > 0 and self.check_blink(right, 25, 5) > 0:
            self.left.reset()
            self.right.reset()
            return [True, True]
        elif self.check_blink(left, 20, 5) == 5 and not self.is_closed(right):
            self.left.reset()
            return [True, False]
        elif self.check_blink(right, 20, 5) == 5 and not self.is_closed(left):
            self.right.reset()
            return [False, True]
        else:
            return [False, False]
        # # variance filters closing eyelid
        # std = np.std(self.buffer[-4:])
        # if std / self.radius > 0.4:
        #     return self.last_center


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
        # find last circle
        l = r = c = x
        for x in self.buffer[::-1]:
            if abs(c - x) > self.radius:
                break
            l = min(l, x)
            r = max(r, x)
            c = 0.5 * (l + r)
        # slight drift accommodation
        if abs(self.last_center - c) < self.radius:
            return self.last_center
        self.last_center = c
        return c


# moving average
class GazeFilter:
    x = CircleFilter(0.005, 20)
    y = CircleFilter(0.01, 20)

    def transform(self, t, l0, l1, r0, r1):
        if l0 == 0.0 and l1 == 0.0:
            return (0.0, 0.0)
        else:
            return (self.x.transform(l0), self.y.transform(l1))
