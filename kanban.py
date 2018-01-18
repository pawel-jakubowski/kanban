#!/usr/bin/python3

import cairo
import pickle
import sys
import os
from datetime import datetime, date

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib, GObject

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
        self.creation_date = datetime.now().timestamp()
        self.update_date = self.creation_date

    def __str__(self):
        return "#%s" % self.title

    def set_title(self, title):
        self.title = title
        self.update_date = datetime.now().timestamp()

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

class KanbanSettings:

    config_dir = os.environ["HOME"] + "/.config/kanban/"

    def __init__(self):
        self.boards = dict()

    def add_board(self, board):
        self.boards[board.title] = board

    def save(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        for key, b in self.boards.items():
            config_path = self.config_dir + key + ".pkl"
            print("save to", config_path)
            with open(config_path, "wb") as f:
                pickle.dump(b, f)

    def load(self):
        if not os.path.exists(self.config_dir):
            self.set_default()
            return
        elif len(os.listdir(self.config_dir)) == 0:
            self.set_default()
            return

        for filename in os.listdir(self.config_dir):
            config_path = self.config_dir + filename
            with open(config_path, "rb") as f:
                board = pickle.load(f)
                print("load", board.title, "from", config_path)
                self.add_board(board)

    def set_default(self):
        b = Board("Work")
        for listname in "Backlog Ready Doing Done".split():
            b.add(TaskList(listname))
        items = 'test task abc'.split()
        for key, l in b.tasklists.items():
            for item in items:
                l.add(Task(item))
        self.add_board(b)

### Views
class TaskEntry(Gtk.TextView):

    def __init__(self, data = ""):
        super(Gtk.TextView, self).__init__()
        self.set_wrap_mode(Gtk.WrapMode.WORD)
        self.set_justification(Gtk.Justification.LEFT)
        self.set_text(data)

    def set_text(self, text):
        self.get_buffer().set_text(text)

    def get_text(self):
        buff = self.get_buffer()
        return buff.get_text(buff.get_start_iter(), buff.get_end_iter(), False)

class TaskView(Gtk.ListBoxRow):

    __gsignals__ = {
        "modified": (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }

    def __init__(self, task):
        super(Gtk.ListBoxRow, self).__init__()
        self.task = task
        self.connect("modified", lambda widget, title: self.task.set_title(title))
        self.set_layout(self.task)
        self.set_drag_and_drop()
        self.show_handler = self.connect("show", self.on_show)
        self.connect("focus-in-event", self.on_focus)
        self.connect("key-press-event", self.on_key_press)

    def set_layout(self, task):
        self.drag_handle = Gtk.EventBox().new()
        self.drag_handle.add(Gtk.Image().new_from_icon_name("open-menu-symbolic", 1))
        self.title = Gtk.Label(task.title)
        self.title.set_line_wrap(True)
        self.titlebox = TaskEntry(task.title)
        self.titlebox.get_buffer().connect("changed", self.on_title_change)
        self.titlebox.connect("key-press-event", self.on_key_press)
        self.editbutton = Gtk.Button.new_from_icon_name("document-edit-symbolic", 1)
        self.editbutton.connect("clicked", self.on_edit_clicked)
        self.box = Gtk.Box(spacing=2)
        self.box.pack_start(self.drag_handle, False, False, 5)
        self.box.pack_start(self.title, False, True, 0)
        self.box.pack_start(self.titlebox, True, True, 0)
        self.box.pack_end(self.editbutton, False, False, 0)
        self.add(self.box)

    def display_titlebox(self):
        self.title.hide()
        self.titlebox.set_text(self.title.get_text())
        self.titlebox.show_all()

    def display_title_label(self):
        self.titlebox.hide()
        self.title.show_all()

    def on_title_change(self, editable):
        new_title = self.titlebox.get_text().strip()
        self.title.set_text(new_title)
        self.emit("modified", new_title)

    # Edit
    def on_key_press(self, widget, event):
        if widget is self.titlebox:
            if event.keyval in [Gdk.KEY_Return, Gdk.KEY_Escape]:
                self.display_title_label()
        elif widget is self:
            if event.keyval == Gdk.KEY_Return:
                self.editbutton.clicked()

    def on_focus(self, widget, event):
        if self.titlebox.is_visible():
            self.titlebox.grab_focus()

    def on_show(self, widget):
        self.titlebox.hide()
        self.disconnect(self.show_handler)

    def on_edit_clicked(self, button):
        if self.title.is_visible():
            self.display_titlebox()
            self.titlebox.grab_focus()
        else:
            self.display_title_label()

    # Drag and Drop

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

class NewTaskView(Gtk.ListBoxRow):

    def __init__(self):
        super(Gtk.ListBoxRow, self).__init__()
        icon = Gtk.Image().new_from_icon_name("list-add-symbolic", 1)
        self.box = Gtk.Box()
        self.add(icon)

class TaskListView(Gtk.ListBox):

    def __init__(self, tasklist):
        super(Gtk.ListBox, self).__init__()
        self.tasklist = tasklist
        self.connect("row-selected", self.on_row_selected)
        for t in tasklist.tasks:
            task_view = TaskView(t)
            self.add(task_view)
        self.add(NewTaskView())

    def get_title(self):
        return self.tasklist.title

    def on_row_selected(self, task_list, task_view):
        if task_view is None:
            return
        board = task_list.get_ancestor(KanbanBoardView)
        for title, l in board.lists.items():
            if title != task_list.get_title():
                l.get_tasklist().unselect_all()

    def add_task(self, task):
        task_view = TaskView(task)
        self.add(task_view)
        self.tasklist.add(task_view.task)

    def insert_task(self, task_view, index):
        self.insert(task_view, index)
        self.tasklist.insert(index, task_view.task)

    def remove_task(self, task_view):
        self.tasklist.remove(task_view.get_index())
        self.remove(task_view)

class KanbanListView(Gtk.Box):

    def __init__(self, tasklist):
        super(Gtk.Box, self).__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.title = Gtk.Label()
        self.title.set_text(tasklist.title)
        self.add(self.title)
        self.tasklist = TaskListView(tasklist)
        self.tasklist.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.add(self.tasklist)

    def get_tasklist(self):
        return self.tasklist

class KanbanBoardView(Gtk.Box):

    def __init__(self, board):
        super(Gtk.Box, self).__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.board = board
        self.lists = dict()
        for title, l in board.tasklists.items():
            self.add_tasklist(l)
        self.set_homogeneous(True)

    def add_tasklist(self, tasklist):
        self.board.add(tasklist)
        l = KanbanListView(tasklist)
        self.lists[tasklist.title] = l
        self.pack_start(l, True, True, 0)

    def get_list(self, name):
        return self.lists[name]

    def get_title(self):
        return self.board.title

class KanbanWindow(Gtk.ApplicationWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL, title="Kanaban")
        self.set_default_icon_name("org.gnome.Todo")
        self.set_title("Kanban")
        self.set_border_width(20)

        self.settings = Gio.Settings.new("com.pjakubow.kanban")
        self.connect("configure-event", self.save_gsettings)
        self.user_settings = KanbanSettings()

        self.load_settings()
        self.draw_boards()

    def draw_boards(self):
        for title, b in self.user_settings.boards.items():
            boardview = KanbanBoardView(b)
            self.add(boardview)
            boardview.show_all()

            self.set_title(self.get_title() + " \u2013 " + boardview.get_title())

    def load_settings(self):
        size = self.settings.get_value("window-size")
        self.resize(size[0], size[1])

        position = self.settings.get_value("window-position")
        if position.n_children() == 2:
            self.move(position[0], position[1])

        if self.settings.get_boolean("window-maximized") == True:
            self.maximize()
        else:
            self.unmaximize()

        self.user_settings.load()

    def save_gsettings(self, window, event):
        self.settings.set_boolean("window-maximized", self.is_maximized())
        w,h = self.get_size()
        self.settings.set_value("window-size", GLib.Variant("ai", [w, h]))
        x,y = self.get_position()
        self.settings.set_value("window-position", GLib.Variant("ai", [x,y]))

class KanbanApplication(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="com.pjakubow.kanban",**kwargs)
        self.window = None
        self.connect("shutdown", self.on_quit)

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

    def on_quit(self, param):
        if self.window is not None:
            self.window.user_settings.save()

if __name__ == "__main__":
    app = KanbanApplication()
    app.run(sys.argv)

