# <img src="./eyeput.png" alt="drawing" width="50"/> Eyeput

This python application offers complete desktop control via eye tracking.

```sh
# application dependencies
pip install PySide2 pynput keyboard numpy psutil
# optional development dependencies
pip install pyqtgraph pyopengl

# add to global path for hotkey configuration
sudo ln -s $PWD/eyeput.sh /usr/local/bin/eyeput

# use your xkb layout as default console keymap
sudo sh -c "echo KEYMAP=de-latin1 > /etc/vconsole.conf"

# allow access to virtual keyboard
sudo usermod -a -G tty,input $USER
```

Add a hotkey in your window manager with the command: `eyeput toggle`.

TODO

- scroll, mouse move
- unicode symbols
- special clicks: double, etc.

KNOWN ISSUES:

- eyeput window is not shown in task/Activities overview
- firefox pop up menu disappers when pressing hotkey
