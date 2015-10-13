# Remote "browse" button for Deluge
This is a plugin for [Deluge](http://deluge-torrent.org) torrent client.
By default, when started in **client-server mode**, Deluge has no option to choose destination folder for download, you have to enter it by hand.
The **Remote "browse" button** plugin eliminates this drawback by adding `Browse..` button to *"Add torrent"* dialog.

## Download
[Download](https://github.com/dredkin/deluge-rbb/releases) .egg files for python 2.6, 2.7 & 3.4.
If you have another version of python, make an .egg file by running build.sh or build.bat depending on platform.

You must use the egg for the correct version of python of both your server & client.
To check which version of Python you are using:
* Unix: open terminal and type `python --version`.
* Windows: Go to your deluge installation directory (e.g. D:\Program Files (x86)\Deluge) and look at the version of the deluge folder. This will be in the format `deluge-someDelugeVersionNumber-pyX.Y.egg` 'X.Y' is the version of Python deluge is running.

## Installation
When running the Deluge daemon, deluged and Deluge client on a separate computers, the plugin must be installed on both computers. When installing the egg through the GTK client it will be placed in the plugins directory of your computer, as well as copied over to the computer running the daemon.

Note: If the Python versions on the server and desktop computer do not match, you will have to copy the egg to the server manually.

For example in the setup below you will have to install the py2.6 egg on the desktop as normal but then manually install the py2.7 egg onto the server.

Windows desktop with Python 2.6 running GTK client.
Linux server with Python 2.7 running deluged

## Features
Browse buttons added to:
* Add torrents dialog (for Download location & move completed location)
* Move completed in the options tab of the bottom menu bar.
* Right click menu "Move" dialog.

## Building
To build yourself you will need to run `python setup.py bdist_egg` to build the egg file.

### Unix
The included `build.sh` file will build the egg file and copy it to the local plugins folder for testing.

### Windows
The included `build.bat` file will try to do some fancy stuff with disabling the plugin on the server before copying the egg to the remote server and re-enabling the plugin. The remote functions use programs associated with putty (plink & pscp) to run remote commands and FTP files. You will need to have putty installed & your host configured for [automatic connections](http://the.earth.li/~sgtatham/putty/0.52/htmldoc/Chapter7.html#7.2.2) for this to work. Once this is done change the value of `serverAddr` at the top of the batch file to the name you saved the configuration in putty.

When calling the batch script you can pass in any number of Python versions to build the eggs for.
e.g. `build.bat "C:\Python26\python.exe" "C:\Python27\python.exe" "C:\Python34\python.exe"`
