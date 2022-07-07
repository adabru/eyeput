from collections import deque
from itertools import islice

import numpy as np

from settings import *


# registers a blink if eye was shortly invalid and revalidated
class BlinkFilter:
    l_block = 0
    r_block = 0

    def check_blink(self, buffer, max_closed, max_opened):
        from_behind = reversed(buffer)
        # eye must be opened
        if not next(from_behind).any():
            return 0
        # but only for a short time
        n_opened = 1
        while next(from_behind).any():
            n_opened += 1
            if n_opened > max_opened:
                return 0
        # before that it mustn't be closed long
        n_closed = 1
        while not next(from_behind).any():
            n_closed += 1
            if n_closed > max_closed:
                return 0
        return n_opened

    def is_closed(self, buffer):
        return not buffer[-1].any()

    def transform(self, t, left, right):
        self.l_block = max(self.l_block - 1, 0)
        self.r_block = max(self.r_block - 1, 0)
        # check if both eyes blinked
        if (
            not self.l_block
            and self.check_blink(left, 25, 5) > 0
            and not self.r_block
            and self.check_blink(right, 25, 5) > 0
        ):
            self.l_block = 19
            self.r_block = 19
            return [True, True]
        elif (
            not self.l_block
            and self.check_blink(left, 20, 5) == 5
            and not self.is_closed(right)
        ):
            self.l_block = 19
            return [True, False]
        elif (
            not self.r_block
            and self.check_blink(right, 20, 5) == 5
            and not self.is_closed(left)
        ):
            self.r_block = 19
            return [False, True]
        else:
            return [False, False]
        # todo: variance filters closing eyelid


class PointerFilter:

    # assume measurements are distributed in a circle

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
    blink_filter = BlinkFilter()
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
        [l_blink, r_blink] = self.blink_filter.transform(t, left, right)
        [l_variance, r_variance] = self.flicker_filter.transform(t, left, right)
        # import timeit
        # _time = lambda n, f: print(timeit.timeit(f, number=n))
        # _time(3000, lambda: self.t.append(t[-1]))
        # _time(1000, lambda: self.pointer_filter.transform(t, left, right))
        # _time(1000, lambda: self.blink_filter.transform(t, left, right))
        # _time(1000, lambda: self.flicker_filter.transform(t, left, right))
        # print(x, y, l_blink, r_blink, l_variance, r_variance)
        return [x, y, l_blink, r_blink, l_variance, r_variance]
