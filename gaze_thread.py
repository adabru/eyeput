from PyQt5.QtCore import (
    pyqtSignal,
    QThread,
)

from unix_socket import UnixSocket
from settings import *

sock_gaze = UnixSocket(Sockets.gaze, 100)

# for debugging
# from graph import *

# graph = Graph()


class GazeThread(QThread):
    gaze_signal = pyqtSignal(float, float, float, float, float)

    def __init__(self):
        super().__init__()
        # for debugging
        # graph.setup()

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
                    [t, l0, l1, r0, r1] = [float(x) for x in gaze_frame.split(" ")]
                    self.gaze_signal.emit(t, l0, l1, r0, r1)
                    # graph.gaze_signal.emit(t, l0, l1, r0, r1, x, y)

            except ValueError as err:
                print(err)

            except RuntimeError as err:
                print(err)

            finally:
                print("Clean up the connection")
                sock_gaze.close_connection()
