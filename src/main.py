# main.py
#
# Copyright (C) 2018 Pawel Jakubowski
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE X CONSORTIUM BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name(s) of the above copyright
# holders shall not be used in advertising or otherwise to promote the sale,
# use or other dealings in this Software without prior written
# authorization.

from datetime import datetime
import sys
import os
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio, GLib, Gdk
from .trello_importer import import_data
from .Board import Board
from .settings import KanbanSettings
from .window import KanbanWindow


class Application(Gtk.Application):

    config_dir = os.environ["HOME"] + "/.config/kanban/"

    def __init__(self, version):
        super().__init__(application_id='org.gnome.kanban',
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.version = version
        self.add_main_option("debug", ord("d"), GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Debug Mode", None)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.create_action("trello-import", self.on_trello_import)
        self.create_action("about", self.on_about)
        self.create_action("quit", self.on_quit)
        builder = Gtk.Builder.new_from_resource(
            "/org/gnome/kanban/ui/menus.ui")
        self.set_app_menu(builder.get_object("app-menu"))

    def create_action(self, name, callback, signal="activate"):
        action = Gio.SimpleAction.new(name, None)
        action.connect(signal, callback)
        self.add_action(action)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = KanbanWindow(application=self, config_dir=self.config_dir)
        win.connect("destroy", self.on_quit)
        win.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        if options.contains("debug"):
            self.config_dir = os.path.dirname(
                os.path.abspath(__file__)) + "/.debug_data/"
            print("Debug mode selected - config dir:", self.config_dir)
        self.activate()
        return 0

    def on_trello_import(self, action, param):
        win = self.props.active_window
        dialog = Gtk.FileChooserDialog("Please choose a trello json file", win,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        filter_json = Gtk.FileFilter()
        filter_json.set_name("json files")
        filter_json.add_mime_type("application/json")
        dialog.add_filter(filter_json)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            confirmdialog = Gtk.MessageDialog(win, 0, Gtk.MessageType.WARNING,
                                              Gtk.ButtonsType.YES_NO, "Do you want to clear current tasks? THIS CANNOT BE REVERTED.")
            response = confirmdialog.run()
            if response == Gtk.ResponseType.YES:
                b = Board("Work")
                self.user_settings.boards["Work"] = b
            import_data(self.user_settings, dialog.get_filename())
            win.draw_board("Work")
            confirmdialog.destroy()
        dialog.destroy()

    def on_about(self, action, param):
        about_dialog = Gtk.AboutDialog(
            transient_for=self.props.active_window, modal=True)
        authors = ["Paweł Jakubowski <pawel-jakubowski@hotmail.com>"]
        about_dialog.set_version(self.version)
        about_dialog.set_authors(authors)
        about_dialog.set_program_name("Kanban")
        about_dialog.set_logo_icon_name("org.gnome.Todo")
        about_dialog.set_copyright(
            "Copyright \xA9 %d\u2013%d The Kanban author" % (2018, datetime.now().year))
        about_dialog.set_license_type(Gtk.License.MIT_X11)
        about_dialog.present()

    def on_quit(self, param):
        if self.props.active_window is not None:
            self.props.active_window.save_board_info()
            self.props.active_window.user_settings.save()
        self.quit()

def main(version):
    style_provider = Gtk.CssProvider()
    style_provider.load_from_resource("/org/gnome/kanban/themes/Adwaita.css")
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    app = Application(version)
    return app.run(sys.argv)
