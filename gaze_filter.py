from collections import deque
from itertools import islice
from pathlib import Path
import pickle

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
    flip_times = [0]
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
                and t[-2] - self.flip_times[-1] < self.sync_latency
                and self.decode(self.flips[-2])[eye] != current_flip[eye]
            ):
                self.flips = self.flips[:-1] + self.encode(current_flip)
                self.flip_times[-1] = t[-2]
            else:
                self.flips += self.encode(current_flip)
                self.flip_times.append(t[-2])

    def transform(self, t, left, right):
        # recognize flip
        self.check_flip(t, left, "l")
        self.check_flip(t, right, "r")
        dt = t[-1] - self.flip_times[-1]
        if dt < self.sync_latency:
            return (None, None)
        # emit when reaching leaf or blink latency
        if (
            self.flips in self.prefix_tree
            and self.flips in self.prefix_tree[self.flips]
            and (dt > self.latency or len(self.prefix_tree[self.flips]) == 1)
        ):
            if len(self.flips) == 1:
                return (self.flips, self.flip_times[0])
            result = (self.flips, self.flip_times[1])
            self.flips = self.flips[-1:]
            self.flip_times = self.flip_times[-1:]
            return result
        # preemptively cancel unregistered blink
        if not self.flips in self.prefix_tree:
            self.flips = self.flips[-1:]
            self.flip_times = self.flip_times[-1:]
        return (None, None)
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
            if not right[-1].any():
                return left[-1]
            else:
                return self.left_filter.transform(right, self.lookbehind, self.radius)
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


class ProjectionFilter:
    screen_size_mm = (344.0, 193.0)
    calibration = []

    def __init__(self, label):
        self.calibration_path = Path("~/.cache/eyeput", label).expanduser()
        self.calibration_path.parent.mkdir(exist_ok=True, parents=True)
        try:
            with self.calibration_path.open("rb") as file:
                self.calibration = pickle.load(file)
        except FileNotFoundError as e:
            self.calibration = []

    def add_calibration_point(self):
        with self.calibration_path.open("wb") as file:
            pickle.dump(self.calibration, file, pickle.HIGHEST_PROTOCOL)

    def transform(self, t, v0, v1):
        # eye closed or offscreen
        if not v1[-1].any():
            return np.array((0.0, 0.0))
        # project to zero plane
        x = v1[-1][0] / self.screen_size_mm[0] + 0.5
        y = -v1[-1][1] / self.screen_size_mm[1] + 1.0
        return np.array((x, y))


class GazeFilter:
    t = deque([0] * 50, 50)
    # eye position relative to tracker [mm]
    l0 = deque([np.array((0.0, 0.0, 0.0))] * 50, 50)
    # gaze destination relative to tracker [mm]
    l1 = deque([np.array((0.0, 0.0, 0.0))] * 50, 50)
    r0 = deque([np.array((0.0, 0.0, 0.0))] * 50, 50)
    r1 = deque([np.array((0.0, 0.0, 0.0))] * 50, 50)
    # screen position, 0=top-left 1=bottom-right
    left = deque([np.array((0.0, 0.0))] * 50, 50)
    right = deque([np.array((0.0, 0.0))] * 50, 50)
    filtered_position = deque([np.array((0.0, 0.0))] * 50, 50)

    projection_filter_left = ProjectionFilter("left")
    projection_filter_right = ProjectionFilter("right")
    pointer_filter = PointerFilter(np.array((0.02, 0.02)), 20)
    blink_filter = BlinkFilter(0.16, 0.04)
    flicker_filter = FlickerFilter(0.7 * np.array((0.02, 0.02)), 5)
    # flicker_filter = VarianceFilter(5, 0.02)

    def transform(self, t, l0, l1, r0, r1, position=True, blink=True, variance=True):
        self.t.append(t)
        t = self.t
        self.l0.append(np.array(l0))
        self.l1.append(np.array(l1))
        self.r0.append(np.array(r0))
        self.r1.append(np.array(r1))
        _left = self.projection_filter_left.transform(t, self.l0, self.l1)
        self.left.append(_left)
        left = self.left
        _right = self.projection_filter_right.transform(t, self.r0, self.r1)
        self.right.append(_right)
        right = self.right
        [x, y] = left[-1]
        if position:
            [x, y] = self.pointer_filter.transform(t, left, right)
        self.filtered_position.append(np.array((x, y)))
        filtered_position = self.filtered_position
        [l_variance, r_variance] = [1 * (l0), 1]
        if variance:
            [l_variance, r_variance] = self.flicker_filter.transform(t, left, right)
        (flips, flip_position) = (None, None)
        if blink:
            (flips, flip_time) = self.blink_filter.transform(t, left, right)
        if flip_time:
            for (_t, _position) in zip(reversed(t), reversed(filtered_position)):
                if _t < flip_time - 0.05:
                    flip_position = _position
                    break

        # import timeit
        # _time = lambda n, f: print(timeit.timeit(f, number=n))
        # _time(3000, lambda: self.t.append(t[-1]))
        # _time(1000, lambda: self.pointer_filter.transform(t, left, right))
        # _time(1000, lambda: self.blink_filter.transform(t, left, right))
        # _time(1000, lambda: self.flicker_filter.transform(t, left, right))
        return [x, y, flips, flip_position, l_variance, r_variance]

    def set_blink_patterns(self, blink_patterns):
        self.blink_filter.set_blink_patterns(blink_patterns)
