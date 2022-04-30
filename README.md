- https://github.com/boppreh/keyboard


TODO
- eye tracker
    - tracker widget move for click
    - throttle

- KNOWN ISSUES:
    - eyeput window is not shown in task/Activities overview
    - firefox pop up menu disappers, when pressing hotkey

- scroll, mouse move
- unicode symbols
- special clicks: double, etc.
- eye blinking for clicking?

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