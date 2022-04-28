from PyQt5.QtCore import (
    pyqtSignal,
    QThread,
)

from unix_socket import UnixSocket
from settings import *

sock_gaze = UnixSocket(Sockets.gaze, 100)


class GazeThread(QThread):
    gaze_signal = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()

    def run(self):
        sock_gaze.listen()
        while True:
            print("Wait for a connection")
            sock_gaze.accept()
            print("Connected. Listening for keys ...")
            try:
                # Receive the data in small chunks and retransmit it
                while True:
                    gaze_frame = sock_gaze.receive()
                    [t, x, y] = gaze_frame.split(" ")
                    self.gaze_signal.emit(float(x), float(y))

            except RuntimeError as err:
                print(err)

            finally:
                print("Clean up the connection")
                sock_gaze.close_connection()
