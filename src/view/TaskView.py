# TaskView.py
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

from gi.repository import Gtk, Gdk, GObject, Pango, GLib
from .gi_composites import GtkTemplate

from .Task import Task
from .TextEntry import TextEntry, ActivableTextEntry

#TODO use GtkTemplate
class TaskEditDialog(Gtk.Dialog):

    def __init__(self, window, task):
        super().__init__(self, "Task edit", window, 0,
                         (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_SAVE, Gtk.ResponseType.APPLY))

        self.task = task

        entrylabel = Gtk.Label("Title", xalign=0)
        self.entry = TextEntry(self.task.title)
        self.entry.connect(
            "modified-cancel", lambda w: self.emit("response", Gtk.ResponseType.CANCEL))
        self.entry.connect("modified-save", self.on_save)

        calendarlabel = Gtk.Label("Due Date", xalign=0)
        calendarbutton = Gtk.MenuButton()
        calendarbox = Gtk.Box()
        self.calendartext = Gtk.Label("No date set")
        calendarimg = Gtk.Image.new_from_icon_name("pan-down-symbolic", 1)
        calendarbox.pack_start(self.calendartext, True, True, 0)
        calendarbox.pack_end(calendarimg, False, False, 0)
        calendarbutton.add(calendarbox)
        todaybutton = Gtk.Button("Today")
        todaybutton.connect("clicked", lambda w: self.set_today())
        tomorrowbutton = Gtk.Button("Tomorrow")
        tomorrowbutton.connect("clicked", lambda w: self.set_tomorrow())
        buttonsbox = Gtk.Box()
        buttonsbox.pack_start(todaybutton, True, True, 0)
        buttonsbox.pack_start(tomorrowbutton, True, True, 0)
        buttonsbox.pack_start(calendarbutton, True, True, 0)

        datepopover = Gtk.Popover()
        self.calendar = Gtk.Calendar()
        self.calendar.connect("day-selected", self.on_date_selected)
        nodatebutton = Gtk.Button("None")
        nodatebutton.connect("clicked", self.on_date_cleared)
        datebox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 12)
        datebox.pack_start(self.calendar, True, True, 0)
        datebox.pack_end(nodatebutton, False, False, 0)
        datepopover.add(datebox)
        datepopover.show_all()
        datepopover.hide()
        calendarbutton.set_popover(datepopover)

        if hasattr(self.task, "due_date") and self.task.due_date is not None:
            d = self.task.due_date
            self.set_calendar_date(d.year, d.month, d.day)
        else:
            self.calendar.select_day(0)

        box = self.get_content_area()
        box.add(entrylabel)
        box.add(self.entry)
        box.add(calendarlabel)
        box.add(buttonsbox)
        self.show_all()
        self.connect("response", self.on_response)

    def set_today(self):
        date = GLib.DateTime.new_now_local()
        self.set_calendar_date(
            date.get_year(), date.get_month(), date.get_day_of_month())

    def set_tomorrow(self):
        date = GLib.DateTime.new_now_local()
        date = date.add_days(1)
        self.set_calendar_date(
            date.get_year(), date.get_month(), date.get_day_of_month())

    def set_calendar_date(self, year, month, day):
        self.calendar.select_month(month - 1, year)
        self.calendar.select_day(day)
        self.set_calendar_label(year, month, day)

    def set_calendar_label(self, year, month, day):
        if day == 0:
            return
        date = GLib.DateTime.new_local(year, month, day, 0, 0, 0)
        self.calendartext.set_text(date.format("%x"))

    def on_date_selected(self, calendar):
        year, month, day = calendar.get_date()
        self.set_calendar_label(year, month + 1, day)

    def on_date_cleared(self, button):
        self.calendartext.set_text("No date set")
        self.calendar.select_day(0)

    def on_save(self, widget):
        self.emit("response", Gtk.ResponseType.APPLY)

    def on_response(self, widget, response):
        if response == Gtk.ResponseType.APPLY:
            self.task.title = self.entry.get_text()
            y, m, d = self.calendar.get_date()
            if d != 0:
                self.task.set_due_date(y, m + 1, d)
            else:
                self.task.due_date = None


@GtkTemplate(ui='/org/gnome/kanban/ui/task.ui')
class TaskView(Gtk.ListBoxRow):
    __gtype_name__ = 'TaskView'

    __gsignals__ = {
        "modified": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "delete": (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    drag_handle, \
        label, \
        endbox, \
        editbutton, \
        deletebutton, \
        due_date = GtkTemplate.Child().widgets(6)

    def __init__(self, task, board):
        super().__init__()
        self.init_template()
        self.task = task
        self.connect("modified", lambda widget,
                     title: self.task.set_title(title))
        self.connect("key-press-event", self.on_key_press)
        self.editbutton.connect("clicked", self.on_edit_clicked)
        self.deletebutton.connect("clicked", lambda w: self.emit("delete"))
        self.refresh()

    def refresh(self):
        task = self.task
        # entry
        self.label.set_text(task.title)
        # due date
        sc = self.get_style_context()
        sc.remove_class("priority-low")
        sc.remove_class("priority-medium")
        sc.remove_class("priority-high")
        if hasattr(task, "due_date") and task.due_date is not None:
            date = GLib.DateTime.new_local(
                task.due_date.year, task.due_date.month, task.due_date.day, 0, 0, 0)
            self.due_date.set_text(date.format("%e %b"))
            todaytime = GLib.DateTime.new_now_local()
            timediff = date.difference(todaytime) / (24 * 60 * 60 * 1000000)
            if timediff < 1:
                sc.add_class("priority-high")
            elif timediff < 2:
                sc.add_class("priority-medium")
            elif timediff < 3:
                sc.add_class("priority-low")
        else:
            self.due_date.set_text("")
        self.show_all()

    def on_modified(self, widget, title):
        self.emit("modified", title)

    # Edit
    def on_key_press(self, widget, event):
        if widget is not self:
            return
        k = event.keyval
        if k == Gdk.KEY_Return:
            self.editbutton.clicked()
        elif k == Gdk.KEY_Delete:
            self.deletebutton.clicked()

    def on_edit_clicked(self, button):
        dialog = TaskEditDialog(self.get_ancestor(Gtk.Window), self.task)
        response = dialog.run()
        if response == Gtk.ResponseType.APPLY:
            self.emit("modified", self.task.title)
            self.refresh()
        dialog.destroy()
