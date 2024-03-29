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
    from deluge.ui.gtk3.path_chooser import PathChooser
else:
    from deluge.log import LOG as log
    import gtk
    from deluge.plugins.pluginbase import GtkPluginBase

from deluge.ui.client import client
import deluge.component as component
import deluge.common
import abc


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

def widget_id(widget, forcepy3 = False):
    if issubclass(type(widget), gtk.Widget):
        if PY3 or forcepy3:
            if gtk.Buildable:
                return gtk.Buildable.get_name(widget)
            else:
                return "gtk.Buildable is not defined!"
        else:
            return widget.get_name()
    else:
        return typename(widget) +" is not a GtkWidget"

def widget_descr(widget):
    return "[Type:" + xstr(typename(widget)) + ", Name="+xstr(widget_id(widget))+"/"+xstr(widget_id(widget, True))+"]"

def findwidget(container, name, verbose):
    if verbose:
        showMessage(None, "\nSearching for entry id:" +name+ "\n inside of:" + widget_descr(container))
    if hasattr(container, 'get_children'):
        ch = container.get_children()
        for widget in ch:
            if (widget_id(widget, False) == name) or (widget_id(widget, True) == name):
              return widget
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

class ButtonRec:
    id = None
    editbox = None
    widget = None
    window = None
    click_handler_id = None
    oldsignal = None
    def __init__(self, id, window):
        self.id = id
        self.window = window

class BrowseDialog:
    def __init__(self, path, recent, parent, RootDirectory, RootDirectoryDisableTraverse):
        self.selectedfolder = path
        self.dialogbuilder = gtk.Builder()
        self.dialogbuilder.add_from_file(get_resource('folder_browse_dialog'))
        self.dialog = self.dialogbuilder.get_object("browse_folders_dialog")
        self.dialog.set_transient_for(parent)

        self.recentliststore = gtk.ListStore(str)
        self.label = self.dialogbuilder.get_object("selected_folder")
        self.label.set_model(self.recentliststore)
        cell = gtk.CellRendererText()
        self.label.pack_start(cell, True)
        self.label.add_attribute(cell, "text", 0)
        self.handler_id = self.label.connect("changed", self.recent_chosed)

        if PY3:
            self.liststore = gtk.ListStore(GdkPixbuf.Pixbuf, str)
        else:
            self.liststore = gtk.ListStore(gtk.gdk.Pixbuf, str)
        self.iconview = self.dialogbuilder.get_object("iconview1")
        self.iconview.set_model(self.liststore)
        column_pixbuf = gtk.TreeViewColumn("Icon", gtk.CellRendererPixbuf(), pixbuf=0)
        self.iconview.append_column(column_pixbuf)
        column_text = gtk.TreeViewColumn("Name", gtk.CellRendererText(), text=1)
        self.iconview.append_column(column_text)
        self.iconview.connect("row-activated", self.subfolder_activated)

        self.refillList("")
        self.recent = recent
        self.RootDirectory = RootDirectory
        self.RootDirectoryDisableTraverse = RootDirectoryDisableTraverse

    def refillList(self, subfolder):
        log.debug("RBB:Getting folders list for "+self.selectedfolder + " / " + subfolder )
        client.browsebutton.get_folder_list(self.selectedfolder, subfolder).addCallback(self.get_folder_list_callback)

    def get_folder_list_callback(self, results):
        log.debug("RBB:got results after folder selection")
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
            try:
                pixbuf = getTheme().load_icon("go-up", 24, 0)
            except:
                pixbuf = None
                
            self.liststore.append([pixbuf, ".."])
        subfolders = []
        for folder in results[2]:
            subfolders.append(folder)
        subfolders.sort(key=caseInsensitive)
        for folder in subfolders:
            try:
                pixbuf = getTheme().load_icon("folder", 24, 0)
            except:
                pixbuf = None
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
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def getTheme(self):
        return

    @abc.abstractmethod
    def findEditor(self, button):
        return

    @abc.abstractmethod
    def findButton(self, button):
        return

    @abc.abstractmethod
    def deleteButton(self, button):
        return 

    @abc.abstractmethod
    def OK(self):
        return 

