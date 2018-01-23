from model.TaskList import TaskList


class Board:

    def __init__(self, title):
        self.title = title
        self.tasklists = dict()

    def __str__(self):
        board_str = "=== " + self.title + " ==="
        for key, l in self.tasklists.items():
            board_str += "\n" + str(l)
        return board_str

    def add_new(self, title):
        tasklist = TaskList(title)
        self.add(tasklist)
        return tasklist

    def add(self, tasklist):
        self.tasklists[tasklist.title] = tasklist
