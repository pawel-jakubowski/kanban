from model.Task import Task
from model.TaskList import TaskList
from model.Board import Board

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib, GObject, Pango


class TaskEntry(Gtk.TextView):

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
        self.show_handler = self.connect("show", self.on_show)
        self.connect("focus-in-event", self.on_focus)
        self.connect("key-press-event", self.on_key_press)

    def set_layout(self, task):
        self.drag_handle = Gtk.EventBox().new()
        self.drag_handle.add(
            Gtk.Image().new_from_icon_name("open-menu-symbolic", 1))
        self.title = Gtk.Label(task.title)
        self.title.set_line_wrap(True)
        self.title.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.title.set_xalign(0)
        self.titlebox = TaskEntry(task.title)
        self.titlebox.get_buffer().connect("changed", self.on_title_change)
        self.titlebox.connect("modified-save", self.on_modified_save)
        self.titlebox.connect("modified-cancel", self.on_modified_save)
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
        self.box.pack_start(self.title, False, False, 0)
        self.box.pack_start(self.titlebox, True, True, 0)
        self.box.pack_end(buttonsbox, False, False, 0)
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

    def on_modified_save(self, widget):
        self.display_title_label()
        self.grab_focus()

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
        self.title = Gtk.Label()
        self.titlebox = TaskEntry()
        self.titlebox.connect("modified-save", self.on_modified_save)
        self.titlebox.connect("modified-cancel", self.on_modified_cancel)
        self.box = Gtk.Box()
        self.box.pack_start(self.icon, False, False, 5)
        self.box.pack_start(self.title, False, True, 0)
        self.box.pack_start(self.titlebox, True, True, 0)
        self.add(self.box)
        self.show_handler = self.connect("show", self.on_show)
        self.connect("focus-in-event", self.on_focus)
        self.connect("key-press-event", self.on_key_press)
        self.connect("button-press-event", self.on_button_press)

    def display_titlebox(self):
        self.title.hide()
        self.titlebox.set_text(self.title.get_text())
        self.titlebox.show_all()

    def display_title_label(self):
        self.titlebox.hide()
        self.title.show_all()

    def toggle_title(self):
        if self.title.is_visible():
            self.display_titlebox()
            self.titlebox.grab_focus()
        else:
            self.display_title_label()

    def on_button_press(self, widget, event):
        if widget is self and event.keyval == Gdk.BUTTON_PRIMARY:
            self.toggle_title()

    def on_key_press(self, widget, event):
        if widget is self and event.keyval == Gdk.KEY_Return:
            self.toggle_title()

    def on_focus(self, widget, event):
        if self.titlebox.is_visible():
            self.titlebox.grab_focus()

    def on_modified_save(self, widget):
        task = Task(widget.get_text().strip())
        self.get_ancestor(TaskListView).add_task(task)
        self.display_title_label()
        self.grab_focus()

    def on_modified_cancel(self, widget):
        self.display_title_label()
        self.grab_focus()

    def on_show(self, widget):
        self.titlebox.hide()
        self.disconnect(self.show_handler)


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
            if not task_view.is_selected() and task_view.titlebox.is_visible():
                task_view.display_title_label()

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
