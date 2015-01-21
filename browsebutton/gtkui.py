#
# gtkui.py
#
# Copyright (C) 2014 dredkin <dmitry.redkin@gmail.com>

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
import deluge.ui.gtkui.menubar

importError = None
try:
    import pkg_resources
    import common
except:
    importError = "Install package setuptools to run this plugin!"


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

def caseInsensitive(key):
    return key.lower()

class BrowseDialog:
    def __init__(self, path, recent, parent):
        self.selectedfolder = path
        self.builder = gtk.Builder()
        self.builder.add_from_file(common.get_resource('folder_browse_dialog.glade'))
        self.dialog = self.builder.get_object("browse_folders_dialog")
        self.dialog.set_transient_for(parent)

        self.recentliststore = gtk.ListStore(str)
        self.label = self.builder.get_object("selected_folder")
        self.label.set_model(self.recentliststore)
        cell = gtk.CellRendererText()
        self.label.pack_start(cell, True)
        self.label.add_attribute(cell, "text", 0)
        self.handler_id = self.label.connect("changed", self.recent_chosed)

        self.liststore = gtk.ListStore(gtk.gdk.Pixbuf, str)
        self.iconview = self.builder.get_object("iconview1")
        self.iconview.set_model(self.liststore)
        self.iconview.set_pixbuf_column(0)
        self.iconview.set_text_column(1)
        self.iconview.set_item_width(300)
        self.iconview.connect("item-activated", self.subfolder_activated)
        self.refillList("")
        self.recent = recent

    def refillList(self, subfolder):
        log.debug("RBB:refillList selectedfolder="+self.selectedfolder+";subfolder="+ subfolder)
        client.browsebutton.get_folder_list(self.selectedfolder, subfolder).addCallback(self.get_folder_list_callback)

    def get_folder_list_callback(self, results):
        if results[3]:
            showMessage(None, results[3])
            return
        self.liststore.clear()
        self.selectedfolder = results[0]
        log.debug("RBB:callback selectedfolder="+self.selectedfolder)
        self.label.handler_block(self.handler_id)
        self.recentliststore.clear()
        for folder in self.recent:
            self.recentliststore.append([folder])
        self.recentliststore.prepend([self.selectedfolder])
        self.label.set_active(0)
        self.label.handler_unblock(self.handler_id)

        if not results[1]:
            pixbuf = gtk.icon_theme_get_default().load_icon("go-up", 24, 0)
            self.liststore.append([pixbuf, ".."])
        subfolders = []
        for folder in results[2]:
            subfolders.append(folder)
        subfolders.sort(key=caseInsensitive)
        for folder in subfolders:
            pixbuf = gtk.icon_theme_get_default().load_icon("folder", 24, 0)
            self.liststore.append([pixbuf, folder])
        #self.iconview.set_item_width(-1)

    def subfolder_activated(self, widget, path):
        subfolder = self.liststore.get_value(self.liststore.get_iter(path),1)
        self.refillList(subfolder)

    def recent_chosed(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()
        if index != None:
            self.selectedfolder = str(model[index][0])
            self.refillList("")

class GtkUI(GtkPluginBase):
    error = None
    buttons = None
    addDialog = None
    mainWindow = None
    moveWindow = None
    recent = []
    def enable(self):
        self.error = importError
        if self.error is None:
            self.initializeGUI()
        self.handleError()

    def disable(self):
        self.error = None
        component.get("Preferences").remove_page("Browse Button")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)
        for name in self.buttons.keys() :
          self.deleteButton(self.buttons[name]['widget'])
          self.buttons[name]['widget'] = None
          self.handleError()

    def handleError(self):
        if self.error is not None:
            showMessage(None, self.error)
        self.error = None



    def on_apply_prefs(self):
        log.debug("RBB:applying prefs for browsebutton")
        config = {
            "test":self.glade.get_widget("txt_test").get_text()
        }
        client.browsebutton.set_config(config)

    def on_show_prefs(self):
        client.browsebutton.get_config().addCallback(self.cb_get_config)
        log.debug("Im here, showing prefs")

    def cb_get_config(self, config):
        """callback for on show_prefs"""
        self.glade.get_widget("txt_test").set_text(config["test"])

    def save_recent(self):
        log.debug("RBB:saving recent ")
        config = {
            "recent": tuple(self.recent)
        }
        client.browsebutton.set_config(config)

    def load_recent(self):
        log.debug("RBB:loading recent ")
        client.browsebutton.get_config().addCallback(self.initialize_recent)

    def initialize_recent(self, config):
        """callback for load_recent"""
        self.recent = []
        if "recent" in config:
            self.recent = list(config["recent"])

    def on_menuitem_move_activate():
        log.debug("asdasdsadsasds")

    def initializeGUI(self):
        self.glade = gtk.glade.XML(common.get_resource("config.glade"))
        self.load_recent()
        component.get("Preferences").add_page("Browse Button", self.glade.get_widget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)

        self.buttons = { 'store' : { 'id': 'entry_download_path' , 'editbox': None, 'widget': None , 'window': None}, \
                     'completed' : { 'id' : 'entry_move_completed_path' , 'editbox': None, 'widget': None , 'window': None}, \
                 'completed_tab' : { 'id' : 'entry_move_completed' , 'editbox': None, 'widget': None , 'window': None} }
        self.makeButtons()
        self.addMoveMenu()
        self.handleError

    def addMoveMenu(self):
        torrentmenu = component.get("MenuBar").torrentmenu
        self.menu = gtk.CheckMenuItem(_("test"))
        self.menu.show()
        log.debug("------------------------------------------------------------------------------------------------")
        self.menu.connect("activate", self.on_menu_activated, None)

        torrentmenu.append(self.menu)

    def on_menu_activated(self, widget=None, data=None):
        log.debug("Item clicked")

        #self.show_move_storage_dialog(component.get("TorrentView").get_torrent_state(component.get("TorrentView").get_selected_torrent()))
        client.core.get_torrent_status(component.get("TorrentView").get_selected_torrent(), ["save_path"]).addCallback(self.show_move_storage_dialog)

    def show_move_storage_dialog(self, status):
        log.debug("show_move_storage_dialog")
        glade = gtk.glade.XML(pkg_resources.resource_filename(
            "deluge.ui.gtkui", "glade/move_storage_dialog.glade"
        ))

        glade = gtk.glade.XML(common.get_resource("myMove_storage_dialog.glade"))


        # Keep it referenced:
        #  https://bugzilla.gnome.org/show_bug.cgi?id=546802
        self.move_storage_dialog = glade.get_widget("move_storage_dialog")
        self.move_storage_dialog.set_transient_for(component.get("MainWindow").window)
        self.move_storage_dialog_entry = glade.get_widget("entry_destination")
        self.move_storage_browse_button = glade.get_widget("browse")
        log.debug("------------------------------------------------------------------------------------------------")
        log.debug(status)

        self.move_storage_dialog_entry.set_text(status["save_path"])
        def on_dialog_response_event(widget, response_id):

            def on_core_result(result):
                # Delete references
                del self.move_storage_dialog
                del self.move_storage_dialog_entry

            if response_id == gtk.RESPONSE_OK:
                log.debug("Moving torrents to %s",
                          self.move_storage_dialog_entry.get_text())
                path = self.move_storage_dialog_entry.get_text()
                client.core.move_storage(
                    component.get("TorrentView").get_selected_torrents(), path
                ).addCallback(on_core_result)
            self.move_storage_dialog.hide()

        self.move_storage_dialog.connect("response", on_dialog_response_event)
        self.move_storage_browse_button.connect("clicked", self.on_browse_button_clicked)

        self.move_storage_dialog.show()












    def addButton(self, editbox, onClickEvent):
        """Adds a Button to the editbox inside hbox container."""
        if editbox is None:
            return None
        hbox = editbox.get_parent()
        if hbox is None:
            self.error = "hbox not found!"
            return None
        if hbox is None:
            return None
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_DIRECTORY,  gtk.ICON_SIZE_BUTTON)
        button = gtk.Button()
        button.set_image(image)
        button.set_label("Browse..")
        button.set_size_request(50,-1)
        hbox.pack_end(button)
        button.show()
        button.connect("clicked", onClickEvent)
        return button

    def deleteButton(self, button):
        if button is not None:
            if button.parent is None:
                return None
            button.parent.remove(button)
        return True

    def findAddDialog(self):
        if self.addDialog is None:
            dialog = component.get("AddTorrentDialog")
            if dialog is None:
                self.error = "AddTorrentDialog not found!"
                return False
            self.addDialog = dialog.dialog
        return self.addDialog is not None

    def findMainWindow(self):
        if self.mainWindow is None:
            comp = component.get("MainWindow")
            if comp is None:
                self.error = "MainWindow not found!"
                return False
            self.mainWindow = comp.window
        return self.mainWindow is not None

    def findEditor(self, dialog, editbox, id):
        if dialog is None:
            return None
        if editbox is None:
            editbox = findwidget(dialog, id)
        if editbox is None:
            self.error = id + " not found!"
        return editbox

    def makeButtons(self):
        if not self.findMainWindow():
            self.handleError()
            return False
        if not self.findAddDialog():
            self.handleError()
            return False

        self.buttons['store']['window'] = self.addDialog
        self.buttons['completed']['window'] = self.addDialog
        self.buttons['completed_tab']['window'] = self.mainWindow
        for name in self.buttons.keys() :
          self.buttons[name]['editbox'] =  self.findEditor(self.buttons[name]['window'], self.buttons[name]['editbox'], self.buttons[name]['id'])
          self.buttons[name]['widget'] = self.addButton(self.buttons[name]['editbox'], self.on_browse_button_clicked)

    def chooseFolder(self, editbox, parent):
        log.debug("RBB:Initial content of "+editbox.get_name()+":"+editbox.get_text())
        dialog = BrowseDialog(editbox.get_text(), self.recent, parent)
        id = dialog.dialog.run()
        if id > 0:
            log.debug("RBB:folder chosen:"+dialog.selectedfolder)
            editbox.set_text(dialog.selectedfolder)
            log.debug("RBB:New content of "+editbox.get_name()+":"+editbox.get_text())
            if self.recent.count(dialog.selectedfolder) > 0:
                self.recent.remove(dialog.selectedfolder)
            self.recent.insert(0, dialog.selectedfolder)
            while len(self.recent) > 10:
                self.recent.pop()
            self.save_recent()
        dialog.dialog.destroy()

    def on_browse_button_clicked(self, widget):
        log.debug("Button clicked")
        for name in self.buttons.keys() :
            if widget == self.buttons[name]['widget']:
                return self.chooseFolder(self.buttons[name]['editbox'], self.buttons[name]['window'])
