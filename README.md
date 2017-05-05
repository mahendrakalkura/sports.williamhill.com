How to install?
===============

```
$ git clone --recursive git@github.com:mahendrakalkura/sports.williamhill.com.git
$ cd sports.williamhill.com
$ mkvirtualenv --python=python3 sports.williamhill.com
$ pip install --requirement requirements.txt
```

How to run?
===========

```
$ cd sports.williamhill.com
$ workon sports.williamhill.com
$ python manage.py --matches
$ python manage.py --web-sockets $ID
```
