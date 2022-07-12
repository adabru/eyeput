from collections import deque
from itertools import islice

import numpy as np

from settings import *


# recognize blink patterns
# closing and opening brackets from both eyes are synchronized, limited by the latency
# available patterns:
#
#        1    2    3    5    5    3    6    3
# left  ███       ▒█▒  ▒██  ███  ██▒  ▒██████▒
# right      ███  ▒█▒  ▒███████████▒  ▒██  ██▒
#
# a blink is only recognized on every closing bracket; it doesn't matter whether the eye starts closed or opened
class BlinkFilter:
    def __init__(self, latency):
        self.latency = latency

    flips = []
    last_flip = 0
    opened = {1: True, 2: True}

    def check_flip(self, t, buffer, eye):
        opened = buffer[-1].any()
        # a little debounce
        if (
            opened != self.opened[eye]
            and buffer[-2].any() == opened
            and buffer[-3].any() == opened
        ):
            self.opened[eye] = opened
            self.flips.append(eye)
            self.last_flip = t[-1]

    def transform(self, t, left, right):
        # recognize flip
        self.check_flip(t, left, 1)
        self.check_flip(t, right, 2)
        # process flips and emit
        blinks = []
        if len(self.flips) and t[-1] - self.last_flip > self.latency:
            l = r = False
            n = len(self.flips)
            i = 0
            while i < n:
                # left eye
                if self.flips[i] == 1:
                    # closing bracket, synchronize
                    if l and r and i + 1 < n and self.flips[i + 1] == 2:
                        blinks.append(3)
                        r = False
                        i += 1
                    # closing bracket, without right
                    elif l and not r:
                        blinks.append(1)
                    # closing bracket, with right
                    elif l and r:
                        blinks.append(5)
                    l = not l
                # right eye
                elif self.flips[i] == 2:
                    if r and l and i + 1 < n and self.flips[i + 1] == 1:
                        blinks.append(3)
                        l = False
                        i += 1
                    elif r and not l:
                        blinks.append(2)
                    elif r and l:
                        blinks.append(6)
                    r = not r
                i += 1
            blinks.append(self.opened[1] * 1 + self.opened[2] * 2)
            self.flips = []
        return blinks
        # todo: variance filters closing eyelid


# assume measurements are distributed in a circle
class PointerFilter:
    def __init__(self, radius, lookbehind):
        self.radius = radius
        self.lookbehind = lookbehind

    class CircleFilter:
        def __init__(self):
            self.last_center = np.array((0.0, 0.0))

        def _check_distance(self, u, v, radius):
            distance = np.linalg.norm((u - v) / radius)
            return distance < 1

        def transform(self, x, lookbehind, radius):
            # find last circle
            c = x[-1]
            sum = np.array(c)
            n = 1
            for v in islice(reversed(x), 1, lookbehind):
                if not self._check_distance(c, v, radius):
                    break
                sum += v
                n += 1
                c = sum / n
            # slight drift accommodation
            if self._check_distance(self.last_center, c, radius):
                c = self.last_center
            self.last_center = c

            return c

    left_filter = CircleFilter()

    def transform(self, t, left, right):
        if not left[-1].any():
            return left[-1]
        else:
            return self.left_filter.transform(left, self.lookbehind, self.radius)


class VarianceFilter:
    def __init__(self, lookbehind, radius):
        self.lookbehind = lookbehind
        self.radius = radius

    def _clamp(self, n, smallest, largest):
        return max(smallest, min(n, largest))

    def _get_factor(self, x):
        if not x[-1].any():
            return 0
        else:
            a = np.fromiter(
                reversed(x), dtype=np.dtype((float, 2)), count=self.lookbehind
            )
            deviation = np.sum(np.std(a, axis=0))
            return self._clamp(self.radius / deviation, 0, 1)

    def transform(self, t, left, right):
        # map to range [0=bad, 1=good]
        return (self._get_factor(left), self._get_factor(right))


class FlickerFilter:
    def __init__(self, radius, lookbehind):
        self.radius = radius
        self.lookbehind = lookbehind

    def _get_factor(self, x):
        if not x[-1].any():
            return 0
        else:
            a = np.fromiter(
                reversed(x), dtype=np.dtype((float, 2)), count=self.lookbehind
            )
            mean = np.mean(a, axis=0)
            distance = np.linalg.norm((a - mean) / self.radius, axis=1)
            return 0.1 + 0.9 * np.count_nonzero(distance < 1) / len(distance)

    def transform(self, t, left, right):
        # map to range [0=bad, 1=good]
        return (self._get_factor(left), self._get_factor(right))


class GazeFilter:
    t = deque([0] * 50, 50)
    left = deque([np.array((0.0, 0.0))] * 50, 50)
    right = deque([np.array((0.0, 0.0))] * 50, 50)

    pointer_filter = PointerFilter(np.array((0.02, 0.02)), 20)
    blink_filter = BlinkFilter(0.22)
    flicker_filter = FlickerFilter(0.7 * np.array((0.02, 0.02)), 5)
    # flicker_filter = VarianceFilter(5, 0.02)

    def transform(self, t, l0, l1, r0, r1):
        self.t.append(t)
        t = self.t
        self.left.append(np.array((l0, l1)))
        left = self.left
        self.right.append(np.array((r0, r1)))
        right = self.right
        [x, y] = self.pointer_filter.transform(t, left, right)
        [l_variance, r_variance] = self.flicker_filter.transform(t, left, right)
        blink = self.blink_filter.transform(t, left, right)
        # import timeit
        # _time = lambda n, f: print(timeit.timeit(f, number=n))
        # _time(3000, lambda: self.t.append(t[-1]))
        # _time(1000, lambda: self.pointer_filter.transform(t, left, right))
        # _time(1000, lambda: self.blink_filter.transform(t, left, right))
        # _time(1000, lambda: self.flicker_filter.transform(t, left, right))
        return [x, y, blink, l_variance, r_variance]
