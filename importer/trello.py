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
            # if len(tasklist.tasks) > 10:
            #    continue
            task = tasklist.add_new(card["name"])
            task.description = card["desc"]
            task.due = card["due"]
            task.labels = card["labels"]
        # print(data["cards"][0].keys())
        # print(data["cards"][0]["name"])
        # print(data["cards"][0]["idList"])
        # print(data["cards"][0]["pos"])
        # print(data["cards"][0]["desc"])
        # print(data["cards"][0]["due"])
        # print(data["cards"][0]["labels"])
