from model.Task import Task
from .TextEntry import TextEntry,ActivableTextEntry

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject


class NewTask(Gtk.ListBoxRow):

    __gsignals__ = {
        "modified": (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }

    def __init__(self):
        super(Gtk.ListBoxRow, self).__init__()
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
            self.entry.uneditable(self)
        else:
            self.entry.editable()

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

    def on_editable_changed(self, widget, is_editable):
        if not is_editable:
            self.grab_focus()

