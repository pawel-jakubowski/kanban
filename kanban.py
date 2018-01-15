#!/usr/bin/python3

import gi
import cairo
import pickle 
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk



class TaskView(Gtk.ListBoxRow):

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
        row = widget.get_ancestor(TaskView)
        listbox = row.get_parent()
        listbox.select_row(row)
        surface = cairo.ImageSurface(cairo.Format.ARGB32, row.get_allocated_width(), row.get_allocated_height())
        context = cairo.Context(surface)
        row.draw(context)
        Gtk.drag_set_icon_surface(drag_context, surface)

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        board = widget.get_ancestor(KanbanBoard)
        source_info = pickle.loads(data.get_data())
        source_list = board.get_list(source_info["list"]).get_tasklist()
        target = self
        target_list = target.get_ancestor(TaskList)
        if source_info["index"] == target.get_index() and source_info["list"] == target_list.get_title():
            return
        source = source_list.get_row_at_index(source_info["index"])
        position = target.get_index()
        source_list.remove(source)
        target_list.insert(source, position)

    def on_drag_data_get(self, widget, drag_context, data, info, time):
        info = dict()
        info["list"] = widget.get_ancestor(TaskList).get_title()
        info["index"] = widget.get_ancestor(TaskView).get_index()
        data.set(Gdk.Atom.intern_static_string("GTK_LIST_BOX_ROW"), 32, pickle.dumps(info))

class TaskList(Gtk.ListBox):
    
    def __init__(self, title):
        super(Gtk.ListBox, self).__init__()
        self.title = title
        self.connect("row-selected", self.on_row_selected)

    def get_title(self):
        return self.title

    def on_row_selected(self, task_list, task_view):
        if task_view is None:
            return
        board = task_list.get_ancestor(KanbanBoard)
        for title, l in board.lists.items():
            if title != task_list.get_title():
                l.get_tasklist().unselect_all()

class KanbanList(Gtk.Box):

    def __init__(self, title):
        super(Gtk.Box, self).__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.title = Gtk.Label()
        self.title.set_text(title)
        self.add(self.title)
        self.tasklist = TaskList(title)
        self.tasklist.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.add(self.tasklist)

    def add_task(self, title):
        self.tasklist.add(TaskView(title))

    def get_tasklist(self):
        return self.tasklist

class KanbanBoard(Gtk.Box):

    def __init__(self, title):
        super(Gtk.Box, self).__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
       
        self.lists = dict()
        for listname in "Backlog Ready Doing Done".split():
            l = KanbanList(listname)
            self.pack_start(l, True, True, 0)
            self.lists[listname] = l
            items = 'test task abc'.split()
            for item in items:
                l.add_task(item)

    def get_list(self, name):
        return self.lists[name]

class KanbanWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Kanaban")
        self.set_border_width(20)
        self.board = KanbanBoard("Work")
        self.add(self.board)
        
window = KanbanWindow()
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()

