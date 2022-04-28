- https://github.com/boppreh/keyboard


TODO
- line 251:
    File "/home/slava/repos/eyeput/./main.py", line 183, in selectItem
    self.pressKey(self.hoverItem.item.pressKey)
  File "/home/slava/repos/eyeput/./main.py", line 251, in pressKey
    sock_keypress.try_send("+".join(list(self.gridState.modifiers) + [keyCode]))
    TypeError: sequence item 0: expected str instance, NoneType found
- missing images in corner have to be removed
- eye tracker
    - BUG: does not draw correctly on start up
    - mouse move for click

- KNOWN ISSUES:
    - eyeput window appears in desktops window overview when overview open and pressing tilde 
    - firefox pop up menu disappers, when pressing tilde
    - hotkey does sometimes not work at the first call, press shift before
    - https://doc.qt.io/qt-5/qwidget.html#showFullScreen

- scroll
- unicode symbols
- special clicks: double, etc.

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