import subprocess
import time

# alt https://stackoverflow.com/a/38171680/6040478
from PySide2.QtGui import QGuiApplication

# https://github.com/moses-palmer/pynput
from pynput.mouse import Button, Controller

# https://github.com/boppreh/keyboard
import keyboard

# see https://github.com/boppreh/keyboard/issues/588
keyboard._os_keyboard.register_key(
    (12, ()), keyboard._os_keyboard.normalize_name("ssharp")
)
keyboard._os_keyboard.register_key(
    (12, (keyboard._os_keyboard.normalize_name("shift"),)),
    keyboard._os_keyboard.normalize_name("question"),
)
keyboard._os_keyboard.register_key(
    (12, (keyboard._os_keyboard.normalize_name("altgr"),)),
    keyboard._os_keyboard.normalize_name("backslash"),
)

mouse = Controller()


def left_click(position=None):
    if position:
        previous_position = mouse.position
        mouse.position = (position.x(), position.y())
        mouse.click(Button.left, 1)
        mouse.position = previous_position
    else:
        mouse.click(Button.left, 1)


def right_click():
    mouse.click(Button.right, 1)


def mouse_move(x, y):
    mouse.position = (x, y)


def scroll(amount):
    mouse.scroll(0, amount)


def press_key(keycode):
    # activate keyboard
    keyboard.press_and_release("shift")
    time.sleep(0.02)
    keyboard.press_and_release(keycode)


def exec(command):
    subprocess.Popen(command, shell=True)


def get_clipboard():
    clipboard = QGuiApplication.clipboard()
    return clipboard.text()


def set_clipboard(text):
    clipboard = QGuiApplication.clipboard()
    clipboard.setText(text)
