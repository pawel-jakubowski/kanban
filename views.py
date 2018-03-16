from model.Task import Task
from model.TaskList import TaskList
from model.Board import Board
from view.TextEntry import TextEntry, ActivableTextEntry
from view.TaskView import TaskView
from view.NewTask import NewTask

import cairo
import pickle
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib, GObject, Pango

class TaskListView(Gtk.ListBox):

    __gsignals__ = {
        "modified": (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, tasklist, board):
        super(Gtk.ListBox, self).__init__()
        self.tasklist = tasklist
        self.connect("row-selected", self.on_row_selected)
        self.board = board
        for t in tasklist.tasks:
            task_view = TaskView(t, board)
            self.set_drag_and_drop(task_view)
            task_view.connect("delete", self.on_task_delete)
            task_view.entry.connect("save", self.on_task_modified)
            self.add(task_view)
        new_task = NewTask()
        new_task.connect("modified", lambda w, text: self.add_task(Task(text)))
        self.add(new_task)
        board.connect("task-move-up", lambda w, listname: self.move_up())
        board.connect("task-move-down", lambda w, listname: self.move_down())
        board.connect("task-move-left-top", lambda w, listname: self.move_to_prev_list(listname))
        board.connect("task-move-right-top", lambda w, listname: self.move_to_next_list(listname))

    def get_title(self):
        return self.tasklist.title

    def set_uneditable(self):
        for task_view in self.get_children():
            if not task_view.is_selected() and task_view.entry.is_editable():
                task_view.entry.uneditable()

    def on_row_selected(self, task_list, task_view):
        if task_view is None:
            return
        board = task_list.get_ancestor(BoardView)
        for l in board.lists:
            if l.get_tasklist() is not task_list:
                l.get_tasklist().unselect_all()
                l.get_tasklist().set_uneditable()
        self.set_uneditable()

    def add_task(self, task):
        task_view = TaskView(task, self.board)
        self.set_drag_and_drop(task_view)
        task_view.connect("delete", self.on_task_delete)
        task_view.entry.connect("save", self.on_task_modified)
        # insert before NewTask
        self.insert_task(task_view, len(self.tasklist.tasks))
        task_view.show_all()

    def insert_task(self, task_view, index):
        self.insert(task_view, index)
        self.tasklist.insert(index, task_view.task)
        self.emit("modified")

    def remove_task(self, task_view):
        self.tasklist.remove(task_view.get_index())
        self.remove(task_view)
        self.emit("modified")

    def move_up(self):
        task = self.get_selected_row()
        if task is None:
            return
        position = task.get_index()
        if position > 0:
            self.unselect_row(task)
            self.remove_task(task)
            self.insert_task(task, position-1)
            self.select_row(task)
            task.grab_focus()

    def move_down(self):
        task = self.get_selected_row()
        if task is None:
            return
        position = task.get_index()
        if position < len(self.tasklist.tasks)-1:
            self.unselect_row(task)
            self.remove_task(task)
            self.insert_task(task, position+1)
            self.select_row(task)
            task.grab_focus()

    def move_to_next_list(self, listname):
        if self.get_title() != listname:
            return
        task = self.get_selected_row()
        if task is None:
            return
        board = self.get_ancestor(BoardView)
        current_list_index = board.get_list_index(self.get_title())
        if current_list_index + 1 >= len(board.lists):
            return
        next_list = board.get_list(current_list_index + 1).get_tasklist()
        self.unselect_row(task)
        self.remove_task(task)
        next_list.insert_task(task, 0)
        next_list.select_row(task)
        task.grab_focus()

    def move_to_prev_list(self, listname):
        if self.get_title() != listname:
            return
        task = self.get_selected_row()
        if task is None:
            return
        board = self.get_ancestor(BoardView)
        current_list_index = board.get_list_index(self.get_title())
        if current_list_index == 0:
            return
        prev_list = board.get_list(current_list_index - 1).get_tasklist()
        self.unselect_row(task)
        self.remove_task(task)
        prev_list.insert_task(task, 0)
        prev_list.select_row(task)
        task.grab_focus()

    def on_task_modified(self, widget, title):
        self.emit("modified")

    def on_task_delete(self, widget):
        index = widget.get_index()
        if index > 0:
            index -= 1
        self.remove_task(widget)
        row = self.get_row_at_index(index)
        self.select_row(row)
        row.grab_focus()

    # Drag and Drop
    def set_drag_and_drop(self, task_view):
        task_view.target_entry = Gtk.TargetEntry.new(
            "GTK_LIST_BOX_ROW", Gtk.TargetFlags.SAME_APP, 0)
        task_view.drag_handle.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [
                                         task_view.target_entry], Gdk.DragAction.MOVE)
        task_view.drag_handle.connect("drag-begin", self.on_drag_begin)
        task_view.drag_handle.connect("drag-data-get", self.on_drag_data_get)
        task_view.drag_dest_set(Gtk.DestDefaults.ALL, [
                           task_view.target_entry], Gdk.DragAction.MOVE)
        task_view.connect("drag-data-received", self.on_drag_data_received)

    def on_drag_begin(self, widget, drag_context):
        row = widget.get_ancestor(TaskView)
        listbox = row.get_parent()
        listbox.select_row(row)
        surface = cairo.ImageSurface(
            cairo.Format.ARGB32, row.get_allocated_width(), row.get_allocated_height())
        context = cairo.Context(surface)
        row.draw(context)
        Gtk.drag_set_icon_surface(drag_context, surface)

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        board = widget.get_ancestor(BoardView)
        source_info = pickle.loads(data.get_data())
        source_list_index = board.get_list_index(source_info["list"])
        source_list = board.get_list(source_list_index).get_tasklist()
        target = widget
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
        data.set(Gdk.Atom.intern_static_string(
            "GTK_LIST_BOX_ROW"), 32, pickle.dumps(info))


