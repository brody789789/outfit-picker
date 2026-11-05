"""
Outfit Picker - core logic
CIS 245 Course Project - Group 5

Functions and dictionaries only: no print(), no input(), no web requests,
and no interface code. app.py, online.py, and morning_notification.py
import from here. Reading and writing our own data files is allowed.
"""

import json
from datetime import date

# ---------------------------------------------------------------------------
# SETTINGS (dictionaries the functions below use)
# ---------------------------------------------------------------------------

# Feature A: the temperature table. Read top to bottom; the first row whose
# "min" the temperature reaches is the one used. Layers stack.
TEMPERATURE_TABLE = [
    {"min": 70, "layers": ["t-shirt"]},
    {"min": 60, "layers": ["t-shirt", "sweatshirt"]},
    {"min": 50, "layers": ["t-shirt", "sweatshirt", "light jacket"]},
    {"min": -999, "layers": ["t-shirt", "sweatshirt", "heavy coat"]},
]

# Feature A: the other numbers, chosen from popular opinion online.
WEATHER_RULES = {
    "shorts_min_temp": 65,          # most-picked "shorts weather" answer in polls is the 60s
    "slides_min_temp": 70,          # sandals/slides once it's warm all day
    "umbrella_rain_chance": 50,     # percent chance of rain
    "breezy_mph": 15,               # National Weather Service: breezy is 15-25 mph
    "windy_mph": 20,                # National Weather Service: windy is 20-30 mph
}

# Feature D: the three times of day.
DAY_TIMES = [
    {"label": "Morning", "hour": 8, "hour_text": "8 AM"},
    {"label": "Afternoon", "hour": 12, "hour_text": "noon"},
    {"label": "Evening", "hour": 18, "hour_text": "6 PM"},
]

# Feature H: timing for the morning message and the weather-service retries.
SCHEDULE = {"default_send_time": "07:00", "send_window_hours": 3}
RETRY_RULES = {"timeout_seconds": 10, "extra_tries": 3, "minutes_between_tries": 5}

# Our data files, relative to the project folder.
DATA_FILES = {
    "profiles": "data/profiles.json",
    "sent_log": "data/sent_log.json",
    "sample_forecast": "data/sample_forecast.json",
}

# Open-Meteo web addresses (free, no key). online.py does the downloading.
WEATHER_SERVICE = {
    "geocoding_url": "https://geocoding-api.open-meteo.com/v1/search",
    "forecast_url": "https://api.open-meteo.com/v1/forecast",
}

# Open-Meteo weather codes that mean clear or mostly clear skies.
CLEAR_SKY_CODES = [0, 1]

# US state abbreviations, used to read "New Haven CT" as "New Haven, CT".
US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


# ---------------------------------------------------------------------------
# FEATURE A: THE RULES AS A TABLE
# ---------------------------------------------------------------------------

# Owner: Jariana (Member 1)
def table_row_for_temp(temp_f):
    """Return the index of the TEMPERATURE_TABLE row for a temperature."""
    for index in range(len(TEMPERATURE_TABLE)):
        if temp_f >= TEMPERATURE_TABLE[index]["min"]:
            return index
    return len(TEMPERATURE_TABLE) - 1


# Owner: Jariana (Member 1)
def wind_speed_to_level(speed_mph):
    """Turn a wind speed in mph into "low", "medium" (breezy), or "high" (windy)."""
    if speed_mph < WEATHER_RULES["breezy_mph"]:
        return "low"
    elif speed_mph < WEATHER_RULES["windy_mph"]:
        return "medium"
    else:
        return "high"


# Owner: Jariana (Member 1)
def layers_for_temp(temp_f, wind_level):
    """
    Return the list of layers for one temperature.
    High wind makes it feel colder, so it moves one row down the table.
    """
    row = table_row_for_temp(temp_f)
    if wind_level == "high" and row < len(TEMPERATURE_TABLE) - 1:
        row = row + 1
    return list(TEMPERATURE_TABLE[row]["layers"])


# Owner: Jariana (Member 1)
def will_rain(rain_chance):
    """True if the chance of rain (percent) is high enough to plan for rain."""
    return rain_chance >= WEATHER_RULES["umbrella_rain_chance"]


# Owner: Jariana (Member 1)
def pick_bottoms(coldest_temp):
    """Shorts or pants, based on the coldest part of the day."""
    if coldest_temp >= WEATHER_RULES["shorts_min_temp"]:
        return "shorts"
    return "pants"


# Owner: Jariana (Member 1)
def pick_shoes(coldest_temp, rain_any):
    """Slides only if it stays warm and dry all day; otherwise sneakers."""
    if coldest_temp >= WEATHER_RULES["slides_min_temp"] and not rain_any:
        return "slides"
    return "sneakers"


# Owner: Jariana (Member 1)
def pick_accessories(rain_any, sunny_any):
    """Return a list of accessories: umbrella for rain, sunglasses for clear skies."""
    accessories = []
    if rain_any:
        accessories.append("umbrella")
    if sunny_any:
        accessories.append("sunglasses")
    return accessories


