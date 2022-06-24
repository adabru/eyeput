# <img src="./eyeput.png" alt="drawing" width="50"/> Eyeput

This python application offers complete desktop control via eye tracking.

```sh
# application dependencies
pip install PyQt5 pynput
# optional development dependencies
pip install pyqtgraph pyopengl numpy

# https://github.com/boppreh/keyboard
sudo pip install git+https://github.com/boppreh/keyboard.git
# sudo pip uninstall keyboard

# add to global path for hotkey configuration
sudo ln -s $PWD/eyeput.sh /usr/local/bin/eyeput

# use your xkb layout as default console keymap
sudo sh -c "echo KEYMAP=de-latin1 > /etc/vconsole.conf"

# enable start on system start
sudo sed "s|__PWD__|$PWD|" ./eyeput.keys.service | sudo tee /etc/systemd/system/eyeput.keys.service
sudo systemctl enable --now eyeput.keys
journalctl -eu eyeput.keys
```

Add a hotkey in your window manager with the command: `eyeput toggle`.

TODO

- scroll, mouse move
- unicode symbols
- special clicks: double, etc.
- eye blinking for clicking?

KNOWN ISSUES:

- eyeput window is not shown in task/Activities overview
- firefox pop up menu disappers when pressing hotkey
