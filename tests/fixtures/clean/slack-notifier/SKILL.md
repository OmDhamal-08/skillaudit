---
name: slack-notifier
description: Send a short status message to a Slack channel through an incoming webhook.
---

# Slack notifier

Needs `SLACK_WEBHOOK_URL` set in the environment.

Show the user the exact message first and only send it after they confirm:
`python scripts/notify.py "<message>"`
