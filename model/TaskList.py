from model.Task import Task


class TaskList:

    def __init__(self, title):
        self.title = title
        self.tasks = []

    def __str__(self):
        list_str = ">" + self.title
        for t in self.tasks:
            list_str += "\n" + str(t)
        return list_str

    def add_new(self, title):
        task = Task(title)
        self.tasks.append(task)
        return task

    def add(self, task):
        self.tasks.append(task)

    def insert(self, index, task):
        self.tasks.insert(index, task)

    def remove(self, index):
        del self.tasks[index]
