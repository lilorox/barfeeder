# barfeeder

## What is it?

This piece of python script is used to feed information to lemonbar (https://github.com/LemonBoy/bar).
It relies on several threads to get the information from the following sources:
- builtin python modules for date and time,
- the /proc filesystem for the battery status
- the i3ipc python module (https://pypi.python.org/pypi/i3ipc) for workspace information from i3
- conky for the cpu, memory, interface status and speed and partitions usage


This work was inspired by [electro7](https://github.com/electro7/dotfiles/tree/master/.i3/lemonbar)'s dotfiles and lemonbar scripts.

## Installation

First, you need to fulfill the following dependencies:
- python (preferably v3.5, haven't tested any other)
- python-virtualenv
- python-virtualenvwrapper
- conky
- Noto Sans & Font Awesome fonts in your font path
- lemonbar

Then, after having cloned this repo:
```
virtualenv ~/.virtualenvs/barfeeder
cd barfeeder
workon barfeeder
pip install -r requirements.txt
```

## Usage

If your virtualenv is set up as above, just run:
```
./run.sh
```

Otherwise, you might need to take a look at `run.sh` or perhaps set the `WORKON_HOME` variable in your environment.

### Run at i3 startup

Just add this line in i3's config file (obviously set your path in here):
```
exec --no-startup-id path_to_barfeeder/run.sh
```

## Debugging

You can pass the `-d` and `-F` flags to `barfeeder.py` to, respectively, add debug information and prevent barfeeder from forking to the background.

## Upcoming features

See [TODO.md](TODO.md).

## Customization

OK sorry, too much doc at once, I'll fill this up later :)
