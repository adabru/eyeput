import os
from PyQt5.QtCore import (
    pyqtSignal,
    QThread,
)

from unix_socket import UnixSocket
from settings import *


class HotḱeyThread(QThread):
    hotkey_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        FIFO = Sockets.eyeput

        try:
            os.unlink(FIFO)
        except OSError:
            if os.path.exists(FIFO):
                raise

        os.mkfifo(FIFO)

        while True:
            with open(FIFO) as fifo:
                data = fifo.read()
                if len(data) > 0:
                    self.hotkey_signal.emit()
