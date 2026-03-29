import json


def get_train_info(path_to_json):
    with open(path_to_json, "r") as file:
        data = json.loads(file.read())

        train_nums = {}
        for k, v in data["categories"].items():
            for item in v:
                train_nums[item["train_no"]] = item["name"].replace(" ", "_")
    return train_nums




if __name__ == "__main__":
    print(get_train_info("config/trains.json"))
