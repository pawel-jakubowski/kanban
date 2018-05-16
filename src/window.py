# window.py
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

from gi.repository import Gtk, Gio, GLib
from .gi_composites import GtkTemplate

from .BoardView import BoardView
from .BoardListView import BoardListView
from .settings import KanbanSettings


@GtkTemplate(ui='/org/gnome/kanban/ui/window.ui')
class KanbanWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'KanbanWindow'

    def __init__(self, config_dir, **kwargs):
        super().__init__(**kwargs)
        self.init_template()
        self.appname = self.get_title()
        self.accelerators = Gtk.AccelGroup()
        self.add_accel_group(self.accelerators)
        self.settings = Gio.Settings.new("org.gnome.kanban")
        self.connect("configure-event", lambda w, e: self.save_window_info())
        self.user_settings = KanbanSettings(config_dir)
        self.load_settings()

    def draw_boards_list(self):
        self.clean()
        self.add(BoardListView(self.user_settings, self))
        self.active_board = ""
        self.show_all()

    def draw_board(self, name):
        self.clean()
        boardview = BoardView(self.user_settings.boards[name], self)
        self.add(boardview)
        self.active_board = name
        self.show_all()

    def clean(self):
        child = self.get_child()
        if child is not None:
            child.destroy()

    def bind_accelerator(self, widget, accelerator, signal='clicked'):
        key, mod = Gtk.accelerator_parse(accelerator)
        widget.add_accelerator(signal, self.accelerators,
                               key, mod, Gtk.AccelFlags.VISIBLE)

    def load_settings(self):
        size = self.settings.get_value("window-size")
        self.resize(size[0], size[1])
        # Get window position
        position = self.settings.get_value("window-position")
        if position.n_children() == 2:
            self.move(position[0], position[1])
        if self.settings.get_boolean("window-maximized") == True:
            self.maximize()
        else:
            self.unmaximize()
        # Get boards settings
        self.user_settings.load()
        board = self.settings.get_string("selected-board")
        if board != "" and board in self.user_settings.boards:
            self.draw_board(board)
        else:
            self.draw_boards_list()

    def save_window_info(self):
        self.settings.set_boolean("window-maximized", self.is_maximized())
        w, h = self.get_size()
        self.settings.set_value("window-size", GLib.Variant("ai", [w, h]))
        x, y = self.get_position()
        self.settings.set_value("window-position", GLib.Variant("ai", [x, y]))

    def save_board_info(self):
        print("save board", self.active_board)
        self.settings.set_string("selected-board", self.active_board)
