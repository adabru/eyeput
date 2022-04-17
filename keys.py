#!/usr/bin/python

import os
import time
import keyboard

# local
from unix_socket import UnixSocket

sock_keyboard = UnixSocket("/tmp/evdev_keypress.sock", 100)
sock_keyboard.listen()

while True:
    print("Wait for a connection")
    sock_keyboard.accept()
    print("Connected. Listening for keys ...")
    try:
        # Receive the data in small chunks and retransmit it
        while True:
            keyboardCode = sock_keyboard.receive()

            # activate keyboard
            keyboard.press_and_release("shift")
            time.sleep(0.02)
            keyboard.press_and_release(keyboardCode)

    except RuntimeError as err:
        print(err)

    finally:
        print("Clean up the connection")
        sock_keyboard.close_connection()

exit()
