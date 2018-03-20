from datetime import datetime

#TODO use UTC time
class DueDate:

    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

class Task:

    def __init__(self, title):
        self.title = title
        self.creation_date = datetime.now().timestamp()
        self.update_date = self.creation_date
        self.due_date = None

    def __str__(self):
        return "#%s" % self.title

    def set_title(self, title):
        self.title = title
        self.update_date = datetime.now().timestamp()

    def set_due_date(self, year, month, day):
        self.due_date = DueDate(year, month, day)

