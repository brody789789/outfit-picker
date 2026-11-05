"""
Outfit Picker - everything that talks to the internet
CIS 245 Course Project - Group 5

Interface layer: downloads from Open-Meteo and sends to ntfy. Both app.py
and morning_notification.py use these, so the code lives in one place.
The decisions all come from core.py.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from core import (
    RETRY_RULES,
    WEATHER_SERVICE,
    forecast_params,
    geocoding_params,
    parse_forecast,
    read_location,
)

# Problems that mean "the weather service didn't give us a usable answer".
WEB_ERRORS = (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError)


def get_json(url, params):
    """Download a web address and turn the JSON answer into a Python dictionary."""
    full_url = url + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(full_url, timeout=RETRY_RULES["timeout_seconds"]) as response:
        return json.loads(response.read().decode("utf-8"))


def find_city(city_text):
    """Look up a typed city. Returns a location dictionary, or None if not found."""
    data = get_json(WEATHER_SERVICE["geocoding_url"], geocoding_params(city_text))
    return read_location(data)


def get_forecast(location):
    """Download today's forecast for a location and return it as plain values."""
    params = forecast_params(location["latitude"], location["longitude"], location["timezone"])
    return parse_forecast(get_json(WEATHER_SERVICE["forecast_url"], params))


def get_forecast_with_retries(location):
    """
    Try the forecast, then up to 3 more times, 5 minutes apart.
    Returns the forecast, or None if every try failed. Never guesses.
    """
    tries = 1 + RETRY_RULES["extra_tries"]
    for attempt in range(1, tries + 1):
        try:
            return get_forecast(location)
        except WEB_ERRORS as error:
            print(f"Forecast try {attempt} of {tries} failed: {error}")
            if attempt < tries:
                time.sleep(RETRY_RULES["minutes_between_tries"] * 60)
    return None


def send_ntfy(topic, message):
    """Send one notification to an ntfy topic. Returns the HTTP status code."""
    url = "https://ntfy.sh/" + urllib.parse.quote(topic, safe="")
    request = urllib.request.Request(
        url,
        data=message.encode("utf-8"),
        headers={"Title": "Your Morning Outfit", "Priority": "default", "Tags": "shirt"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.status
