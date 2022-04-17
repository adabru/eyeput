- https://github.com/boppreh/keyboard


TODO
- eye tracker
    - introduce IPC in main.py to communicate with mouse.py (reads mouse position and converts into exetracker replacement)
    - start main.py as subprocess from mouse_simulation.py
- start hidden
- KNOWN ISSUES:
    - eyeput window appears in desktops window overview when overview open and pressing tilde 
    - firefox pop up menu disappers, when pressing tilde
    - hotkey does sometimes not work at the first call, press shift before

- scroll
- unicode symbols
- images
- special clicks: double, etc.
- commandos

setup
```sh
pip install PyQt5 pynput 
sudo pip install keyboard
sudo ln -s $PWD/eyeput.sh /usr/local/bin/eyeput
sudo sed "s|__PWD__|$PWD|" ./eyeput.keys.service | sudo tee /etc/systemd/system/eyeput.keys.service
sudo systemctl enable --now eyeput.keys
journalctl -eu eyeput.keys
```
- window manager hotkey command: eyeput toggle