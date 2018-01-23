from datetime import datetime

class Task:

    def __init__(self, title):
        self.title = title
        self.creation_date = datetime.now().timestamp()
        self.update_date = self.creation_date

    def __str__(self):
        return "#%s" % self.title

    def set_title(self, title):
        self.title = title
        self.update_date = datetime.now().timestamp()
