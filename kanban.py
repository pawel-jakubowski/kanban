#!/usr/bin/python3

import gi
import cairo
import pickle 
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

class ListBoxRowWithData(Gtk.ListBoxRow):

    def __init__(self, data):
        super(Gtk.ListBoxRow, self).__init__()
        self.data = data
        self.set_layout()
        self.set_drag_and_drop()

    def set_layout(self):
        self.drag_handle = Gtk.EventBox().new()
        self.drag_handle.add(Gtk.Image().new_from_icon_name("open-menu-symbolic", 1))
        self.titlebox = Gtk.Entry()
        self.titlebox.set_has_frame(False)
        self.titlebox.set_text(self.data)
        self.box = Gtk.Box(spacing=2)
        self.box.pack_start(self.drag_handle, False, False, 5)
        self.box.pack_start(self.titlebox, True, True, 0)
        self.add(self.box)

    def set_drag_and_drop(self):
        self.target_entry = Gtk.TargetEntry.new("GTK_LIST_BOX_ROW", Gtk.TargetFlags.SAME_APP, 0)
        self.drag_handle.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [self.target_entry], Gdk.DragAction.MOVE)
        self.drag_handle.connect("drag-begin", self.on_drag_begin)
        self.drag_handle.connect("drag-data-get", self.on_drag_data_get)
        self.drag_dest_set(Gtk.DestDefaults.ALL, [self.target_entry], Gdk.DragAction.MOVE)
        self.connect("drag-data-received", self.on_drag_data_received)

    def on_drag_begin(self, widget, drag_context):
        row = widget.get_ancestor(Gtk.ListBoxRow)
        listbox = row.get_parent()
        listbox.select_row(row)
        surface = cairo.ImageSurface(cairo.Format.ARGB32, row.get_allocated_width(), row.get_allocated_height())
        context = cairo.Context(surface)
        row.draw(context)
        Gtk.drag_set_icon_surface(drag_context, surface)

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        source_index = pickle.loads(data.get_data())
        if source_index == self.get_index():
            return
        listbox = self.get_parent()
        source = listbox.get_row_at_index(source_index)
        position = self.get_index()
        listbox.remove(source)
        listbox.insert(source, position)

    def on_drag_data_get(self, widget, drag_context, data, info, time):
        data.set(Gdk.Atom.intern_static_string("GTK_LIST_BOX_ROW"), 32, pickle.dumps(self.get_index()))

class KanbanWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Kanaban")
        self.set_border_width(20)

        self.box = Gtk.Box(spacing=6)
        self.add(self.box)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.BROWSE)
        self.box.pack_start(listbox, True, True, 0)
       
        items = 'test task abc'.split()

        for item in items:
            listbox.add(ListBoxRowWithData(item))

    def on_button_clicked(self, widget):
        print("Hello")

window = KanbanWindow()
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()

