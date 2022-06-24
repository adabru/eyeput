from collections import deque

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


class MovingAverage:
    def __init__(self, window):
        self.window = window
        self.buffer = deque()
        self.sum = 0.0

    def transform(self, x):
        self.buffer.append(x)
        self.sum += x
        if len(self.buffer) > self.window:
            self.sum -= self.buffer.popleft()
        return self.sum / len(self.buffer)


class LowFilter:
    def __init__(self, window):
        self.window = window
        self.buffer = deque()
        self.sum = 0.0

    def transform(self, x):
        self.buffer.append(x)
        self.sum += x
        if len(self.buffer) > self.window:
            self.sum -= self.buffer.popleft()
        return self.sum / len(self.buffer)


# moving average
class GazeFilter:
    x = MovingAverage(30)
    y = MovingAverage(30)

    def transform(self, t, l0, l1, r0, r1):
        if l0 == 0.0 and l1 == 0.0:
            return (0.0, 0.0)
        else:
            return (self.x.transform(l0), self.y.transform(l1))
