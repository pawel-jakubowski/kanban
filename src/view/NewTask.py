# NewTask.py
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

from gi.repository import Gtk, Gdk, GObject
from .Task import Task
from .TextEntry import TextEntry, ActivableTextEntry


#TODO use GtkTemplate
class NewTask(Gtk.ListBoxRow):

    __gsignals__ = {
        "enter": (GObject.SIGNAL_RUN_FIRST, None, ()),
        "modified": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "closed": (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self):
        super().__init__()
        self.icon = Gtk.Image().new_from_icon_name("list-add-symbolic", 1)
        self.entry = ActivableTextEntry()
        self.entry.connect("editable-state-changed", self.on_editable_changed)
        self.entry.connect("save", self.on_save)
        self.entry.connect("cancel", self.on_cancel)
        self.box = Gtk.Box()
        self.box.pack_start(self.icon, False, False, 5)
        self.box.pack_start(self.entry, True, True, 0)
        self.add(self.box)
        self.connect("focus-in-event", self.on_focus)
        self.connect("key-press-event", self.on_key_press)
        self.connect("button-press-event", self.on_button_press)

    def toggle_title(self):
        if self.entry.is_editable():
            self.entry.uneditable()
        else:
            self.entry.editable()
            self.emit("enter")
            sw = self.get_ancestor(Gtk.ScrolledWindow)
            vadj = sw.get_vadjustment()
            vadj.set_value(vadj.get_upper())
            sw.set_vadjustment(vadj)

    def on_button_press(self, widget, event):
        if widget is self and event.button == Gdk.BUTTON_PRIMARY:
            self.toggle_title()

    def on_key_press(self, widget, event):
        if widget is self and event.keyval == Gdk.KEY_Return:
            self.toggle_title()

    def on_focus(self, widget, event):
        if self.entry.is_editable():
            self.entry.entry.grab_focus()  # TODO: fix

    def on_save(self, widget, text):
        self.emit("modified", text)
        widget.clear()

    def on_cancel(self, widget):
        widget.clear()
        self.emit("closed")

    def on_editable_changed(self, widget, is_editable):
        if not is_editable:
            self.grab_focus()
