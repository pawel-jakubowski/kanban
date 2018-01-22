import json

def import_data(settings, filename):
    print("import", filename)
    with open(filename, "r") as f:
        data = json.load(f)
        for l in data["lists"]:
            print(l["name"], l["id"])
        print(data["cards"][0].keys())
        print(data["cards"][0]["name"])
        print(data["cards"][0]["idList"])
        print(data["cards"][0]["pos"])
        print(data["cards"][0]["desc"])
        print(data["cards"][0]["due"])
        print(data["cards"][0]["labels"])

import_data(None, "/home/pjakubow/Downloads/YeV4kGQt.json")
