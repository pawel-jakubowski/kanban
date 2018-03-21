import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject, Pango

class TextEntry(Gtk.TextView):

    __gsignals__ = {
        "modified-save": (GObject.SIGNAL_RUN_FIRST, None, ()),
        "modified-cancel": (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, data=""):
        super(Gtk.TextView, self).__init__()
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

class ActivableTextEntry(Gtk.Box):

    __gsignals__ = {
        "changed": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "save": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "cancel": (GObject.SIGNAL_RUN_FIRST, None, ()),
        "editable-state-changed": (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
    }

    def __init__(self, data=""):
        super(Gtk.Box, self).__init__()
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


