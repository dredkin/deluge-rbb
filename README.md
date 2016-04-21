# Remote "browse" button for Deluge
This is a plugin for [Deluge](http://deluge-torrent.org) torrent client.
By default, when started in **client-server mode**, Deluge has no option to choose destination folder for download, you have to enter it by hand.
The **Remote "browse" button** plugin eliminates this drawback by adding `Browse..` button to *"Add torrent"* dialog. You can also set a *top level* directory which will be the default starting location for browse dialog, there is also the option to stop the user traversing above this directory (useful for restricting moves to a specific drive/folder).

![Image showing browse buttons](https://raw.githubusercontent.com/dredkin/deluge-rbb/master/Images/BrowseButtons.png)
![Image showing preferences pane](https://raw.githubusercontent.com/dredkin/deluge-rbb/master/Images/Preferences.png)

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
* Set a default folder for the browse dialog
** Also limit directory traversal to this folder & subfolders.

## Building
To build yourself you will need to run `python setup.py bdist_egg` to build the egg file.

### Unix
The included `build.sh` file will build the egg file and copy it to the local plugins folder for testing.

### Windows
The included `build.bat` file will try to do some fancy stuff with disabling the plugin on the server before copying the egg to the remote server and re-enabling the plugin. The remote functions use programs associated with putty (plink & pscp) to run remote commands and FTP files. You will need to have putty installed & your host configured for [automatic connections](http://the.earth.li/~sgtatham/putty/0.52/htmldoc/Chapter7.html#7.2.2) for this to work (note putty dir needs to also be on your environment PATH). Once this is done change the value of `serverAddr` at the top of the batch file to the name you saved the configuration in putty.

When using this script for the first time you should build the plugin python egg and **manually** upload it to the server via the *Preferences -> Plugins -> Install Plugin*. Then enable the plugin through the *Preferences -> Plugins* tab. This should stop some low frequency issues with deluge becomming confused with the plugin version when using this `build.bat` script.

These issues look like this:
```
Traceback (most recent call last):
  File "/usr/local/lib/python2.7/dist-packages/deluge-1.3.11-py2.7.egg/deluge/core/rpcserver.py", line 299, in dispatch
    ret = self.factory.methods[method](*args, **kwargs)
  File "/usr/local/lib/python2.7/dist-packages/deluge-1.3.11-py2.7.egg/deluge/core/core.py", line 527, in enable_plugin
    self.pluginmanager.enable_plugin(plugin)
  File "/usr/local/lib/python2.7/dist-packages/deluge-1.3.11-py2.7.egg/deluge/core/pluginmanager.py", line 82, in enable_plugin
    super(PluginManager, self).enable_plugin(name)
  File "/usr/local/lib/python2.7/dist-packages/deluge-1.3.11-py2.7.egg/deluge/pluginmanagerbase.py", line 151, in enable_plugin
    component.start([instance.plugin._component_name])
  File "/usr/local/lib/python2.7/dist-packages/deluge-1.3.11-py2.7.egg/deluge/component.py", line 290, in start
    if self.components[name]._component_depend:
KeyError: 'CorePlugin.browsebutton'
```

When calling the batch script you can pass in any number of Python versions to build the eggs for.
e.g. `build.bat "C:\Python26\python.exe" "C:\Python27\python.exe" "C:\Python34\python.exe"`
