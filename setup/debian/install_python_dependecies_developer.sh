#!/bin/sh
# Run this script from terminal within atom to get it running with platformio virtual environment
sudo apt-get install python-dev
sudo apt-get install libmysqlclient-dev
sudo apt-get install python-pip
sudo pip install --upgrade pip

# install nabton SDK pynab library
pip install ioant
pip install ioant_mysqlhelper
