# TaskListView.py
#
# Copyright (C) 2018 Pawel Jakubowski
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE X CONSORTIUM BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name(s) of the above copyright
# holders shall not be used in advertising or otherwise to promote the sale,
# use or other dealings in this Software without prior written
# authorization.

import cairo
import pickle
from gi.repository import Gtk, GObject, Gdk
from .TaskView import TaskView
from .NewTask import NewTask
from .Task import Task

# TODO use GtkTemplate
class TaskListView(Gtk.ListBox):

    __gsignals__ = {
        "modified": (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    handlers = []

    def __init__(self, tasklist, board):
        super().__init__()
        self.tasklist = tasklist
        self.connect("row-selected", self.on_row_selected)
        self.board = board
        for t in tasklist.tasks:
            task_view = TaskView(t, board)
            self.set_drag_and_drop(task_view)
            index = len(self.get_children())
            h = []
            h.append(task_view.connect("delete", self.on_task_delete))
            h.append(task_view.connect("modified", self.on_task_modified))
            self.handlers.append(h)
            self.add(task_view)
        new_task = NewTask()
        new_task.connect("enter", self.on_new_task_enter)
        new_task.connect("closed", self.on_new_task_closed)
        new_task.connect("modified", lambda w, text: self.add_task(Task(text)))
        self.add(new_task)
        board.connect("task-move-up", lambda w, listname: self.move_up())
        board.connect("task-move-down", lambda w, listname: self.move_down())
        board.connect("task-move-top", lambda w, listname: self.move_top())
        board.connect("task-move-bottom", lambda w,
                      listname: self.move_bottom())
        board.connect("task-move-left-top", lambda w,
                      listname: self.move_to_prev_list(listname))
        board.connect("task-move-right-top", lambda w,
                      listname: self.move_to_next_list(listname))

    def get_board(self):
        return self.board

    def get_title(self):
        return self.tasklist.title

    def on_row_selected(self, task_list, task_view):
        if task_view is None:
            return
        board = task_list.get_board()
        for l in board.lists:
            if l.get_tasklist() is not task_list:
                l.get_tasklist().unselect_all()

    def add_task(self, task):
        task_view = TaskView(task, self.board)
        self.set_drag_and_drop(task_view)
        # insert before NewTask
        self.insert_task(task_view, len(self.tasklist.tasks))
        task_view.show_all()

    def insert_task(self, task_view, index):
        h = []
        h.append(task_view.connect("delete", self.on_task_delete))
        h.append(task_view.connect("modified", self.on_task_modified))
        self.handlers.insert(index, h)
        self.insert(task_view, index)
        self.tasklist.insert(index, task_view.task)
        self.emit("modified")

    def remove_task(self, task_view):
        index = task_view.get_index()
        self.tasklist.remove(index)
        for h in self.handlers[index]:
            task_view.disconnect(h)
        del self.handlers[index]
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
            self.insert_task(task, position - 1)
            self.select_row(task)
            task.grab_focus()

    def move_down(self):
        task = self.get_selected_row()
        if task is None:
            return
        position = task.get_index()
        if position < len(self.tasklist.tasks) - 1:
            self.unselect_row(task)
            self.remove_task(task)
            self.insert_task(task, position + 1)
            self.select_row(task)
            task.grab_focus()

    def move_top(self):
        task = self.get_selected_row()
        if task is None:
            return
        position = task.get_index()
        if position > 0:
            self.unselect_row(task)
            self.remove_task(task)
            self.insert_task(task, 0)
            self.select_row(task)
            task.grab_focus()

    def move_bottom(self):
        task = self.get_selected_row()
        if task is None:
            return
        position = task.get_index()
        lastelem = len(self.tasklist.tasks) - 1
        if position < lastelem:
            self.unselect_row(task)
            self.remove_task(task)
            self.insert_task(task, lastelem)
            self.select_row(task)
            task.grab_focus()

    def move_to_next_list(self, listname):
        if self.get_title() != listname:
            return
        task = self.get_selected_row()
        if task is None:
            return
        current_list_index = self.board.get_list_index(self.get_title())
        if current_list_index + 1 >= len(self.board.lists):
            return
        next_list = self.board.get_list(current_list_index + 1).get_tasklist()
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
        current_list_index = self.board.get_list_index(self.get_title())
        if current_list_index == 0:
            return
        prev_list = self.board.get_list(current_list_index - 1).get_tasklist()
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
        board = widget.get_ancestor(TaskListView).get_board()
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

    def on_new_task_enter(self, widget):
        self.board.remove_noneditable_accelerators()

    def on_new_task_closed(self, widget):
        self.board.add_noneditable_accelerators()
