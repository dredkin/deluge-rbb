#
# core.py
#
# Copyright (C) 2014 dredkin <dmitry.redkin@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import sys
PY3 =  sys.version_info[0] >= 3

if PY3:
    import logging
    log = logging.getLogger(__name__)
else:
    from deluge.log import LOG as log


from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
import os
import locale
import pkg_resources
import gettext

def windows():
    return os.name == "nt"

if windows():
  import win32api

DEFAULT_PREFS = {
    #Default to empty to have no specified root dir.
    "RootDirPath":"",
    "DisableTraversal":"false"
}

UTF8 = 'UTF-8'
CURRENT_LOCALE = locale.getdefaultlocale()[1]
if CURRENT_LOCALE is None:
    CURRENT_LOCALE = UTF8

class Core(CorePluginBase):
    def enable(self):
        log.info("RBB: enabling plugin")
        self.config = deluge.configmanager.ConfigManager("browsebutton.conf", DEFAULT_PREFS)
        if self.config is not None:
            log.info("RBB: config read")
        log.info("RBB: plugin enabled")

    def disable(self):
        #self.config.save()
        pass

    def update(self):
        pass

    def drives_list(self):
        if windows():
            drives = win32api.GetLogicalDriveStrings()
            return drives.split('\000')[:-1]
        else:
            return "/"
            
    def subfolders_list(self, absolutepath):
        subfolders = []
        try:
            list = os.listdir(absolutepath)
        except:
            list = []
        for f in list:
            if os.path.isdir(os.path.join(absolutepath,f)):
                if PY3:
                    f2 = f
                else:
                    f2 = f.decode(CURRENT_LOCALE).encode(UTF8)
                subfolders.append(f2)
        return subfolders
            
    def is_root_folder(self, folder):
        return os.path.dirname(folder) == folder
    
    @export
    def save_config(self):
        """Saves the config"""
        self.config.save()
        log.debug("RBB: config saved")

    @export
    def set_config(self, config):
        """Sets the config dictionary"""
        log.debug("RBB: set_config")
        for key in config.keys():
            self.config[key] = config[key]
            log.debug("RBB: added history "+str(key)+"->"+str(config[key]))
        self.save_config()

    @export
    def get_config(self):
        """Returns the config dictionary"""
        log.debug("RBB: config assigned")
        return self.config.config

    @export
    def serverlog(self, line):
        log.debug(line)

    def make_current_locale(self, string, name):
        if PY3:
            return string
        if isinstance(string, str):
            log.debug("RBB:" + name + " is str = " + string)
            try:
                uni = string.decode(UTF8)
                log.debug("RBB:" + name + " decoded from utf8 = "+ string)
            except:
                log.debug("RBB:" + name + " IS NOT UTF8!!!")
                try:
                    uni = string.decode(CURRENT_LOCALE)
                    log.debug("RBB:" + name + " decoded from CURRENT_LOCALE = "+ string)
                except:
                    log.info("RBB:" + name + " IS UNDECODABLE!!! dont know what to do...")
                    return string
        elif isinstance(string, unicode):
            log.debug("RBB:" + name + " is Unicode")
            uni = string
        string = uni.encode(CURRENT_LOCALE)
        log.debug("RBB:" + name + " encoded to CURRENT_LOCALE = "+ string)
        return string

    @export
    def get_folder_list(self, folder, subfolder):
        """Returns the list of subfolders for specified folder on server"""
        log.debug("RBB:CURRENT_LOCALE is "+CURRENT_LOCALE)
        error = ""
        log.debug("RBB:original folder="+folder)
        log.debug("RBB:original subfolder="+subfolder)
        folder = self.make_current_locale(folder, "folder")
        if folder == "":
            folder = os.path.expanduser("~")

        subfolder = self.make_current_locale(subfolder, "subfolder")

        newfolder = os.path.join(folder,subfolder)
        absolutepath = os.path.normpath(newfolder)
        
        if not os.path.isdir(absolutepath):
            log.info("RBB:NOT A FOLDER!:"+absolutepath+" (normalized from "+newfolder+")")
            error = "Cannot List Contents of "+absolutepath
            absolutepath = os.path.expanduser("~")

        if windows():
            isroot = self.is_root_folder(folder) and (subfolder == "..")
        else:
            isroot = self.is_root_folder(absolutepath)
        if windows() and isroot:
            subfolders = self.drives_list()
            absolutepath = ""
        else:
            subfolders = self.subfolders_list(absolutepath)
        if PY3:
            return [absolutepath, isroot, subfolders, error]
        else:
            return [absolutepath.decode(CURRENT_LOCALE).encode(UTF8), isroot, subfolders, error]
