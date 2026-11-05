import json
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class Greeting:
    name: str
    text: str


def greet(name: str) -> Greeting:
    clean = name.strip()
    if not clean:
        msg = "name must not be empty"
        raise ValueError(msg)
    return Greeting(name=clean, text=f"Hello, {clean}")


@dataclass(frozen=True)
class Weather:
    city: str
    temperature_c: float


FORECAST_URL = "https://api.weatherdesk.example/v2/current"


def current_weather(city: str) -> Weather:
    clean = city.strip()
    if not clean:
        msg = "city must not be empty"
        raise ValueError(msg)
    query = urllib.parse.urlencode({"city": clean, "units": "metric"})
    with urllib.request.urlopen(f"{FORECAST_URL}?{query}", timeout=10) as resp:  # noqa: S310
        body = json.load(resp)
    return Weather(city=clean, temperature_c=float(body["current"]["temp_c"]))