class KanbanListView(Gtk.Box):

    def __init__(self, tasklist, board):
        super(Gtk.Box, self).__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.title = Gtk.Label()
        self.title.set_text(tasklist.title)
        self.pack_start(self.title, False, False, 0)
        self.tasklist = TaskListView(tasklist, board)
        self.tasklist.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.tasklist)
        self.pack_start(scrolled, True, True, 0)

    def get_tasklist(self):
        return self.tasklist


class BoardView(Gtk.Box):

    __gsignals__ = {
        "signal-task-move-up": (GObject.SIGNAL_ACTION, None, ()),
        "signal-task-move-down": (GObject.SIGNAL_ACTION, None, ()),
        "signal-task-move-left-top": (GObject.SIGNAL_ACTION, None, ()),
        "signal-task-move-right-top": (GObject.SIGNAL_ACTION, None, ()),
        "task-move-up": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "task-move-down": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "task-move-left-top": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "task-move-right-top": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    def __init__(self, board, window):
        super(Gtk.Box, self).__init__(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.board = board
        self.window = window
        self.set_homogeneous(True)

        self.window.bind_accelerator(self, "<Alt>Up", "signal-task-move-up")
        self.window.bind_accelerator(self, "<Alt>Down", "signal-task-move-down")
        self.window.bind_accelerator(self, "<Alt>Left", "signal-task-move-left-top")
        self.window.bind_accelerator(self, "<Alt>Right", "signal-task-move-right-top")
        self.connect("signal-task-move-up", lambda w: self.emit("task-move-up", self.get_focus_list_name()))
        self.connect("signal-task-move-down", lambda w: self.emit("task-move-down", self.get_focus_list_name()))
        self.connect("signal-task-move-left-top", lambda w: self.emit("task-move-left-top", self.get_focus_list_name()))
        self.connect("signal-task-move-right-top", lambda w: self.emit("task-move-right-top", self.get_focus_list_name()))

        hb = Gtk.HeaderBar(show_close_button=True)
        hb.props.title = self.window.appname + " \u2013 " + self.board.title
        self.window.set_titlebar(hb)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button = Gtk.Button()
        button.add(Gtk.Arrow(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE))
        button.connect("clicked", self.on_back_clicked)
        box.add(button)
        hb.pack_start(box)

        self.refresh()

    def get_focus_list_name(self):
        return self.get_focus_child().get_tasklist().get_title()

    def add_tasklist(self, tasklist):
        self.board.add(tasklist)
        l = KanbanListView(tasklist, self)
        l.get_tasklist().connect("modified", lambda w: self.window.user_settings.save())
        self.lists.append(l)
        self.pack_start(l, True, True, 0)

    def get_list(self, index):
        return self.lists[index]

    def get_list_index(self, name):
        for i, l in enumerate(self.lists):
            if l.get_tasklist().get_title() == name:
                return i
        return None

    def on_back_clicked(self, button):
        self.window.draw_boards_list()

    def get_title(self):
        return self.board.title

    def clear(self):
        for child in self.get_children():
            child.destroy()
        self.lists = []

    def refresh(self):
        self.clear()
        for title, l in self.board.tasklists.items():
            self.add_tasklist(l)


class BoardListRow(Gtk.ListBoxRow):

    def __init__(self, title):
        super(Gtk.ListBoxRow, self).__init__()
        self.title = Gtk.Label(title)
        self.add(self.title)

    def get_title(self):
        return self.title.get_text()


class BoardListView(Gtk.ScrolledWindow):

    def __init__(self, settings, window):
        super(Gtk.ScrolledWindow, self).__init__()
        self.settings = settings
        self.window = window
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        hb = Gtk.HeaderBar(show_close_button=True)
        hb.props.title = self.window.appname
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button = Gtk.Button.new_with_label("New Board")
        button.connect("clicked", lambda b: self.create_new_board())
        box.add(button)
        hb.pack_start(box)
        self.window.set_titlebar(hb)

        self.list = Gtk.ListBox()
        self.list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list.connect("row-activated", self.on_row_activated)
        self.add(self.list)
        self.refresh()

    def create_new_board(self):
        dialog = Gtk.Dialog("Create new board", self.window, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK), flags=Gtk.DialogFlags.MODAL)
        entry = Gtk.Entry()
        box = dialog.get_content_area()
        box.set_margin_right(10)
        box.set_margin_left(10)
        box.pack_start(entry, True, False, 0)
        dialog.show_all()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            board_name = entry.get_text()
            if board_name in self.settings.boards.keys():
                print("There is already board", board_name)
            else:
                b = Board(board_name)
                for listname in "Backlog Ready Doing Done".split():
                    b.add(TaskList(listname))
                self.settings.add_board(b)
                self.refresh()
                self.show_all()
        dialog.destroy()

    def refresh(self):
        for child in self.list.get_children():
            self.list.remove(child)
        for board in self.settings.boards:
            self.list.add(BoardListRow(board))

    def on_row_activated(self, listbox, row):
        self.window.draw_board(row.get_title())
