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

import sys
PY3 =  sys.version_info[0] >= 3

if PY3:
    from gi.repository import Gtk as gtk
    from gi.repository import GdkPixbuf
    import logging
    log = logging.getLogger(__name__)
    from deluge.plugins.pluginbase import Gtk3PluginBase
else:
    from deluge.log import LOG as log
    import gtk
    from deluge.plugins.pluginbase import GtkPluginBase

from deluge.ui.client import client
import deluge.component as component
import deluge.common

importError = None
try:
    import pkg_resources
    from .common import get_resource

except:
    importError = "Install package setuptools to run this plugin!"


def xstr(s):
    if s is None:
        return ''
    return str(s)

def typename(x):
    return type(x).__name__

def widget_id(widget):
    if issubclass(type(widget), gtk.Widget):
        if PY3:
            return gtk.Buildable.get_name(widget)
        else:
            return widget.get_name()
    else:
        return typename(widget) +" is not a GtkWidget"

def widget_descr(widget):
    return "[Type:"+xstr(widget.get_name() if hasattr(widget, "get_name") else typename(widget))+\
          ", Name="+xstr(widget_id(widget))+"]"

def findwidget(container, name, verbose):
    if hasattr(container, 'get_children'):
        ch = container.get_children()
        for widget in ch:
            if widget_id(widget) == name:
              return widget
            if verbose:
                showMessage(None, widget_descr(widget))
            ret = findwidget(widget, name, verbose)
            if ret is not None:
              return ret
    return None

def showMessage(parent, message):
    if parent is None:
        parent = component.get("MainWindow").window
    if PY3:
      md = gtk.MessageDialog(parent, gtk.DialogFlags.MODAL, gtk.MessageType.ERROR, gtk.ButtonsType.OK, 'Error starting plugin: '+ message)
    else:
      md = gtk.MessageDialog(parent, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, 'Error starting plugin: '+ message)
    md.format_secondary_text('Remote browse button plugin')
    md.run()
    md.destroy()

def getTheme():
    if PY3:
        return gtk.IconTheme().get_default()
    else:
        return gtk.icon_theme_get_default()

def caseInsensitive(key):
    return key.lower()


