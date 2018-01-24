from model.Task import Task
from model.TaskList import TaskList
from model.Board import Board

import cairo
import pickle
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib, GObject, Pango


class TextEntry(Gtk.TextView):

    __gsignals__ = {
        "modified-save": (GObject.SIGNAL_RUN_FIRST, None, ()),
        "modified-cancel": (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, data=""):
        super(Gtk.TextView, self).__init__()
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


class TaskView(Gtk.ListBoxRow):

    __gsignals__ = {
        "modified": (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }

    def __init__(self, task):
        super(Gtk.ListBoxRow, self).__init__()
        self.task = task
        self.connect("modified", lambda widget,
                     title: self.task.set_title(title))
        self.set_layout(self.task)
        self.set_drag_and_drop()
        self.connect("focus-in-event", self.on_focus)
        self.connect("key-press-event", self.on_key_press)

    def set_layout(self, task):
        self.drag_handle = Gtk.EventBox().new()
        self.drag_handle.add(
            Gtk.Image().new_from_icon_name("open-menu-symbolic", 1))
        self.entry = ActivableTextEntry(task.title)
        self.entry.connect("changed", self.on_modified)
        self.entry.connect("editable-state-changed", self.on_editable_changed)
        self.buttons = dict()
        self.buttons["edit"] = Gtk.Button.new_from_icon_name(
            "document-edit-symbolic", 1)
        self.buttons["edit"].connect("clicked", self.on_edit_clicked)
        self.buttons["edit"].set_can_focus(False)
        self.buttons["delete"] = Gtk.Button.new_from_icon_name(
            "user-trash-full-symbolic", 1)
        self.buttons["delete"].connect("clicked", self.on_delete_clicked)
        self.buttons["delete"].set_can_focus(False)
        buttonsbox = Gtk.Box(spacing=1)
        for name, button in self.buttons.items():
            buttonsbox.pack_start(button, False, False, 0)
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

    # Move
    def move_to_next_list(self):
        board = self.get_ancestor(BoardView)
        current_list = self.get_ancestor(TaskListView)
        current_list_index = board.get_list_index(current_list.get_title())
        if current_list_index >= len(board.lists):
            return
        next_list = board.get_list(current_list_index + 1).get_tasklist()
        current_list.remove_task(self)
        next_list.insert_task(self, 0)

    def move_to_prev_list(self):
        board = self.get_ancestor(BoardView)
        current_list = self.get_ancestor(TaskListView)
        current_list_index = board.get_list_index(current_list.get_title())
        if current_list_index == 0:
            return
        prev_list = board.get_list(current_list_index - 1).get_tasklist()
        current_list.remove_task(self)
        prev_list.insert_task(self, 0)

    # Delete

    def on_delete_clicked(self, button):
        listview = self.get_ancestor(TaskListView)
        index = self.get_index()
        if index > 0:
            index -= 1
        listview.remove_task(self)
        row = listview.get_row_at_index(index)
        listview.select_row(row)
        row.grab_focus()

    # Edit

    def on_key_press(self, widget, event):
        if widget is not self:
            return
        k = event.keyval
        if k == Gdk.KEY_Return:
            self.buttons["edit"].clicked()
        elif k == Gdk.KEY_Delete:
            self.buttons["delete"].clicked()
        elif k == Gdk.KEY_greater:
            self.move_to_next_list()
            self.grab_focus()
        elif k == Gdk.KEY_less:
            self.move_to_prev_list()
            self.grab_focus()

    def on_focus(self, widget, event):
        if self.entry.is_editable():
            self.entry.entry.grab_focus()  # TODO: entry.grab_focus() should be enough

    def on_edit_clicked(self, button):
        if self.entry.is_editable():
            self.entry.uneditable()
        else:
            self.entry.editable()

    # Drag and Drop

    def set_drag_and_drop(self):
        self.target_entry = Gtk.TargetEntry.new(
            "GTK_LIST_BOX_ROW", Gtk.TargetFlags.SAME_APP, 0)
        self.drag_handle.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [
                                         self.target_entry], Gdk.DragAction.MOVE)
        self.drag_handle.connect("drag-begin", self.on_drag_begin)
        self.drag_handle.connect("drag-data-get", self.on_drag_data_get)
        self.drag_dest_set(Gtk.DestDefaults.ALL, [
                           self.target_entry], Gdk.DragAction.MOVE)
        self.connect("drag-data-received", self.on_drag_data_received)

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
        data.set(Gdk.Atom.intern_static_string(
            "GTK_LIST_BOX_ROW"), 32, pickle.dumps(info))


class NewTaskView(Gtk.ListBoxRow):

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
        if widget is self and event.keyval == Gdk.BUTTON_PRIMARY:
            self.toggle_title()

    def on_key_press(self, widget, event):
        if widget is self and event.keyval == Gdk.KEY_Return:
            self.toggle_title()

    def on_focus(self, widget, event):
        if self.entry.is_editable():
            self.entry.entry.grab_focus()  # TODO: fix

    def on_save(self, widget, text):
        task = Task(text)
        self.get_ancestor(TaskListView).add_task(task)
        widget.clear()

    def on_cancel(self, widget):
        widget.clear()

    def on_editable_changed(self, widget, is_editable):
        if not is_editable:
            self.grab_focus()


class TaskListView(Gtk.ListBox):

    def __init__(self, tasklist):
        super(Gtk.ListBox, self).__init__()
        self.tasklist = tasklist
        self.connect("row-selected", self.on_row_selected)
        for t in tasklist.tasks:
            self.add(TaskView(t))
        self.add(NewTaskView())

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
                selected_row = l.get_tasklist().get_selected_row()
                if selected_row is not None:
                    l.get_tasklist().unselect_row(selected_row)
                l.get_tasklist().set_uneditable()
        self.set_uneditable()

    def add_task(self, task):
        task_view = TaskView(task)
        self.tasklist.add(task_view.task)
        # insert before NewTaskView
        self.insert(task_view, len(self.tasklist.tasks) - 1)
        task_view.show_all()

    def insert_task(self, task_view, index):
        self.insert(task_view, index)
        self.tasklist.insert(index, task_view.task)

    def remove_task(self, task_view):
        self.tasklist.remove(task_view.get_index())
        self.remove(task_view)


class KanbanListView(Gtk.Box):

    def __init__(self, tasklist):
        super(Gtk.Box, self).__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.title = Gtk.Label()
        self.title.set_text(tasklist.title)
        self.pack_start(self.title, False, False, 0)
        self.tasklist = TaskListView(tasklist)
        self.tasklist.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.tasklist)
        self.pack_start(scrolled, True, True, 0)

    def get_tasklist(self):
        return self.tasklist


class BoardView(Gtk.Box):

    def __init__(self, board, window):
        super(Gtk.Box, self).__init__(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.board = board
        self.window = window
        self.set_homogeneous(True)

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

    def add_tasklist(self, tasklist):
        self.board.add(tasklist)
        l = KanbanListView(tasklist)
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

    def __init__(self, boards, window):
        super(Gtk.ScrolledWindow, self).__init__()
        self.boards = boards
        self.window = window
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        hb = Gtk.HeaderBar(show_close_button=True)
        hb.props.title = self.window.appname
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button = Gtk.Button.new_with_label("New Board")
        button.set_sensitive(False)
        box.add(button)
        hb.pack_start(box)
        self.window.set_titlebar(hb)

        self.list = Gtk.ListBox()
        self.list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list.connect("row-activated", self.on_row_activated)
        self.add(self.list)
        self.refresh()

    def refresh(self):
        for board in self.boards:
            self.list.add(BoardListRow(board))

    def on_row_activated(self, listbox, row):
        self.window.draw_board(row.get_title())
