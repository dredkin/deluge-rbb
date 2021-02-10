# Remote "browse" button for Deluge
This is a plugin for [Deluge](http://deluge-torrent.org) torrent client.
By default, when started in **client-server mode**, Deluge has no option to choose destination folder for download, you have to enter it by hand.
The **Remote "browse" button** plugin eliminates this drawback by adding `Browse..` button to *"Add torrent"* dialog. You can also set a *top level* directory which will be the default starting location for browse dialog, there is also the option to stop the user traversing above this directory (useful for restricting moves to a specific drive/folder).

![Image showing browse buttons](https://raw.githubusercontent.com/dredkin/deluge-rbb/master/Images/BrowseButtons.png)
![Image showing preferences pane](https://raw.githubusercontent.com/dredkin/deluge-rbb/master/Images/Preferences.png)

## Download
[Download](https://github.com/dredkin/deluge-rbb/releases) .egg files for python 2.7, 3.6 & 3.7.
If you have another version of python, you can make an .egg file by yourself (see **Build** section below).

You must use the egg for the correct version of python of both your server & client.
To check which version of Python you are using:
* Unix: open terminal and type `python --version`.
* Windows: Go to your deluge installation directory (e.g. D:\Program Files (x86)\Deluge) and look at the version of the deluge folder. This will be in the format `deluge-someDelugeVersionNumber-pyX.Y.egg` 'X.Y' is the version of Python deluge is running.

## Installation
When running the Deluge daemon, deluged and Deluge client on a separate computers, the plugin must be installed on both computers. When installing the egg through the GTK client it will be placed in the plugins directory of your computer, as well as copied over to the computer running the daemon.

For example if you have this setup:

* Windows desktop with Python 2.6 running GTK client.
* Linux server with Python 2.7 running deluged

you will have to install both py2.6 and py2.7 eggs.

Note: Remember, that after **every** upgrade of a plugin you have to restart both server and client..

## Features
Browse buttons added to:
* Add torrents dialog (for Download location & move completed location)
* Move completed in the options tab of the bottom menu bar.
* Right click menu "Move" dialog.
* Set a default folder for the browse dialog
** Also limit directory traversal to this folder & subfolders.

## Building
If you havn't found an .egg file for your version of python in Releases, you can build it:
````
git clone  https://github.com/dredkin/deluge-rbb.git 
cd deluge-rbb
python ./setup.py bdist_egg
````
The resulting .egg file will be in `dist` subfolder.
 - If you haven't `git` installed, you can download the sources from `<>Code` page, click `⬇Code`button and then "Download Zip" ;
 - If you have several versions of python on your machine, you can specify the exact version you need: 
 ````
 python3.8 ./setup.py bdist_egg
 ````

### Unix
The included `build.sh` file will build the egg file and copy it to the local plugins folder for testing.

### Windows
The included `build.bat` file will try to disable the plugin on the server before copying the egg to the remote server and re-enabling the plugin. The remote functions use programs associated with putty (plink & pscp) to run remote commands and FTP files. You will need to have putty installed & your host configured for [automatic connections](http://the.earth.li/~sgtatham/putty/0.52/htmldoc/Chapter7.html#7.2.2) for this to work (note putty dir needs to also be on your environment PATH). Once this is done change the value of `serverAddr` at the top of the batch file to the name you saved the configuration in putty.

When using this script for the first time you should build the plugin python egg and manually upload it to the server via the *Preferences -> Plugins -> Install Plugin*. Then enable the plugin through the *Preferences -> Plugins* tab. This should stop some low frequency issues with deluge becomming confused with the plugin version when using this `build.bat` script.

When calling the batch script you can pass in any number of Python versions to build the eggs for.
e.g. `build.bat "C:\Python26\python.exe" "C:\Python27\python.exe" "C:\Python34\python.exe"`

## Known Issues

Because of python's `setuptools` package "zip caching" technique sometimes deluge cannot update the plugins content right after upgrade. This can cause the following errors in LOG file:

 - `KeyError: CorePlugin.browsebutton`
 - `ZipImportError: bad local file header`
 
The workaround is:

 1. Disable (uncheck) plugin in settings dialog
 2. Exit _client_ 
 3. **Restart** _server_.
 4. Start client and enable plugin in settings again

After this procedure the plugins cache is cleared and deluge correctly loads new plugin package. So it is always advised to restart deluge after installing a new version of the plugin.
