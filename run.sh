#!/bin/bash

WORKON_HOME=${WORKON_HOME:-~/.virtualenvs}
VIRTUALENV_DIR=$WORKON_HOME/barfeeder

$VIRTUALENV_DIR/bin/python $(dirname $0)/barfeeder.py
