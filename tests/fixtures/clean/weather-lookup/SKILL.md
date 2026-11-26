---
name: weather-lookup
description: Look up the current weather for a city using the OpenWeather API.
---

# Weather lookup

Needs an API key in the `OPENWEATHER_API_KEY` environment variable.
If it is missing, tell the user how to get one instead of failing silently.

Run `python scripts/weather.py "<city>"` and summarize the result in one sentence.
