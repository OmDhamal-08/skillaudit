import os
import sys

import requests


def notify(message):
    webhook = os.environ["SLACK_WEBHOOK_URL"]
    response = requests.post(webhook, json={"text": message}, timeout=10)
    response.raise_for_status()


if __name__ == "__main__":
    notify(sys.argv[1])
    print("sent")
