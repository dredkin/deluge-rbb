#
# gtkui.py
#
# Copyright (C) 2009 dredkin <dmitry.redkin@gmail.com>
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

import gtk

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

importError = None
try:
    import pkg_resources
    import common
except:
    importError = "package setuptools is required!"


def findwidget(container, name):
    if hasattr(container, 'get_children'):
        ch = container.get_children()
        for widget in ch:
            if widget.get_name() == name:
              return widget
            ret = findwidget(widget, name)
            if ret is not None:
              return ret
    return None

def showMessage(parent, message):
    if parent is None:
        parent = component.get("MainWindow").window
    md = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, 'Error starting plugin: '+ message)
    md.format_secondary_text('Remote browse button plugin');
    md.run()
    md.destroy()
    
class BrowseDialog:
    def __init__(self, path, parent):
        self.selectedfolder = path
        self.builder = gtk.Builder()
        self.builder.add_from_file(common.get_resource('folder_browse_dialog.glade'))
        self.dialog = self.builder.get_object("browse_folders_dialog")
        self.dialog.set_transient_for(parent)
        self.label = self.builder.get_object("current_folder_label")
        self.liststore = gtk.ListStore(gtk.gdk.Pixbuf, str)
        iconview = self.builder.get_object("iconview1")
        iconview.set_model(self.liststore)
        iconview.set_pixbuf_column(0)
        iconview.set_text_column(1)
        iconview.connect("item-activated", self.subfolder_activated)
        self.refillList("")
        #        self.dialog.connect("delete-event", self._on_delete_event)
        
    def on_folder_double_click(self, widget):
        """"""

    def refillList(self, subfolder):
        self.liststore.clear()
#        try:
        client.browsebutton.get_folder_list(self.selectedfolder, subfolder).addCallback(self.get_folder_list_callback)

    def get_folder_list_callback(self, results):
        self.selectedfolder = results[0]
        self.label.set_label(self.selectedfolder)
        if results[1]:
            pixbuf = gtk.icon_theme_get_default().load_icon("go-up", 24, 0)
            self.liststore.append([pixbuf, ".."])    
            
        for folder in results[2]:
            pixbuf = gtk.icon_theme_get_default().load_icon("folder", 24, 0)
            self.liststore.append([pixbuf, folder])    

    def subfolder_activated(self, widget, path):
        subfolder = self.liststore.get_value(self.liststore.get_iter(path),1)
        self.refillList(subfolder)
    
class GtkUI(GtkPluginBase):
    error = None
    button = None
    editbox = None
    addDialog = None
    def enable(self):
        self.error = importError
        if self.error is None:
            self.initializeGUI()
        if self.error is not None:
            showMessage(None, self.error)

    def disable(self):
        self.error = None
        component.get("Preferences").remove_page("remotebrowsebutton")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)
        self.deleteButton()
        if self.error is not None:
            showMessage(None, self.error)

    def on_apply_prefs(self):
        log.debug("applying prefs for remotebrowsebutton")
        config = {
            "test":self.glade.get_widget("txt_test").get_text()
        }
        client.remotebrowsebutton.set_config(config)

    def on_show_prefs(self):
        client.remotebrowsebutton.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.glade.get_widget("txt_test").set_text(config["test"])

    def initializeGUI(self):
        self.glade = gtk.glade.XML(common.get_resource("config.glade"))
        component.get("Preferences").add_page("remotebrowsebutton", self.glade.get_widget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
        self.addButton()

    def addButton(self):
        """Adds a Button to remote Add torrent dialog."""
        if self.button is None:
            hbox = self.findHbox14()
            if hbox is None:
                return None
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_DIRECTORY,  gtk.ICON_SIZE_BUTTON)
            self.button = gtk.Button()
            self.button.set_image(image)
            self.button.set_label("Browse..")
            self.button.set_size_request(50,-1)
            hbox.pack_end(self.button)
            self.button.show()
            self.button.connect("clicked", self.on_browse_button_clicked)
        return True

    def deleteButton(self):
        if self.button is not None:
            hbox = self.findHbox14()
            if hbox is None:
                return None
            hbox.remove(self.button)
            self.button = None
        return True

    def findHbox14(self):
        dialog = component.get("AddTorrentDialog")
        if dialog is None:
            self.error = "AddTorrentDialog not found!"
            return None
        self.addDialog = dialog.dialog
        if self.editbox is None:
            self.editbox = findwidget(self.addDialog,'entry_download_path')
        if self.editbox is None:
            self.error = "entry_download_path not found!"
            return None
        hbox = self.editbox.get_parent()
        if hbox is None:
            self.error = "hbox14 not found!"
            return None
        return hbox

    def on_browse_button_clicked(self, widget):
        dialog = BrowseDialog(self.editbox.get_text(), self.addDialog)
        id = dialog.dialog.run()
        if id > 0:
            self.editbox.set_text(dialog.selectedfolder)
        dialog.dialog.destroy()