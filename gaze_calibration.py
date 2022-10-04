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

screen_size_mm = vec(344.0, -193.0)

calibration_points = [
    vec(0.05, 0.05),
    vec(0.95, 0.05),
    vec(0.5, 0.95),
]


@dataclass
class CalibrationData:
    T: np.ndarray = None
    r3: np.ndarray = None

    # properties used for faster computation
    Ti: np.ndarray = None
    l: np.ndarray = None

    # there's quite a performance penalty for a generic solution
    def __iter__(self):
        return iter((self.T, self.r3, self.Ti, self.l))


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
    calibration_data: CalibrationData

    def __init__(self, parent, label, color):
        self.marker = EyeMarker(parent, color)
        self.marker.show()
        self.last_reference = None
        self.position_buffer = deque(maxlen=30)
        self.measurements = []

        self.calibration_path = Path("~/.cache/eyeput", label).expanduser()
        self.calibration_path.parent.mkdir(exist_ok=True, parents=True)
        try:
            with self.calibration_path.open("rb") as file:
                self.calibration_data = pickle.load(file)
        except FileNotFoundError as e:
            self.calibration_data = None

    def transform(self, t, v0, v1):
        x = v1[-1][:2]
        # initial guess: project to zero plane
        if self.calibration_data is None:
            return x / screen_size_mm + vec(0.5, 1.0)
        # https://en.wikipedia.org/wiki/Barycentric_coordinate_system#Edge_approach
        else:
            T, r3, Ti, l = self.calibration_data
            l[:2] = Ti @ (x - r3)
            l[2] = 1 - l[0] - l[1]
            screen_position = np.dot(l, calibration_points)
            # ntimes(
            #     1000,
            #     lambda: self.calibration_data.__iter__(),
            #     lambda: np.zeros(3),
            #     lambda: Ti @ (x - r3),
            #     lambda: 1 - l[0] - l[1],
            #     lambda: l @ calibration_points,
            #     lambda: np.dot(l, calibration_points),
            # )
            return screen_position

    def start(self):
        self.measurements.clear()
        self.position_buffer.clear()

    def next(self):
        self.measurements.append(self.measurement)
        self.position_buffer.clear()

    def finalize(self):
        self.next()
        r = self.measurements
        self.calibration_data = CalibrationData(
            T=np.array([r[0] - r[2], r[1] - r[2]]),
            r3=r[2],
            Ti=np.linalg.inv(np.array([r[0] - r[2], r[1] - r[2]])),
            l=np.zeros(3),
        )
        with self.calibration_path.open("wb") as file:
            pickle.dump(self.calibration_data, file, pickle.HIGHEST_PROTOCOL)

    def on_gaze(self, reference, gaze_position, take, test, radius_mm):
        gaze_position_2d = gaze_position[:2]

        # calculate new mean
        self.position_buffer.append(gaze_position_2d)
        self.measurement = np.mean(slice(self.position_buffer, -take), axis=0)
        distance = np.linalg.norm(
            slice(self.position_buffer, -(take + test)) - self.measurement,
            axis=1,
        )

        # decide whether this reference point has completed
        self.is_ok = len(self.position_buffer) >= take + test and np.all(
            distance < radius_mm
        )

        # visualize current deviation
        deviation = (self.measurement - gaze_position_2d) / screen_size_mm
        self.marker.move(rel2abs(reference + deviation))


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
            self.left.on_gaze(reference, frame.l1, 15, 5, 12)
            self.right.on_gaze(reference, frame.r1, 15, 5, 12)
            # proceed with next point
            if self.left.is_ok and self.right.is_ok:
                self.finalize_point()