class BrowseButtonUI(AbstractUI):
    error = None
    buttons = []
    addDialog = None
    moveDialog = None
    mainWindow = None
    configPage = None
    prefDialog = None
    hooksregistered = False
    originalMoveItem = None
    originalMoveItemPosition = -1
    originalMoveItem = None
    newMoveItem = None
    move_storage_dialog_entry = None
    config_root_path_entry = None

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
        if self.buttons is not None:
            for button in self.buttons :
                self.deleteButton(button)
                self.handleError()
        self.buttons.clear()
        self.configPage = None
        component.get("Preferences").remove_page("Browse Button")
        if self.hooksregistered:
          component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
          component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)
        self.swapMenuItems(self.newMoveItem, self.originalMoveItem)
        self.originalMoveItem = None
        self.mainWindow = None
        self.addDialog = None
        self.prefDialog = None

    def handleError(self):
        if self.error is not None:
            showMessage(None, self.error)
        self.error = None

    def on_apply_prefs(self):
        config = {
            "RootDirPath": self.config_root_path_entry.get_text().rstrip('\\').rstrip('/'),
            "DisableTraversal": str(self.configbuilder.get_object("RootDir_DisableTraversal").get_active())
        }
        client.browsebutton.set_config(config)
        self.load_RootDirectory()

    def on_show_prefs(self):
        client.browsebutton.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        """callback for on show_prefs"""
        self.config_root_path_entry.set_text(config["RootDirPath"])
        self.configbuilder.get_object("RootDir_DisableTraversal").set_active(self.str2bool(config["DisableTraversal"]))
        
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
        self.configbuilder = gtk.Builder()
        self.configbuilder.add_from_file(get_resource("config"))
        self.configPage = self.configbuilder.get_object("prefs_box")
        if PY3:
            hbox = self.configbuilder.get_object("hbox_root_path_chooser")
            self.config_root_path_entry = PathChooser('config_root_paths_list', self.prefDialog)
            hbox.add(self.config_root_path_entry)
            hbox.show_all()
        else:
            self.config_root_path_entry = self.configbuilder.get_object("entry_root_path")
        self.load_recent()
        self.load_RootDirectory()
        component.get("Preferences").add_page("Browse Button", self.configPage)
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
        self.hooksregistered = True
    
        self.makeButtons()
        self.addMoveMenu()
        self.handleError()

    def addMoveMenu(self):
        log.debug("adding Menu Item")
        if self.newMoveItem is None:
            self.newMoveItem = gtk.ImageMenuItem(gtk.STOCK_SAVE_AS, 'move_storage_rbb')
            self.newMoveItem.set_label("Move Storage...")
            self.newMoveItem.show()
            self.newMoveItem.connect("activate", self.on_menu_activated, None)

        if self.originalMoveItem is None:
            log.debug("Searching for original menu item...")
            torrentmenu = component.get("MenuBar").torrentmenu
            position = 0
            for item in torrentmenu.get_children():
                position = position + 1
                if widget_id(item) == "menuitem_move":
                    self.originalMoveItemPosition = position
                    self.originalMoveItem = item
                    log.debug("Original move menu item found.")
                    break

        self.swapMenuItems(self.originalMoveItem, self.newMoveItem)
        log.debug("adding Menu Item end")

    def swapMenuItems(self, old, new):
        torrentmenu = component.get("MenuBar").torrentmenu
        #Remove the original move button
        if old is not None:
            torrentmenu.remove(old)
            log.debug("Menu Item Removed: "+xstr(old.get_label()))
        #Insert into original "move" position
        if new is not None:
            if self.originalMoveItemPosition >= 0 and self.originalMoveItemPosition < len(torrentmenu.get_children()):
                torrentmenu.insert(new, self.originalMoveItemPosition)
            else:
                torrentmenu.append(new)
            log.debug("Menu Item Inserted:"+xstr(new.get_label()))

    def on_menu_activated(self, widget=None, data=None):
        client.core.get_torrent_status(component.get("TorrentView").get_selected_torrent(), ["save_path"]).addCallback(self.show_move_storage_dialog)

    def makeMoveStorageDialog(self):
        self.movedialogbuilder = gtk.Builder()
        self.movedialogbuilder.add_from_file(get_resource("myMove_storage_dialog"))
        result = self.movedialogbuilder.get_object("move_storage_dialog")
        result.set_transient_for(component.get("MainWindow").window)
        if PY3:
            hbox = self.movedialogbuilder.get_object("hbox_destination_chooser")
            self.move_storage_dialog_entry = PathChooser('move_completed_paths_list', result)
            hbox.add(self.move_storage_dialog_entry)
            hbox.show_all()
        else:
            self.move_storage_dialog_entry = self.movedialogbuilder.get_object("entry_destination")
        result.connect("response", self.on_dialog_response_event)
        return result

    def show_move_storage_dialog(self, status):
        self.move_storage_dialog_entry.set_text(status["save_path"])
        self.moveDialog.show()

    def on_dialog_response_event(self, widget, response_id):
        if response_id == self.OK():
            log.debug("Moving torrents to %s", self.move_storage_dialog_entry.get_text())
            path = self.move_storage_dialog_entry.get_text()
            client.core.move_storage(component.get("TorrentView").get_selected_torrents(), path).addCallback(self.on_core_result)
        self.moveDialog.hide()

    def on_core_result(self, result):
        log.debug(xstr(result))
        

    def findDialog(self, compName, attribute):
        comp = component.get(compName)
        if comp is None:
            self.error = "Window " + compName + " not found!"
            self.handleError
        if hasattr(comp, attribute):
            return getattr(comp, attribute)
        else:
            self.error = "Component "+compName+" has no attribute "+attribute
        self.handleError
        return None

    def makeButtons(self):
        log.debug('starting to add/connect buttons...')
        if self.mainWindow is None:
            self.mainWindow = self.findDialog("MainWindow", "window")
        if self.addDialog is None:
            self.addDialog = self.findDialog("AddTorrentDialog", "dialog")
        if self.prefDialog is None:
            self.prefDialog = self.findDialog("Preferences", "pref_dialog")
        if self.moveDialog is None:
            self.moveDialog = self.makeMoveStorageDialog()

        if PY3:
            self.buttons.append(ButtonRec('hbox_download_location_chooser' ,      self.addDialog))
            self.buttons.append(ButtonRec('hbox_move_completed_chooser' ,         self.addDialog))
            self.buttons.append(ButtonRec('hbox_move_completed_path_chooser',     self.mainWindow))
            self.buttons.append(ButtonRec('hbox_root_path_chooser',               self.prefDialog))
            self.buttons.append(ButtonRec('hbox_destination_chooser',             self.moveDialog))
            self.buttons.append(ButtonRec('hbox_download_to_path_chooser',        self.prefDialog))
            self.buttons.append(ButtonRec('hbox_move_completed_to_path_chooser',  self.prefDialog))
            self.buttons.append(ButtonRec('hbox_copy_torrent_files_path_chooser', self.prefDialog))
        else:
            self.buttons.append(ButtonRec('entry_download_path' ,       self.addDialog))
            self.buttons.append(ButtonRec('entry_move_completed_path' , self.addDialog))
            self.buttons.append(ButtonRec('entry_move_completed' ,      self.mainWindow))
            self.buttons.append(ButtonRec('entry_root_path' ,           self.configPage))
            self.buttons.append(ButtonRec('entry_destination' ,         self.moveDialog))
            self.buttons.append(ButtonRec('entry_download_path' ,       self.prefDialog))
            self.buttons.append(ButtonRec('entry_move_completed_path' , self.prefDialog))
            self.buttons.append(ButtonRec('entry_torrents_path' ,       self.prefDialog))
            self.buttons.append(ButtonRec('entry_autoadd' ,             self.prefDialog))


        for btnRec in self.buttons :
            editbox = self.findEditor(btnRec)
            if editbox is None:
                self.handleError()
                continue
            btnRec.editbox = editbox  

            btn = self.findButton(btnRec)
            if btn is None:
                self.handleError()
                continue

            log.debug("connecting button to browse dialog:"+btnRec.id)
            btnRec.click_handler_id = btn.connect("clicked", self.on_browse_button_clicked)
            log.debug("button connected:"+btnRec.id)
            btnRec.widget = btn
        log.debug('all buttons connected.')

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
        log.debug("RBB: Initial folder:" + startDir)
        if not issubclass(type(parent), gtk.Window):
            parent = None
        dialog = BrowseDialog(startDir, self.recent, parent, self.RootDirectory, self.RootDirectoryDisableTraverse)
        if dialog.dialog.run() == self.OK():
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
        for btnRec in self.buttons :
            if widget == btnRec.widget:
                return self.chooseFolder(btnRec.editbox, btnRec.window)

