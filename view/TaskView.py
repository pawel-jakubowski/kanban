from model.Task import Task
from .TextEntry import TextEntry,ActivableTextEntry

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject


class TaskView(Gtk.ListBoxRow):

    __gsignals__ = {
        "modified": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "delete": (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, task, board):
        super(Gtk.ListBoxRow, self).__init__()
        self.task = task
        self.connect("modified", lambda widget,
                     title: self.task.set_title(title))
        self.buttons = dict()
        self.refresh_layout(self.task)
        self.connect("focus-in-event", self.on_focus)
        self.connect("key-press-event", self.on_key_press)

    def refresh_layout(self, task):
        # Cleanup first
        for child in self.get_children():
            self.remove(child)
        # drag handle
        self.drag_handle = Gtk.EventBox().new()
        self.drag_handle.add(
            Gtk.Image().new_from_icon_name("open-menu-symbolic", 1))
        # entry
        self.entry = ActivableTextEntry(task.title)
        self.entry.connect("changed", self.on_modified)
        self.entry.connect("editable-state-changed", self.on_editable_changed)
        # buttons
        self.buttons["edit"] = Gtk.Button.new_from_icon_name(
            "document-edit-symbolic", 1)
        self.buttons["edit"].connect("clicked", self.on_edit_clicked)
        self.buttons["edit"].set_can_focus(False)
        self.buttons["delete"] = Gtk.Button.new_from_icon_name(
            "user-trash-full-symbolic", 1)
        self.buttons["delete"].connect("clicked", lambda w: self.emit("delete"))
        self.buttons["delete"].set_can_focus(False)
        buttonsbox = Gtk.Box(spacing=1)
        for name, button in self.buttons.items():
            buttonsbox.pack_start(button, False, False, 0)
        # Add all elements
        self.box = Gtk.Box(spacing=2)
        self.box.pack_start(self.drag_handle, False, False, 5)
        self.box.pack_start(self.entry, True, True, 0)
        self.box.pack_end(buttonsbox, False, False, 0)
        self.add(self.box)

    def on_modified(self, widget, title):
        self.emit("modified", title)

    def on_editable_changed(self, widget, is_editable):
        if not is_editable:
            self.grab_focus()

    # Edit
    def on_key_press(self, widget, event):
        if widget is not self:
            return
        k = event.keyval
        if k == Gdk.KEY_Return:
            self.buttons["edit"].clicked()
        elif k == Gdk.KEY_Delete:
            self.buttons["delete"].clicked()

    def on_focus(self, widget, event):
        if self.entry.is_editable():
            self.entry.entry.grab_focus()  # TODO: entry.grab_focus() should be enough

    def on_edit_clicked(self, button):
        if self.entry.is_editable():
            self.entry.uneditable()
        else:
            self.entry.editable()


