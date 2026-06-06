import json

from .models import Save


def read_locations() -> list[Save]:
    with open("locations.json") as f:
        data = json.load(f)
    return [Save(name=entry["name"], paths=entry["paths"]) for entry in data]


def read_git_url() -> str:
    with open("gitFilePath.txt") as f:
        return f.readline().strip()
