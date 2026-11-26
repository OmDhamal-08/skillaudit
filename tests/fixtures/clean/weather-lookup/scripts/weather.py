import os
import sys

import requests

API_URL = "https://api.openweathermap.org/data/2.5/weather"


def current_weather(city):
    api_key = os.environ["OPENWEATHER_API_KEY"]
    response = requests.get(API_URL, params={"q": city, "appid": api_key, "units": "metric"}, timeout=10)
    response.raise_for_status()
    data = response.json()
    return f"{data['name']}: {data['main']['temp']} C, {data['weather'][0]['description']}"


if __name__ == "__main__":
    print(current_weather(sys.argv[1]))
