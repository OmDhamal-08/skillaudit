import json
import sys


def validate(path):
    try:
        with open(path, encoding="utf-8") as fh:
            json.load(fh)
    except json.JSONDecodeError as err:
        return f"{path}: line {err.lineno}, column {err.colno}: {err.msg}"
    return f"{path}: ok"


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(validate(arg))
