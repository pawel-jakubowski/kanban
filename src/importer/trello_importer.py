# trello_importer.py
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

import json

def import_data(settings, filename):
    print("import", filename)
    with open(filename, "r") as f:
        data = json.load(f)
        board = next(iter(settings.boards.values()))
        lists = dict()
        for l in data["lists"]:
            lists[l["id"]] = l["name"]
            if l["name"] not in board.tasklists:
                tasklist = board.add_new(l["name"])
        for card in data["cards"]:
            if card["closed"]:
                continue
            listname = lists[card["idList"]]
            tasklist = board.tasklists[listname]
            task = tasklist.add_new(card["name"])
            task.description = card["desc"]
            task.due = card["due"]
            task.labels = card["labels"]

