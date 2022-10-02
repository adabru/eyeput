from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QPoint, QPointF

import numpy as np


def vec(x, y=None):
    if y != None:
        return np.array((x, y))
    elif isinstance(x, QPoint):
        return np.array((x.x(), x.y()))
    elif isinstance(x, QWidget):
        return vec(x.pos())
    else:
        return np.array(x)


def qpoint(x):
    return QPoint(int(x[0]), int(x[1]))


def slice(buffer, u, v=None):
    assert v == None
    assert u < 0
    return np.fromiter(
        reversed(buffer),
        dtype=np.dtype((float, len(buffer[0]))),
        count=min(-u, len(buffer)),
    )


# is set in QApplication`s constructor
screen_geometry = None


def rel2abs(v):
    return QPoint(
        int(v[0] * screen_geometry.width()),
        int(v[1] * screen_geometry.height()),
    )


def get_screen_geometry():
    return screen_geometry


def set_screen_geometry(geometry):
    global screen_geometry
    screen_geometry = geometry
