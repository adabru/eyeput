# first phase calibration is done in Tobias sdk
# https://tobiitech.github.io/stream-engine-docs/#see-also-46
# ~/downloads/talon-linux/talon/resources/python/lib/python3.9/site-packages/talon/track/tobii.pyi


from collections import deque
from pathlib import Path
import pickle

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPixmap, QColor
from PyQt5.QtCore import Qt, QPoint, QPointF, QRect, QTimer, pyqtSignal

import numpy as np

from util import *
from gaze_filter import *

screen_size_mm = (344.0, 193.0)

x1 = 0.05
x2 = 0.95
y1 = 0.05
y2 = 0.95
calibration_points = [
    vec(x1, y1),
    vec(x2, y1),
    vec(x1, y2),
    vec(x2, y2),
]


class LookAtMe(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(0, 0, 10, 10)
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(255, 255, 0, 255))
        painter.drawRect(QRect(0, 0, 20, 20))


class EyeMarker(QWidget):
    def __init__(self, parent, color):
        super().__init__(parent)
        self.color = color
        self.setGeometry(0, 0, 10, 10)
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(self.color)
        painter.drawRect(QRect(0, 0, 20, 20))


class EyeCalibration:
    def __init__(self, parent, label, color):
        self.marker = EyeMarker(parent, color)
        self.marker.show()
        self.last_reference = None
        self.position_buffer = deque(maxlen=30)
        self.corrections = []

        self.calibration_path = Path("~/.cache/eyeput", label).expanduser()
        self.calibration_path.parent.mkdir(exist_ok=True, parents=True)
        try:
            with self.calibration_path.open("rb") as file:
                self.calibration_vector = pickle.load(file)
        except FileNotFoundError as e:
            self.calibration_vector = None

    def add_calibration_point(self):
        with self.calibration_path.open("wb") as file:
            pickle.dump(self.calibration_vector, file, pickle.HIGHEST_PROTOCOL)

    def transform(self, t, v0, v1):
        screen_position = vec(
            v1[-1][0] / screen_size_mm[0] + 0.5,
            -v1[-1][1] / screen_size_mm[1] + 1.0,
        )
        # initial guess: project to zero plane
        if self.calibration_vector is None:
            return screen_position
        # https://en.wikipedia.org/wiki/Bilinear_interpolation#Repeated_linear_interpolation
        # https://en.wikipedia.org/wiki/Bilinear_interpolation#Weighted_mean
        else:
            x = vec(x2 - screen_position[0], screen_position[0] - x1)
            y = vec(y2 - screen_position[1], screen_position[1] - y1)
            # somehow the following line yields the wrong result:
            # correction = x @ Q @ y
            # weights take 8 instead of 6 multiplications but are easier to examine
            weights = np.array((x[0] * y[0], x[0] * y[1], x[1] * y[0], x[1] * y[1]))
            correction = weights @ self.calibration_vector
            return screen_position + correction

    def start(self):
        self.corrections.clear()
        self.position_buffer.clear()

    def next(self):
        self.corrections.append(self.correction)
        self.position_buffer.clear()

    def finalize(self):
        self.next()
        self.calibration_vector = np.array(self.corrections) / (x2 - x1) / (y2 - y1)

    def on_gaze(self, reference, screen_position, take, test, radius):
        # calculate new correction
        self.position_buffer.append(screen_position)
        mean = np.mean(slice(self.position_buffer, -take), axis=0)
        self.correction = reference - mean
        distance = np.linalg.norm(
            slice(self.position_buffer, -(take + test)) + self.correction - reference,
            axis=1,
        )

        # decide whether this reference point has completed
        self.is_ok = len(self.position_buffer) >= take + test and np.all(
            distance < radius
        )

        # visualize current corrected position
        self.marker.move(rel2abs(screen_position + self.correction))


class Calibration(QWidget):
    end_signal = pyqtSignal()

    def __init__(self, parent, geometry):
        super().__init__(parent)
        self.setGeometry(geometry)
        self.lookatme = LookAtMe(self)
        self.lookatme.show()
        self.left = EyeCalibration(self, "left", QColor("lime"))
        self.right = EyeCalibration(self, "right", QColor("red"))
        self.hide()

    def get(self, label):
        if label == "left":
            return self.left
        else:
            return self.right

    def start(self):
        self.counter = 0
        self.show()
        self.left.start()
        self.right.start()
        position = rel2abs(calibration_points[self.counter])
        self.lookatme.move(position)

    def next_point(self):
        self.show()
        self.counter += 1
        position = rel2abs(calibration_points[self.counter])
        self.lookatme.move(position)
        self.left.next()
        self.right.next()

    def finalize_point(self):
        self.hide()
        if self.counter == len(calibration_points) - 1:
            self.finalize()

    def cancel(self):
        self.hide()

    def finalize(self):
        self.end_signal.emit()
        self.left.finalize()
        self.right.finalize()

    def on_frame(self, frame: FilteredFrame):
        if self.isVisible():
            reference = calibration_points[self.counter]
            self.left.on_gaze(reference, frame.l_screen_position, 15, 5, 0.02)
            self.right.on_gaze(reference, frame.r_screen_position, 15, 5, 0.02)
            # proceed with next point
            if self.left.is_ok and self.right.is_ok:
                self.finalize_point()
