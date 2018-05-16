# settings.py
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

import os
import sys
import json
import pickle

from .Board import Board
from .TaskList import TaskList
from .Task import Task, DueDate


class KanbanSettings:

    def __init__(self, config_dir):
        self.boards = dict()
        self.config_dir = config_dir

    def add_board(self, board):
        self.boards[board.title] = board

    def save(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        for key, b in self.boards.items():
            config_path = self.config_dir + key + ".json"
            print("save to", config_path)
            with open(config_path, "w") as f:
                json.dump(b, f, cls=BoardEncoder)

    def load(self):
        if not os.path.exists(self.config_dir) or len(os.listdir(self.config_dir)) == 0:
            self.set_default()
            return
        for filename in os.listdir(self.config_dir):
            config_path = self.config_dir + filename
            filepath, file_extension = os.path.splitext(config_path)
            if file_extension == ".json":
                self.load_json(config_path)
            elif file_extension == ".pkl":
                # Old configuration
                json_equivalent = filepath + ".json"
                print("old configuration detected", config_path)
                if os.path.exists(json_equivalent):
                    print("new configuration for the same board is present - old configuration ignored.")
                else:
                    print("converting", config_path, "to json...")
                self.load_pkl(config_path)
                self.save()
                if not os.path.exists(json_equivalent):
                    raise RuntimeError("Converting error " + config_path)

    def load_json(self, filepath):
        print("load from", filepath)
        with open(filepath, "r") as f:
            board = json.JSONDecoder(
                object_hook=decodeBoard).decode(f.read())
            print("load", board.title, "from", filepath)
            self.add_board(board)

    def load_pkl(self, filepath):
        # Trick pickle to think that there is 'model' module
        sys.modules['model'] = sys.modules['kanban']
        with open(filepath, "rb") as f:
            board = pickle.load(f)
            print("load", board.title, "from", filepath)
            newboard = Board(board.title)
            # Old configuration has hardcoded dict of tasklists
            newboard.add(board.tasklists["Backlog"])
            newboard.add(board.tasklists["Ready"])
            newboard.add(board.tasklists["Doing"])
            newboard.add(board.tasklists["Done"])
            self.add_board(newboard)

    def set_default(self):
        b = Board("Work")
        for listname in "Backlog Ready Doing Done".split():
            b.add(TaskList(listname))
        items = 'test task abc'.split()
        for l in b.tasklists:
            for item in items:
                l.add(Task(item))
        self.add_board(b)


class BoardEncoder(json.JSONEncoder):

    def default(self, b):
        return b.__dict__


def decodeBoard(d):
    o = None
    if 'day' in d:
        o = DueDate(0, 0, 0)
    elif not 'title' in d:
        return o

    if 'creation_date' in d:
        o = Task(d['title'])
    if 'tasks' in d:
        o = TaskList(d['title'])
    if 'tasklists' in d:
        o = Board(d['title'])
    for p in d:
        setattr(o, p, d[p])
    return o
