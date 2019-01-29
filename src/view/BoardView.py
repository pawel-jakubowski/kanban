# BoardView.py
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

from gi.repository import Gtk, GObject
from .gi_composites import GtkTemplate
from .KanbanListView import KanbanListView


@GtkTemplate(ui='/org/gnome/kanban/ui/board.ui')
class BoardView(Gtk.Box):
    __gtype_name__ = 'BoardView'

    __gsignals__ = {
        "signal-task-move-up": (GObject.SIGNAL_ACTION, None, ()),
        "signal-task-move-down": (GObject.SIGNAL_ACTION, None, ()),
        "signal-task-move-top": (GObject.SIGNAL_ACTION, None, ()),
        "signal-task-move-bottom": (GObject.SIGNAL_ACTION, None, ()),
        "signal-task-move-left-top": (GObject.SIGNAL_ACTION, None, ()),
        "signal-task-move-right-top": (GObject.SIGNAL_ACTION, None, ()),
        "signal-exit": (GObject.SIGNAL_ACTION, None, ()),
        "task-move-up": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "task-move-down": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "task-move-top": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "task-move-bottom": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "task-move-left-top": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "task-move-right-top": (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }

    headerbar, \
        returnbutton = GtkTemplate.Child().widgets(2)

    def __init__(self, board, window):
        super().__init__(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.init_template()
        self.board = board
        self.window = window

        self.window.bind_accelerator(self, "<Alt>Up", "signal-task-move-up")
        self.window.bind_accelerator(
            self, "<Alt>Down", "signal-task-move-down")
        self.window.bind_accelerator(
            self, "<Alt><Shift>Up", "signal-task-move-top")
        self.window.bind_accelerator(
            self, "<Alt><Shift>Down", "signal-task-move-bottom")
        self.window.bind_accelerator(
            self, "<Alt>Left", "signal-task-move-left-top")
        self.window.bind_accelerator(
            self, "<Alt>Right", "signal-task-move-right-top")
        self.add_noneditable_accelerators()
        self.connect("signal-task-move-up",
                     lambda w: self.emit("task-move-up", self.get_focus_list_name()))
        self.connect("signal-task-move-down",
                     lambda w: self.emit("task-move-down", self.get_focus_list_name()))
        self.connect("signal-task-move-top",
                     lambda w: self.emit("task-move-top", self.get_focus_list_name()))
        self.connect("signal-task-move-bottom",
                     lambda w: self.emit("task-move-bottom", self.get_focus_list_name()))
        self.connect("signal-task-move-left-top",
                     lambda w: self.emit("task-move-left-top", self.get_focus_list_name()))
        self.connect("signal-task-move-right-top",
                     lambda w: self.emit("task-move-right-top", self.get_focus_list_name()))
        self.connect("signal-exit", self.on_back_clicked)

        self.headerbar.props.title = self.window.appname + " \u2013 " + self.board.title
        self.window.set_titlebar(self.headerbar)
        self.returnbutton.connect("clicked", self.on_back_clicked)

        self.refresh()

    def add_noneditable_accelerators(self):
        self.window.bind_accelerator(self, "Escape", "signal-exit")

    def remove_noneditable_accelerators(self):
        self.window.remove_accelerator(self, "Escape")

    def get_focus_list_name(self):
        return self.get_focus_child().get_tasklist().get_title()

    def add_tasklist_view(self, tasklist):
        l = KanbanListView(tasklist, self)
        l.get_tasklist().connect("modified", lambda w: self.window.user_settings.save())
        self.lists.append(l)
        self.pack_start(l, True, True, 0)

    def get_list(self, index):
        return self.lists[index]

    def get_list_index(self, name):
        for i, l in enumerate(self.lists):
            if l.get_tasklist().get_title() == name:
                return i
        return None

    def on_back_clicked(self, button):
        self.window.draw_boards_list()

    def get_title(self):
        return self.board.title

    def clear(self):
        for child in self.get_children():
            child.destroy()
        self.lists = []

    def refresh(self):
        self.clear()
        for l in self.board.tasklists:
            self.add_tasklist_view(l)
        if len(self.board.tasklists) > 0:
            first_list = self.get_children()[0].get_tasklist()
            first_elem = first_list.get_row_at_index(0)
            first_list.select_row(first_elem)
            first_elem.grab_focus()
