8player
=======
[![Build Status](https://travis-ci.org/etataurov/8player.png?branch=master)](https://travis-ci.org/etataurov/8player)
[![Coverage Status](https://coveralls.io/repos/etataurov/8player/badge.png?branch=master)](https://coveralls.io/r/etataurov/8player?branch=master)

Desktop app for 8tracks.com

written in Python using PyQt4


Installation
------------
On Ubuntu >= 12.04
```
sudo apt-get install python3-pyqt4 python3-pyqt4.phonon python3-pip
sudo pip-3.2 install requests
```
copy config and paste in your API key
```
cp config.json.template config.json
```
run
```
python3 eightplayer.py
```

TODO
----
 * deb package
 * better interface
 * like/favorite button
 * search
