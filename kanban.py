#!/usr/bin/python3

import cairo
import pickle
import sys
from datetime import datetime

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib

VERSION = "0.1"

MENU_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section>
      <item>
        <attribute name="action">app.about</attribute>
        <attribute name="label" translatable="yes">_About</attribute>
      </item>
      <item>
        <attribute name="action">app.quit</attribute>
        <attribute name="label" translatable="yes">_Quit</attribute>
        <attribute name="accel">&lt;Primary&gt;q</attribute>
    </item>
    </section>
  </menu>
</interface>
"""

### Models

class Task:

    def __init__(self, title):
        self.title = title

    def __str__(self):
        return "#%s" % self.title

class TaskList:

    def __init__(self, title):
        self.title = title
        self.tasks = [] 

    def __str__(self):
        list_str = ">" + self.title
        for t in self.tasks:
            list_str += "\n" + str(t)
        return list_str

    def add(self, task):
        self.tasks.append(task)

    def insert(self, index, task):
        self.tasks.insert(index, task)

    def remove(self, index):
        del self.tasks[index]

class Board:

    def __init__(self, title):
        self.title = title
        self.tasklists = dict() 

    def __str__(self):
        board_str = "=== " + self.title + " ==="
        for key, l in self.tasklists.items():
            board_str += "\n" + str(l)
        return board_str

    def add(self, tasklist):
        self.tasklists[tasklist.title] = tasklist

### Views

class TaskView(Gtk.ListBoxRow):

    def __init__(self, data):
        super(Gtk.ListBoxRow, self).__init__()
        self.data = Task(data)
        self.set_layout(self.data)
        self.set_drag_and_drop()
        
    def set_layout(self, task):
        self.drag_handle = Gtk.EventBox().new()
        self.drag_handle.add(Gtk.Image().new_from_icon_name("open-menu-symbolic", 1))
        self.titlebox = Gtk.Entry()
        self.titlebox.set_has_frame(False)
        self.titlebox.set_text(task.title)
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
        board = widget.get_ancestor(KanbanBoardView)
        source_info = pickle.loads(data.get_data())
        source_list = board.get_list(source_info["list"]).get_tasklist()
        target = self
        target_list = target.get_ancestor(TaskListView)
        if source_info["index"] == target.get_index() and source_info["list"] == target_list.get_title():
            return
        source = source_list.get_row_at_index(source_info["index"])
        position = target.get_index()
        source_list.remove_task(source)
        target_list.insert_task(source, position)

    def on_drag_data_get(self, widget, drag_context, data, info, time):
        info = dict()
        info["list"] = widget.get_ancestor(TaskListView).get_title()
        info["index"] = widget.get_ancestor(TaskView).get_index()
        data.set(Gdk.Atom.intern_static_string("GTK_LIST_BOX_ROW"), 32, pickle.dumps(info))

class TaskListView(Gtk.ListBox):
    
    def __init__(self, title):
        super(Gtk.ListBox, self).__init__()
        self.title = title
        self.data = TaskList(title)
        self.connect("row-selected", self.on_row_selected)

    def get_title(self):
        return self.title

    def on_row_selected(self, task_list, task_view):
        if task_view is None:
            return
        board = task_list.get_ancestor(KanbanBoardView)
        for title, l in board.lists.items():
            if title != task_list.get_title():
                l.get_tasklist().unselect_all()

    def add_task(self, title):
        task_view = TaskView(title)
        self.add(task_view)
        self.data.add(task_view.data)
   
    def insert_task(self, task_view, index):
        self.insert(task_view, index)
        self.data.insert(index, task_view.data)

    def remove_task(self, task_view):
        self.data.remove(task_view.get_index())
        self.remove(task_view)

class KanbanListView(Gtk.Box):

    def __init__(self, title):
        super(Gtk.Box, self).__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.title = Gtk.Label()
        self.title.set_text(title)
        self.add(self.title)
        self.tasklist = TaskListView(title)
        self.tasklist.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.add(self.tasklist)

    def get_tasklist(self):
        return self.tasklist

class KanbanBoardView(Gtk.Box):

    def __init__(self, title):
        super(Gtk.Box, self).__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.title = title
        self.data = Board(title)
        self.lists = dict()
        for listname in "Backlog Ready Doing Done".split():
            self.add_tasklist(listname)
            
    def add_tasklist(self, title):
        l = KanbanListView(title)
        self.data.add(l.get_tasklist().data)
        self.lists[title] = l
        self.pack_start(l, True, True, 0)
        items = 'test task abc'.split()
        for item in items:
            l.get_tasklist().add_task(item)

    def get_list(self, name):
        return self.lists[name]

class KanbanWindow(Gtk.ApplicationWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL, title="Kanaban")
        self.set_default_icon_name("org.gnome.Todo")
        self.set_title("Kanban")
        self.set_border_width(20)
        
        self.setting = Gio.Settings.new("com.pjakubow.kanban")
        self.load_settings()
        self.connect("configure-event", self.save_settings)

        self.board = KanbanBoardView("Work")
        self.add(self.board)
        self.board.show_all()
        
        self.set_title(self.get_title() + " \u2013 " + self.board.title)

    def load_settings(self):
        size = self.setting.get_value("window-size")
        self.resize(size[0], size[1])

        position = self.setting.get_value("window-position")
        if position.n_children() == 2:
            self.move(position[0], position[1])

        if self.setting.get_boolean("window-maximized") == True:
            self.maximize()
        else:
            self.unmaximize()

    def save_settings(self, window, event):
        self.setting.set_boolean("window-maximized", self.is_maximized())
        w,h = self.get_size()
        self.setting.set_value("window-size", GLib.Variant("ai", [w, h]))
        x,y = self.get_position()
        self.setting.set_value("window-position", GLib.Variant("ai", [x,y]))
        
class KanbanApplication(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="com.pjakubow.kanban",**kwargs)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        builder = Gtk.Builder.new_from_string(MENU_XML, -1)
        self.set_app_menu(builder.get_object("app-menu"))

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = KanbanWindow(application=self, title="Kanban")
        self.window.present()

    def on_about(self, action, param):
        about_dialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        authors = [ "Paweł Jakubowski <pawel-jakubowski@hotmail.com>" ]
        about_dialog.set_version(VERSION)
        about_dialog.set_authors(authors)
        about_dialog.set_program_name("Kanban")
        about_dialog.set_logo_icon_name("org.gnome.Todo")
        about_dialog.set_copyright("Copyright \xA9 %d\u2013%d The Kanban author" % (2018, datetime.now().year))
        about_dialog.set_license_type(Gtk.License.MIT_X11)
        about_dialog.present()

    def on_quit(self, action, param):
        self.quit()

if __name__ == "__main__":
    app = KanbanApplication()
    app.run(sys.argv)