# Owner: Jariana (Member 1)
def manual_times(temps, rain_labels, wind_level, sunny):
    """
    Turn typed-in weather into the same shape parse_forecast() returns.
    temps: three temperatures (morning, afternoon, evening)
    rain_labels: list of the times it will rain, e.g. ["Evening"]
    """
    times = []
    for index in range(len(DAY_TIMES)):
        spec = DAY_TIMES[index]
        times.append({
            "label": spec["label"],
            "hour_text": spec["hour_text"],
            "temp": round(temps[index]),
            "rain_chance": 100 if spec["label"] in rain_labels else 0,
            "wind_mph": None,
            "wind_level": wind_level,
            "sunny": sunny,
        })
    return times


# ---------------------------------------------------------------------------
# FEATURE D: A DAY, NOT A MOMENT
# ---------------------------------------------------------------------------

# Owner: Cody (Member 3)
def join_items(items):
    """Join a list into readable text: "a", "a and b", "a, b, and c"."""
    if len(items) == 0:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + " and " + items[1]
    return ", ".join(items[:-1]) + ", and " + items[-1]


# Owner: Cody (Member 3)
def describe_change(before, after):
    """Describe how to go from one set of layers to the next."""
    removed = [item for item in before if item not in after]
    added = [item for item in after if item not in before]
    parts = []
    if removed:
        parts.append("take off the " + join_items(removed))
    if added:
        parts.append("put on a " + join_items(added))
    if removed and not added:
        parts.append("stay in the " + join_items(after))
    if not parts:
        return "no change"
    return "; ".join(parts)


# Owner: Cody (Member 3)
def bring_list(layer_lists, rain_any):
    """
    Items worn at some times of day but not all of them, so you carry them.
    Adds an umbrella if rain is likely at any time.
    """
    bring = []
    for layers in layer_lists:
        for item in layers:
            worn_all_day = all(item in other for other in layer_lists)
            if not worn_all_day and item not in bring:
                bring.append(item)
    if rain_any:
        bring.append("umbrella")
    return bring


# Owner: Cody (Member 3)
def build_day_plan(times, high, low):
    """
    Build the whole day's plan from three times of day.
    times: list of dictionaries from parse_forecast() or manual_times()
    Returns a dictionary with each part of the day and the day-wide picks.
    """
    parts = []
    previous = None
    for spot in times:
        layers = layers_for_temp(spot["temp"], spot["wind_level"])
        change = "" if previous is None else describe_change(previous, layers)
        parts.append({
            "label": spot["label"],
            "hour_text": spot["hour_text"],
            "temp": spot["temp"],
            "layers": layers,
            "change": change,
            "rain": will_rain(spot["rain_chance"]),
            "windy": spot["wind_level"] == "high",
        })
        previous = layers

    coldest = min(spot["temp"] for spot in times)
    rain_any = any(part["rain"] for part in parts)
    sunny_any = any(spot["sunny"] and not will_rain(spot["rain_chance"]) for spot in times)
    bottoms = pick_bottoms(coldest)
    shoes = pick_shoes(coldest, rain_any)

    warnings = []
    if not parts[0]["rain"]:
        for part in parts[1:]:
            if part["rain"]:
                warnings.append(
                    f"Rain is likely starting around {part['hour_text']}. "
                    "Bring an umbrella or rain jacket."
                )
                break

    reasons = [
        f"{bottoms.capitalize()} because the coldest part of the day is {coldest}°F "
        f"(shorts at {WEATHER_RULES['shorts_min_temp']}°F and up)."
    ]
    if rain_any:
        reasons.append("Sneakers instead of slides because rain is likely today.")
        reasons.append(
            f"Umbrella because the chance of rain reaches "
            f"{WEATHER_RULES['umbrella_rain_chance']}% or more."
        )
    elif shoes == "sneakers":
        reasons.append(
            f"Sneakers because it drops to {coldest}°F "
            f"(slides at {WEATHER_RULES['slides_min_temp']}°F and up)."
        )
    else:
        reasons.append("Slides are fine: warm and dry all day.")
    for part in parts:
        if part["windy"]:
            reasons.append(
                f"Windy at {part['hour_text']} ({WEATHER_RULES['windy_mph']}+ mph), "
                "so one step warmer than the temperature alone."
            )
    if sunny_any:
        reasons.append("Sunglasses because it's clear and dry for part of the day.")

    return {
        "parts": parts,
        "high": high,
        "low": low,
        "bottoms": bottoms,
        "shoes": shoes,
        "accessories": pick_accessories(rain_any, sunny_any),
        "bring": bring_list([part["layers"] for part in parts], rain_any),
        "warnings": warnings,
        "reasons": reasons,
    }


# ---------------------------------------------------------------------------
# FEATURE H: LOADING THE FORECAST AND THE MORNING MESSAGE
# ---------------------------------------------------------------------------