class BrowseDialog:
    def __init__(self, path, recent, parent, RootDirectory, RootDirectoryDisableTraverse):
        self.selectedfolder = path
        self.builder = gtk.Builder()
        self.builder.add_from_file(get_resource('folder_browse_dialog'))
        self.dialog = self.builder.get_object("browse_folders_dialog")
        self.dialog.set_transient_for(parent)

        self.recentliststore = gtk.ListStore(str)
        self.label = self.builder.get_object("selected_folder")
        self.label.set_model(self.recentliststore)
        cell = gtk.CellRendererText()
        self.label.pack_start(cell, True)
        self.label.add_attribute(cell, "text", 0)
        self.handler_id = self.label.connect("changed", self.recent_chosed)

        if PY3:
            self.liststore = gtk.ListStore(GdkPixbuf.Pixbuf, str)
        else:
            self.liststore = gtk.ListStore(gtk.gdk.Pixbuf, str)
        self.iconview = self.builder.get_object("iconview1")
        self.iconview.set_model(self.liststore)
        if PY3:
            column_pixbuf = gtk.TreeViewColumn("Icon", gtk.CellRendererPixbuf(), pixbuf=0)
            self.iconview.append_column(column_pixbuf)
            column_text = gtk.TreeViewColumn("Name", gtk.CellRendererText(), text=1)
            self.iconview.append_column(column_text)
            self.iconview.connect("row-activated", self.subfolder_activated)
        else:
            self.iconview.set_pixbuf_column(0)
            self.iconview.set_text_column(1)
            self.iconview.set_item_width(300)
            self.iconview.connect("item-activated", self.subfolder_activated)


        self.refillList("")
        self.recent = recent
        self.RootDirectory = RootDirectory
        self.RootDirectoryDisableTraverse = RootDirectoryDisableTraverse

    def refillList(self, subfolder):
        client.browsebutton.get_folder_list(self.selectedfolder, subfolder).addCallback(self.get_folder_list_callback)

    def get_folder_list_callback(self, results):
        if results[3]:
            showMessage(None, results[3])
            return

        if self.RootDirectoryDisableTraverse:
            if self.RootDirectory and not results[0].startswith(self.RootDirectory):
                log.debug("Browse Folder: disable=" + str(self.RootDirectoryDisableTraverse) + " matched start with rootDir '" + results[0] + "'")
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
            pixbuf = getTheme().load_icon("go-up", 24, 0)
            self.liststore.append([pixbuf, ".."])
        subfolders = []
        for folder in results[2]:
            subfolders.append(folder)
        subfolders.sort(key=caseInsensitive)
        for folder in subfolders:
            pixbuf = getTheme().load_icon("folder", 24, 0)
            self.liststore.append([pixbuf, folder])
        #self.iconview.set_item_width(-1)

    def subfolder_activated(self, widget, path, column):
        subfolder = self.liststore.get_value(self.liststore.get_iter(path),1)
        self.refillList(subfolder)

    def recent_chosed(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()
        if index != None:
            self.selectedfolder = str(model[index][0])
            self.refillList("")

class AbstractUI:
    def getTheme(self):
        return

    def getWidget(self, id):
        return

    def makeBuilder(self):
        return 

    def OK(self):
        return 

    def findEditor(self, button):
        return True

    def findButton(self, button):
        return True

    def deleteButton(self, button):
        return 

class BrowseButtonUI(AbstractUI):
    error = None
    buttons = None
    addDialog = None
    mainWindow = None
    originalMoveItem = None
    hooksregistered = False
    originalMoveItemPosition = -1
    originalMoveItem = None
    newMoveItem = None
    recent = []
    
    def str2bool(self,v):
        return v.lower() in ("yes", "true", "t", "1")
  
    def enable(self):
        log.debug("RBB:enabling GTK plugin")
        self.error = importError
        if self.error is None:
            self.initializeGUI()
        self.handleError()

    def disable(self):
        self.error = None
        component.get("Preferences").remove_page("Browse Button")
        if self.hooksregistered:
          component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
          component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)
        if self.buttons is not None:
            for name in self.buttons.keys() :
                self.deleteButton(self.buttons[name])
                self.handleError()
        self.swapMenuItems(self.newMoveItem, self.originalMoveItem)

    def handleError(self):
        if self.error is not None:
            showMessage(None, self.error)
        self.error = None

    def on_apply_prefs(self):
        config = {
            "RootDirPath":self.getWidget("RootDir_Path").get_text().rstrip('\\').rstrip('/'),
            "DisableTraversal":str(self.getWidget("RootDir_DisableTraversal").get_active())
        }
        client.browsebutton.set_config(config)
        self.load_RootDirectory()

    def on_show_prefs(self):
        client.browsebutton.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        """callback for on show_prefs"""
        self.getWidget("RootDir_Path").set_text(config["RootDirPath"])
        self.getWidget("RootDir_DisableTraversal").set_active(self.str2bool(config["DisableTraversal"]))
        def browseClicked(something):
            self.chooseFolder(self.getWidget("RootDir_Path"), None)
        self.getWidget("RootDir_Browse").connect("clicked", browseClicked)
        
    def save_recent(self):
        config = {
            "recent": tuple(self.recent)
        }
        client.browsebutton.set_config(config)

    def load_recent(self):
        client.browsebutton.get_config().addCallback(self.initialize_recent)

    def initialize_recent(self, config):
        """callback for load_recent"""
        self.recent = []
        if "recent" in config:
            self.recent = list(config["recent"])
                        
    def load_RootDirectory(self):
        client.browsebutton.get_config().addCallback(self.initialize_RootDirectory)

    def initialize_RootDirectory(self, config):
        """callback for load_RootDirectory"""
        self.RootDirectory = ""
        if "RootDirPath" in config:
            self.RootDirectory = config["RootDirPath"]
        self.RootDirectoryDisableTraverse = False
        if "DisableTraversal" in config:
            self.RootDirectoryDisableTraverse = self.str2bool(config["DisableTraversal"])

    def initializeGUI(self):
        self.makeBuilder()
        self.load_recent()
        self.load_RootDirectory()
        component.get("Preferences").add_page("Browse Button", self.getWidget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
        self.hooksregistered = True
    
        self.makeButtons()
        self.addMoveMenu()
        self.handleError()

    def addMoveMenu(self):
        if self.newMoveItem is None:
            self.newMoveItem = gtk.ImageMenuItem(gtk.STOCK_SAVE_AS, 'Move Storage Advanced')
            self.newMoveItem.set_label("Move Storage")
            self.newMoveItem.show()
            self.newMoveItem.connect("activate", self.on_menu_activated, None)

        torrentmenu = component.get("MenuBar").torrentmenu
        position = 0

        if self.originalMoveItem is None:
            for item in torrentmenu.get_children():
                position = position + 1
                if gtk.Buildable.get_name(item) == "menuitem_move":
                    self.originalMoveItemPosition = position
                    self.originalMoveItem = item
                    break

        #Remove the original move button
        #Insert into original "move" position
        self.swapMenuItems(self.originalMoveItem, self.newMoveItem)

    def swapMenuItems(self, old, new):
        torrentmenu = component.get("MenuBar").torrentmenu
        if old is not None:
            torrentmenu.remove(old)
        if new is not None:
            if self.originalMoveItemPosition >= 0 and self.originalMoveItemPosition < len(torrentmenu.get_children()):
                torrentmenu.insert(new, self.originalMoveItemPosition)
            else:
                torrentmenu.append(new)

    def on_menu_activated(self, widget=None, data=None):
        client.core.get_torrent_status(component.get("TorrentView").get_selected_torrent(), ["save_path"]).addCallback(self.show_move_storage_dialog)

    def show_move_storage_dialog(self, status):
        glade = gtk.Builder.new_from_file(get_resource("myMove_storage_dialog"))
        self.move_storage_dialog = glade.get_object("move_storage_dialog")
        self.move_storage_dialog.set_transient_for(component.get("MainWindow").window)
        self.move_storage_dialog_entry = glade.get_object("entry_destination")
        self.move_storage_browse_button = glade.get_object("browse")
        self.move_storage_entry_destination = glade.get_object("entry_destination")
        self.move_storage_dialog_entry.set_text(status["save_path"])
        def on_dialog_response_event(widget, response_id):

            def on_core_result(result):
                # Delete references
                del self.move_storage_dialog
                del self.move_storage_dialog_entry

            if response_id == self.OK():
                log.debug("Moving torrents to %s",
                          self.move_storage_dialog_entry.get_text())
                path = self.move_storage_dialog_entry.get_text()
                client.core.move_storage(
                    component.get("TorrentView").get_selected_torrents(), path
                ).addCallback(on_core_result)
            self.move_storage_dialog.hide()

        def browseClicked(something):
            self.chooseFolder(self.move_storage_entry_destination, None)
        self.move_storage_dialog.connect("response", on_dialog_response_event)
        self.move_storage_browse_button.connect("clicked", browseClicked)
        self.move_storage_dialog.show()

    def findDialog(self, name):
        comp = component.get(name)
        if comp is None:
            self.error = "Window " + name + " not found!"
            self.handleError
        if hasattr(comp, "dialog"):
            return comp.dialog
        elif hasattr(comp, "window"):
            return comp.window
        else:
            return comp

    def makeButtons(self):
        if self.mainWindow is None:
            self.mainWindow = self.findDialog("MainWindow")
        if self.addDialog is None:
            self.addDialog = self.findDialog("AddTorrentDialog")

        if PY3:
            self.buttons = { 'store' : { 'id': 'hbox_download_location_chooser' , 'editbox': None, 'widget': None , 'window': self.addDialog, 'oldsignal': None}, \
                         'completed' : { 'id': 'hbox_move_completed_chooser' ,    'editbox': None, 'widget': None , 'window': self.addDialog, 'oldsignal': None}, \
                     'completed_tab' : { 'id': 'hbox_move_completed_path_chooser','editbox': None, 'widget': None , 'window': self.mainWindow, 'oldsignal': None} }
        else:
            self.buttons = { 'store' : { 'id': 'entry_download_path' , 'editbox': None, 'widget': None , 'window': self.addDialog}, \
                         'completed' : { 'id': 'entry_move_completed_path' , 'editbox': None, 'widget': None , 'window': self.addDialog}, \
                     'completed_tab' : { 'id': 'entry_move_completed' , 'editbox': None, 'widget': None , 'window': self.mainWindow} }


        for name in self.buttons.keys() :
            button = self.buttons[name]
            editbox = self.findEditor(button)
            if editbox is None:
                self.handleError()
                continue
            button['editbox'] = editbox  

            btn = self.findButton(button)
            if btn is None:
                self.handleError()
                continue

            btn.connect("clicked", self.on_browse_button_clicked)
            log.debug("button connected")
            button['widget'] = btn

    def findwidget(self, container, name, verbose):
        result = findwidget(container, name, verbose)
        if result is None:
            self.error = 'Cannot find widget ' +name + ' inside of ' + widget_descr(container)
            self.handleError()
        return result
        
    def chooseFolder(self, editbox, parent):
        if self.RootDirectory:
            startDir = self.RootDirectory
        else:
            startDir = editbox.get_text()
        dialog = BrowseDialog(startDir, self.recent, parent, self.RootDirectory, self.RootDirectoryDisableTraverse)
        id = dialog.dialog.run()
        if id > 0:
            log.debug("RBB:folder chosen:"+dialog.selectedfolder)
            editbox.set_text(dialog.selectedfolder)
            log.debug("RBB:New content of " + widget_id(editbox) + ":" + editbox.get_text())
            if self.recent.count(dialog.selectedfolder) > 0:
                self.recent.remove(dialog.selectedfolder)
            self.recent.insert(0, dialog.selectedfolder)
            while len(self.recent) > 10:
                self.recent.pop()
            self.save_recent()
        dialog.dialog.destroy()

    def on_browse_button_clicked(self, widget):
        for name in self.buttons.keys() :
            if widget == self.buttons[name]['widget']:
                return self.chooseFolder(self.buttons[name]['editbox'], self.buttons[name]['window'])

if PY3:
    class Gtk3UI_(BrowseButtonUI):
        def getTheme(self):
            return gtk.IconTheme().get_default()

        def getWidget(self, id):
            return self.builder.get_object(id)

        def makeBuilder(self):
            self.builder = gtk.Builder()
            self.builder.add_from_file(get_resource("config"))

        def OK(self):
            return gtk.STOCK_OK

        def findEditor(self, button):
            hbox = self.findwidget(button['window'], button['id'], False)
            if hbox is None:
                return None
            editbox = self.findwidget(hbox, 'entry_text', False)
            if editbox is None:
                return None
            return editbox

        def findButton(self, button):
            hbox = self.findwidget(button['window'], button['id'], False)
            if hbox is None:
                return None
            btn = self.findwidget(hbox, 'button_open_dialog', False)
            log.debug("disconnecting button ")
            ch = hbox.get_children()
            for widget in ch:
                if hasattr(widget, '_on_button_open_dialog_clicked'):
                    button['oldsignal'] = widget._on_button_open_dialog_clicked
                    btn.disconnect_by_func(button['oldsignal'])
                    log.debug('button sucessfilly disconnected')
            return self.findwidget(hbox, 'button_open_dialog', False)

        def deleteButton(self, button):
            if button['widget'] is not None:
                btn = button['widget']
                btn.disconnect_by_func(self.on_browse_button_clicked)
                if button['oldsignal'] is not None:
                    btn.connect("clicked", button['oldsignal'])
                button['widget'] = None
            return True
else:
    class GtkUI_(BrowseButtonUI):
        def getTheme(self):
            return gtk.icon_theme_get_default()

        def getWidget(self, id):
            return self.glade.get_widget(id)
            
        def makeBuilder(self):
            self.glade = gtk.glade.XML(get_resource("config"))

        def OK(self):
            return gtk.RESPONSE_OK

        def findEditor(self, button):
            dialog = button['window']
            id = button['id']
            if dialog is None:
                self.error = "window is not set for "+ id +"!"
                return None
            editbox = findwidget(dialog, id, False)
            if editbox is None:
                self.error = id + " not found!"
            return editbox

        def findButton(self, button):
            """Adds a Button to the editbox inside hbox container."""
            if button['editbox'] is None:
                self.error = "editbox is not set for "+button['id']+"!"
                return None
            editbox = button['editbox']
            hbox = editbox.get_parent()
            if hbox is None:
                self.error = "hbox not found for "+button['id']+"!"
                return None
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_DIRECTORY,  gtk.ICON_SIZE_BUTTON)
            button = gtk.Button()
            button.set_image(image)
            button.set_label("Browse..")
            button.set_size_request(50,-1)
            hbox.pack_end(button)
            button.show()
            return button

        def deleteButton(self, button):
            if button['widget'] is not None:
                if button['widget'].parent is None:
                    return False
                button['widget'].parent.remove(button)
                button['widget'] = None
            return True

if PY3:
    class Gtk3UI(Gtk3PluginBase):
        UI = Gtk3UI_()

        def enable(self):
            return self.UI.enable()
        def disable(self):
            return self.UI.disable()

else:
    class Gtk3UI(GtkPluginBase):
        UI = GtkUI_()

        def enable(self):
            return self.UI.enable()
        def disable(self):
            return self.UI.disable()

