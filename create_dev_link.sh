#!/bin/bash
cd `dirname "$0"`
mkdir temp
export PYTHONPATH=./temp
/usr/bin/python setup.py build develop --install-dir ./temp
sudo cp ./temp/browse_button.egg-link /var/lib/deluged/config/plugins
rm -fr ./temp
