import json
from pathlib import Path


def get_train_info(path_to_json: Path) -> dict[str, str]:
    with open(path_to_json, "r") as file:
        data = json.loads(file.read())

        train_nums = {}
        # categories,train_no,name are hardcoded need to take care of it later
        for _, v in data["categories"].items():
            for item in v:
                train_nums[item["train_no"]] = item["name"].replace(" ", "_")
    return train_nums


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    path_to_train = BASE_DIR / "trains.json"
    print(get_train_info(path_to_train))
