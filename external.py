import subprocess
import time

from pynput.mouse import Button, Controller
import keyboard

from settings import *

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


def press_key(keycode):
    if not activate_keypress:
        print("WARN: keypresses are deactivated in settings!")
        return
    # activate keyboard
    keyboard.press_and_release("shift")
    time.sleep(0.02)
    keyboard.press_and_release(keycode)


def exec(command):
    subprocess.Popen(command, shell=True)
