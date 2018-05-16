# TextEntry.py
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

from gi.repository import Gtk, Gdk, GObject, Pango

#TODO use GtkTemplate
class TextEntry(Gtk.TextView):

    __gsignals__ = {
        "modified-save": (GObject.SIGNAL_RUN_FIRST, None, ()),
        "modified-cancel": (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, data=""):
        super().__init__()
        self.set_accepts_tab(False)
        self.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.set_justification(Gtk.Justification.LEFT)
        self.set_text(data)
        self.connect("key-press-event", self.on_key_press)

    def set_text(self, text):
        self.get_buffer().set_text(text)

    def get_text(self):
        buff = self.get_buffer()
        return buff.get_text(buff.get_start_iter(), buff.get_end_iter(), False)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Return:
            self.emit("modified-save")
        elif event.keyval == Gdk.KEY_Escape:
            self.emit("modified-cancel")

#TODO use GtkTemplate
class ActivableTextEntry(Gtk.Box):

    __gsignals__ = {
        "changed": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "save": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "cancel": (GObject.SIGNAL_RUN_FIRST, None, ()),
        "editable-state-changed": (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
    }

    def __init__(self, data=""):
        super().__init__()
        self.show_handler = self.connect("show", self.on_show)

        self.label = Gtk.Label(data)
        self.label.set_line_wrap(True)
        self.label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label.set_xalign(0)
        self.entry = TextEntry(data)
        self.entry.get_buffer().connect("changed", self.on_text_change)
        self.entry.connect("modified-save", self.on_modified_save)
        self.entry.connect("modified-cancel", self.on_modified_cancel)
        self.pack_start(self.label, True, True, 0)
        self.pack_start(self.entry, True, True, 0)

    def clear(self):
        self.entry.set_text("")
        self.label.set_text("")

    def is_editable(self):
        return self.entry.is_visible()

    def editable(self):
        self.label.hide()
        self.entry.set_text(self.label.get_text())
        self.entry.show_all()
        self.entry.grab_focus()
        self.emit("editable-state-changed", True)

    def uneditable(self):
        self.entry.hide()
        self.label.show_all()
        self.entry.set_text("")
        self.emit("editable-state-changed", False)

    def on_text_change(self, editable):
        if not self.is_editable():
            return
        new_text = self.entry.get_text().strip()
        self.label.set_text(new_text)
        self.emit("changed", new_text)

    def on_modified_save(self, widget):
        self.emit("save", self.entry.get_text().strip())
        self.uneditable()

    def on_modified_cancel(self, widget):
        self.emit("cancel")
        self.uneditable()

    def on_show(self, widget):
        self.entry.hide()
        self.disconnect(self.show_handler)
