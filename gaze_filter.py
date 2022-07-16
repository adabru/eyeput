from collections import deque
from itertools import islice

import numpy as np

from settings import *


# recognize blink patterns
# closing and opening brackets from both eyes are synchronized, limited by the latency
# available patterns, e.g:
#
#      ".r." ".l." ". ."   ". r r ."    ". l ."
# left  ███         ▒█▒  ▒██  ███  ██▒  ▒██████▒
# right       ███   ▒█▒  ▒███████████▒  ▒██  ██▒
#
# a blink is only recognized on every closing bracket; it doesn't matter whether the eye starts closed or opened
#
# defining a limited set of available patterns reduces latency
class BlinkFilter:
    def __init__(self, latency, sync_latency):
        self.latency = latency
        self.sync_latency = sync_latency

    flips = "."
    last_flip_time = 0
    prefix_tree = {}

    def decode(self, pattern):
        return {
            ".": {"l": True, "r": True},
            "l": {"l": True, "r": False},
            "r": {"l": False, "r": True},
            " ": {"l": False, "r": False},
        }[pattern]

    def encode(self, pair):
        return {
            (True, True): ".",
            (True, False): "l",
            (False, True): "r",
            (False, False): " ",
        }[(pair["l"], pair["r"])]

    def set_blink_patterns(self, blink_patterns):
        # build prefix tree
        self.prefix_tree = {}
        for p in blink_patterns:
            for i in range(1, len(p) + 1):
                if not p[:i] in self.prefix_tree:
                    self.prefix_tree[p[:i]] = {p}
                else:
                    self.prefix_tree[p[:i]].add(p)

    def check_flip(self, t, buffer, eye):
        current_flip = self.decode(self.flips[-1])
        opened = buffer[-1].any()
        # a little debounce
        if opened != current_flip[eye] and buffer[-2].any() == opened:
            current_flip[eye] = opened
            # sync both eyes
            if (
                len(self.flips) >= 2
                and t[-2] - self.last_flip_time < self.sync_latency
                and self.decode(self.flips[-2])[eye] != current_flip[eye]
            ):
                self.flips = self.flips[:-1] + self.encode(current_flip)
            else:
                self.flips += self.encode(current_flip)
            self.last_flip_time = t[-2]

    def transform(self, t, left, right):
        # recognize flip
        self.check_flip(t, left, "l")
        self.check_flip(t, right, "r")
        dt = t[-1] - self.last_flip_time
        if dt < self.sync_latency:
            return ""
        # emit when reaching leaf or blink latency
        if (
            self.flips in self.prefix_tree
            and self.flips in self.prefix_tree[self.flips]
            and (dt > self.latency or len(self.prefix_tree[self.flips]) == 1)
        ):
            result = self.flips
            self.flips = self.flips[-1:]
            return result
        # preemptively cancel unregistered blink
        if not self.flips in self.prefix_tree:
            self.flips = self.flips[-1:]
        return ""
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
    blink_filter = BlinkFilter(0.22, 0.05)
    flicker_filter = FlickerFilter(0.7 * np.array((0.02, 0.02)), 5)
    # flicker_filter = VarianceFilter(5, 0.02)

    def transform(self, t, l0, l1, r0, r1, position=True, blink=True, variance=True):
        self.t.append(t)
        t = self.t
        self.left.append(np.array((l0, l1)))
        left = self.left
        self.right.append(np.array((r0, r1)))
        right = self.right
        [x, y] = left[-1]
        if position:
            [x, y] = self.pointer_filter.transform(t, left, right)
        [l_variance, r_variance] = [1 * (l0), 1]
        if variance:
            [l_variance, r_variance] = self.flicker_filter.transform(t, left, right)
        b = ""
        if blink:
            b = self.blink_filter.transform(t, left, right)

        # import timeit
        # _time = lambda n, f: print(timeit.timeit(f, number=n))
        # _time(3000, lambda: self.t.append(t[-1]))
        # _time(1000, lambda: self.pointer_filter.transform(t, left, right))
        # _time(1000, lambda: self.blink_filter.transform(t, left, right))
        # _time(1000, lambda: self.flicker_filter.transform(t, left, right))
        return [x, y, b, l_variance, r_variance]

    def set_blink_patterns(self, blink_patterns):
        self.blink_filter.set_blink_patterns(blink_patterns)
