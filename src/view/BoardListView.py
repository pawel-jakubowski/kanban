# BoardListView.py
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

from gi.repository import Gtk
from .gi_composites import GtkTemplate
from .Board import Board
from .TaskList import TaskList

# TODO use GtkTemplate


class NewBoardDialog(Gtk.Dialog):

    def __init__(self, window):
        super().__init__("Create new board", window, 0,
                         (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_OK, Gtk.ResponseType.OK), flags=Gtk.DialogFlags.MODAL)
        box = self.get_content_area()
        box.set_margin_right(10)
        box.set_margin_left(10)
        self.entry = Gtk.Entry()
        box.pack_start(self.entry, True, False, 0)
        self.show_all()

    def get_text(self):
        return self.entry.get_text()


@GtkTemplate(ui='/org/gnome/kanban/ui/boardlist.ui')
class BoardListView(Gtk.ScrolledWindow):
    __gtype_name__ = 'BoardListView'

    headerbar, \
        button, \
        list = GtkTemplate.Child().widgets(3)

    def __init__(self, settings, window):
        super().__init__()
        self.init_template()
        self.settings = settings
        self.window = window
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.button.connect("clicked", lambda b: self.create_new_board())
        self.window.set_titlebar(self.headerbar)

        self.list.connect("row-activated", self.on_row_activated)
        self.refresh()

    def create_new_board(self):
        dialog = NewBoardDialog(self.window)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            board_name = dialog.get_text()
            if board_name in self.settings.boards.keys():
                print("There is already board", board_name)
            else:
                b = Board(board_name)
                for listname in "Backlog Ready Doing Done".split():
                    b.add(TaskList(listname))
                self.settings.add_board(b)
                self.refresh()
        dialog.destroy()

    def refresh(self):
        for child in self.list.get_children():
            self.list.remove(child)
        for board in self.settings.boards:
            self.list.add(BoardListRow(board))
        self.show_all()

    def on_row_activated(self, listbox, row):
        self.window.draw_board(row.get_title())


class BoardListRow(Gtk.ListBoxRow):

    def __init__(self, title):
        super().__init__()
        self.title = Gtk.Label(title)
        self.add(self.title)

    def get_title(self):
        return self.title.get_text()