if PY3:
    class Gtk3UI_(BrowseButtonUI):
        def getTheme(self):
            return gtk.IconTheme().get_default()

        def findEditor(self, btnRec):
            hbox = self.findwidget(btnRec.window, btnRec.id, False)
            if hbox is None:
                return None
            editbox = self.findwidget(hbox, 'entry_text', False)
            if editbox is None:
                return None
            return editbox

#        def get_handler_id(self, obj, signal_name):
#            signal_id, detail = gtk.signal_parse_name(signal_name, obj, True)
#            return gtk.signal_handler_find(obj, GObject.SignalMatchType.ID, signal_id, detail, None, None, None)

        def findButton(self, btnRec):
            hbox = self.findwidget(btnRec.window, btnRec.id, False)
            if hbox is None:
                return None
            btn = self.findwidget(hbox, 'button_open_dialog', False)
            log.debug("disconnecting old signal from button "+btnRec.id)
            ch = hbox.get_children()
            for widget in ch:
                if hasattr(widget, '_on_button_open_dialog_clicked'):
                    btnRec.oldsignal = widget._on_button_open_dialog_clicked
                    btn.disconnect_by_func(btnRec.oldsignal)
                    log.debug('button sucessfilly disconnected:'+ btnRec.id)
            return self.findwidget(hbox, 'button_open_dialog', False)

        def deleteButton(self, btnRec):
            if btnRec.widget is not None:
                log.debug('restoring old signal for button:'+ btnRec.id)
                btn = btnRec.widget
                if btnRec.click_handler_id is not None:
                    btn.disconnect(btnRec.click_handler_id)
                if btnRec.oldsignal is not None:
                    btn.connect("clicked", btnRec.oldsignal)
                    btnRec.oldsignal = None
                    log.debug('old signal for button restored:'+ btnRec.id)
                btnRec.widget = None
            return True

        def OK(self):
            return gtk.ResponseType.OK
