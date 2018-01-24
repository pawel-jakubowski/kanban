#!/usr/bin/python3

import pickle
import sys
import os
import signal
from datetime import datetime, date

import importer.trello
from views import *

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib, GObject, Pango

VERSION = "0.1"

MENU_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section>
      <item>
        <attribute name="action">app.trello-import</attribute>
        <attribute name="label" translatable="yes">_Import from trello</attribute>
      </item>
    </section>
    <section>
      <item>
        <attribute name="action">app.about</attribute>
        <attribute name="label" translatable="yes">_About</attribute>
      </item>
      <item>
        <attribute name="action">app.quit</attribute>
        <attribute name="label" translatable="yes">_Quit</attribute>
        <attribute name="accel">&lt;Primary&gt;q</attribute>
    </item>
    </section>
  </menu>
</interface>
"""


class KanbanSettings:

    config_dir = os.environ["HOME"] + "/.config/kanban/"

    def __init__(self):
        self.boards = dict()

    def add_board(self, board):
        self.boards[board.title] = board

    def save(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        for key, b in self.boards.items():
            config_path = self.config_dir + key + ".pkl"
            print("save to", config_path)
            with open(config_path, "wb") as f:
                pickle.dump(b, f)

    def load(self):
        if not os.path.exists(self.config_dir) or len(os.listdir(self.config_dir)) == 0:
            self.set_default()
            return
        for filename in os.listdir(self.config_dir):
            config_path = self.config_dir + filename
            with open(config_path, "rb") as f:
                board = pickle.load(f)
                print("load", board.title, "from", config_path)
                self.add_board(board)

    def set_default(self):
        b = Board("Work")
        for listname in "Backlog Ready Doing Done".split():
            b.add(TaskList(listname))
        items = 'test task abc'.split()
        for key, l in b.tasklists.items():
            for item in items:
                l.add(Task(item))
        self.add_board(b)


class KanbanWindow(Gtk.ApplicationWindow):

    def __init__(self, user_settings=KanbanSettings(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        Gtk.Window.__init__(
            self, type=Gtk.WindowType.TOPLEVEL)
        self.appname = "Kanban"
        self.set_title(self.appname)
        self.set_default_icon_name("org.gnome.Todo")
        self.set_icon_name("org.gnome.Todo")
        self.set_border_width(20)

        self.settings = Gio.Settings.new("com.pjakubow.kanban")
        self.connect("configure-event", self.save_gsettings)
        self.user_settings = user_settings

        self.active_board = ""
        self.load_settings()

    def draw_boards_list(self):
        self.clean()
        self.add(BoardListView(self.user_settings.boards, self))
        self.active_board = ""
        self.show_all()

    def draw_board(self, name):
        self.clean()
        boardview = BoardView(self.user_settings.boards[name], self)
        self.add(boardview)
        self.active_board = name
        self.show_all()

    def load_settings(self):
        size = self.settings.get_value("window-size")
        self.resize(size[0], size[1])

        position = self.settings.get_value("window-position")
        if position.n_children() == 2:
            self.move(position[0], position[1])

        if self.settings.get_boolean("window-maximized") == True:
            self.maximize()
        else:
            self.unmaximize()

        self.user_settings.load()

        board = self.settings.get_string("selected-board")
        if board != "" and board in self.user_settings.boards:
            self.draw_board(board)
        else:
            self.draw_boards_list()

    def save_gsettings(self, window, event):
        self.settings.set_boolean("window-maximized", self.is_maximized())
        w, h = self.get_size()
        self.settings.set_value("window-size", GLib.Variant("ai", [w, h]))
        x, y = self.get_position()
        self.settings.set_value("window-position", GLib.Variant("ai", [x, y]))
        self.settings.set_string("selected-board", self.active_board)

    def clean(self):
        child = self.get_child()
        if child is not None:
            child.destroy()


class KanbanApplication(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="com.pjakubow.kanban",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs)
        self.window = None
        self.connect("shutdown", self.on_quit)
        self.add_main_option("debug", ord("d"), GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Debug Mode", None)

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("trello-import", None)
        action.connect("activate", self.on_trello_import)
        self.add_action(action)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        builder = Gtk.Builder.new_from_string(MENU_XML, -1)
        self.set_app_menu(builder.get_object("app-menu"))

    def do_activate(self):
        if not self.window:
            if not hasattr(self, "user_settings"):
                self.user_settings = KanbanSettings()
            self.window = KanbanWindow(
                application=self, title="Kanban", user_settings=self.user_settings)
        self.window.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        if options.contains("debug"):
            print("Debug mode selected")
            self.user_settings = KanbanSettings()
            self.user_settings.config_dir = os.path.dirname(
                os.path.abspath(__file__)) + "/.debug_data/"
        self.activate()
        return 0

    def on_trello_import(self, action, param):
        dialog = Gtk.FileChooserDialog("Please choose a trello json file", self.window,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        filter_json = Gtk.FileFilter()
        filter_json.set_name("json files")
        filter_json.add_mime_type("application/json")
        dialog.add_filter(filter_json)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            confirmdialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.WARNING,
                                              Gtk.ButtonsType.YES_NO, "Do you want to clear current tasks? THIS CANNOT BE REVERTED.")
            response = confirmdialog.run()
            if response == Gtk.ResponseType.YES:
                self.user_settings.boards["Work"] = Board("Work")
            importer.trello.import_data(
                self.user_settings, dialog.get_filename())
            self.window.draw_board("Work")
            confirmdialog.destroy()
        dialog.destroy()

    def on_about(self, action, param):
        about_dialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        authors = ["Paweł Jakubowski <pawel-jakubowski@hotmail.com>"]
        about_dialog.set_version(VERSION)
        about_dialog.set_authors(authors)
        about_dialog.set_program_name("Kanban")
        about_dialog.set_logo_icon_name("org.gnome.Todo")
        about_dialog.set_copyright(
            "Copyright \xA9 %d\u2013%d The Kanban author" % (2018, datetime.now().year))
        about_dialog.set_license_type(Gtk.License.MIT_X11)
        about_dialog.present()

    def on_quit(self, param):
        if self.window is not None:
            self.window.save_gsettings(self.window, None)
            self.window.user_settings.save()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = KanbanApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