# Owner: Ben (Member 4)
def normalize_city(text):
    """
    Clean up a typed city so the weather service can find it.
    "New Haven CT" and "new haven  ct" become "New Haven, CT"-style text.
    """
    text = " ".join(text.split())
    if "," in text:
        pieces = [piece.strip() for piece in text.split(",")]
        return ", ".join(piece for piece in pieces if piece)
    words = text.split(" ")
    if len(words) > 1 and words[-1].upper() in US_STATES:
        return " ".join(words[:-1]) + ", " + words[-1].upper()
    for state_name in US_STATES.values():
        ending = " " + state_name.lower()
        if text.lower().endswith(ending) and len(text) > len(ending):
            return text[:-len(ending)] + ", " + state_name
    return text


# Owner: Ben (Member 4)
def geocoding_params(city_text):
    """Build the request details for looking up a city."""
    return {"name": normalize_city(city_text), "count": 1, "language": "en"}


# Owner: Ben (Member 4)
def read_location(data):
    """
    Read the geocoding answer. Returns a dictionary with the city name,
    state, coordinates, and time zone, or None if no city was found.
    """
    if "results" not in data or len(data["results"]) == 0:
        return None
    result = data["results"][0]
    return {
        "name": result["name"],
        "state": result.get("admin1", ""),
        "country_code": result.get("country_code", ""),
        "latitude": result["latitude"],
        "longitude": result["longitude"],
        "timezone": result.get("timezone", "auto"),
    }


# Owner: Ben (Member 4)
def location_label(location):
    """Short name for a place, e.g. "Hamden, CT"."""
    for abbreviation, state_name in US_STATES.items():
        if location["country_code"] == "US" and location["state"] == state_name:
            return location["name"] + ", " + abbreviation
    if location["state"]:
        return location["name"] + ", " + location["state"]
    return location["name"]


# Owner: Ben (Member 4)
def forecast_params(latitude, longitude, timezone):
    """Build the request details for today's hourly forecast."""
    return {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,weather_code,is_day",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": timezone,
        "forecast_days": 1,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
    }


# Owner: Ben (Member 4)
def parse_forecast(data):
    """
    Turn an Open-Meteo forecast (a dictionary) into plain values:
    the date, the high and low, and the weather at 8 AM, noon, and 6 PM.
    """
    hourly = data["hourly"]
    day = data["daily"]["time"][0]
    times = []
    for spec in DAY_TIMES:
        index = hourly["time"].index(f"{day}T{spec['hour']:02d}:00")
        rain_chance = hourly["precipitation_probability"][index]
        wind_mph = hourly["wind_speed_10m"][index]
        times.append({
            "label": spec["label"],
            "hour_text": spec["hour_text"],
            "temp": round(hourly["temperature_2m"][index]),
            "rain_chance": rain_chance if rain_chance is not None else 0,
            "wind_mph": round(wind_mph),
            "wind_level": wind_speed_to_level(wind_mph),
            "sunny": hourly["weather_code"][index] in CLEAR_SKY_CODES and hourly["is_day"][index] == 1,
        })
    return {
        "date": day,
        "high": round(data["daily"]["temperature_2m_max"][0]),
        "low": round(data["daily"]["temperature_2m_min"][0]),
        "times": times,
    }


# Owner: Ben (Member 4)
def format_date(iso_date):
    """Turn "2026-10-15" into "Thursday, October 15"."""
    day = date.fromisoformat(iso_date)
    return f"{day:%A, %B} {day.day}"


# Owner: Ben (Member 4)
def build_message(city, date_text, plan):
    """Build the morning phone message from a day plan. Returns a string."""
    lines = [f"Outfit Picker: {city}", f"{date_text}. High {plan['high']}°F / Low {plan['low']}°F"]
    for index in range(len(plan["parts"])):
        part = plan["parts"][index]
        if index == 0:
            lines.append(f"{part['label']} ({part['temp']}°F): {', '.join(part['layers'])}")
        else:
            lines.append(f"{part['label']} ({part['temp']}°F): {part['change']}")
    lines.append(f"All day: {plan['bottoms']}, {plan['shoes']}")
    for warning in plan["warnings"]:
        lines.append(warning)
    if plan["bring"]:
        lines.append("Bring with you: " + ", ".join(plan["bring"]))
    else:
        lines.append("Bring with you: nothing extra")
    return "\n".join(lines)


# Owner: Ben (Member 4)
def failure_message(city):
    """The short message sent when the weather service never answers."""
    return f"Couldn't get today's forecast for {city}. Check the weather before you head out."


# Owner: Ben (Member 4)
def time_to_minutes(clock_text):
    """Turn "07:30" into minutes after midnight (450)."""
    hours, minutes = clock_text.split(":")
    return int(hours) * 60 + int(minutes)


# Owner: Ben (Member 4)
def is_due(now_clock, send_time, today, last_sent_date):
    """
    True if this person's message should go out now: it is at or after their
    send time (within the send window) and they haven't been messaged today.
    """
    if last_sent_date == today:
        return False
    minutes_late = time_to_minutes(now_clock) - time_to_minutes(send_time)
    return 0 <= minutes_late < SCHEDULE["send_window_hours"] * 60


# Owner: Ben (Member 4)
def load_json(path, default):
    """Read a JSON file into Python data. Returns default if the file is missing."""
    try:
        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default


# Owner: Ben (Member 4)
def save_json(path, data):
    """Write Python data to a JSON file."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")