else:
    class GtkUI_(BrowseButtonUI):
        def getTheme(self):
            return gtk.icon_theme_get_default()

        def findEditor(self, btnRec):
            dialog = btnRec.window
            id = btnRec.id
            if dialog is None:
                self.error = "window is not set for "+ id +"!"
                return None
            editbox = findwidget(dialog, id, False)
            if editbox is None:
                self.error = id + " not found!"
            return editbox

        def findButton(self, btnRec):
            """Adds a Button to the editbox inside hbox container."""
            if btnRec.editbox is None:
                self.error = "editbox is not set for "+btnRec.id+"!"
                return None
            hbox = btnRec.editbox.get_parent()
            if hbox is None:
                self.error = "hbox not found for "+btnRec.id+"!"
                return None
            #image = gtk.Image()
            #image.set_from_stock(gtk.STOCK_DIRECTORY,  gtk.ICON_SIZE_BUTTON)
            btn = gtk.Button()
            #button.set_image(image)
            btn.set_label("...")
            btn.set_size_request(50,20)
            hbox.pack_end(btn, False, False)
            btn.show()
            return btn

        def deleteButton(self, btnRec):
            btn = btnRec.widget
            if btn is not None:
                if btn.parent is None:
                    return False
                btn.parent.remove(btn)
                btnRec.widget = None
            return True

        def OK(self):
            return gtk.RESPONSE_OK
if PY3:
    class Gtk3UI(Gtk3PluginBase):
        UI = Gtk3UI_()

        def enable(self):
            return self.UI.enable()
        def disable(self):
            return self.UI.disable()

else:
    class GtkUI(GtkPluginBase):
        UI = GtkUI_()

        def enable(self):
            return self.UI.enable()
        def disable(self):
            return self.UI.disable()

