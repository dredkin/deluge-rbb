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
    "test":"NiNiNi"
}

CURRENT_LOCALE = locale.getdefaultlocale()[1]
if CURRENT_LOCALE is None:
    CURRENT_LOCALE = 'utf8'

class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("browsebutton.conf", DEFAULT_PREFS)

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
        log.debug("RBB:iterating "+absolutepath)
        for f in list:
            if os.path.isdir(os.path.join(absolutepath,f)):
                f2 = f.decode(CURRENT_LOCALE).encode('utf8')
                subfolders.append(f2)
        return subfolders
            
    def is_root_folder(self, folder):
        return os.path.dirname(folder) == folder
    
    @export
    def set_config(self, config):
        """Sets the config dictionary"""
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        """Returns the config dictionary"""
        return self.config.config

    @export
    def serverlog(self, line):
        log.debug(line)

    @export
    def get_folder_list(self, folder, subfolder):
        """Returns the list of subfolders for specified folder on server"""
        error = ""
        if folder == "":
            folder = os.path.expanduser("~")
        else:
            folder = folder.encode(CURRENT_LOCALE)
        log.debug("RBB:native folder"+folder)
        log.debug("RBB:orig subfolder"+subfolder)
        subfolder = subfolder.encode(CURRENT_LOCALE)
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
        return [absolutepath.decode(CURRENT_LOCALE).encode('utf8'), isroot, subfolders, error]
