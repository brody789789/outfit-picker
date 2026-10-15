"""
Outfit Picker
CIS 245 Course Project - Group 5

Recommends an outfit based on today's weather.
Has two modes:
  1. Manual entry - you type in the weather yourself
  2. Auto lookup - the program fetches real weather for a city (stretch goal)
"""

import json
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# CORE LOGIC (this is the MVP - the actual outfit-picking rules)
# ---------------------------------------------------------------------------

def get_outfit_recommendation(temperature, is_raining, wind_level, is_sunny):
    """
    Decide what to wear based on the weather.

    temperature: number, degrees Fahrenheit
    is_raining:  True/False
    wind_level:  "low", "medium", or "high"
    is_sunny:    True/False

    Returns two lists: the outfit items, and the reasons behind them.
    """
    outfit = []
    reasons = []

    # --- Shoes ---
    if is_raining or temperature < 50:
        outfit.append("sneakers")
        reasons.append("sneakers instead of slides because it's cold or wet")
    else:
        outfit.append("slides")
        reasons.append("slides are fine since it's warm and dry")

    # --- Shorts vs. pants ---
    if temperature < 60:
        outfit.append("pants")
    else:
        outfit.append("shorts")

    # --- Shirt / jacket layers ---
    if temperature < 40:
        outfit.append("a heavy coat")
    elif temperature < 60:
        outfit.append("a long-sleeve shirt")
        outfit.append("a jacket")
    else:
        outfit.append("a t-shirt")

    # --- Wind gear ---
    if wind_level == "high" and "a jacket" not in outfit and "a heavy coat" not in outfit:
        outfit.append("a windbreaker")
    if wind_level == "high":
        reasons.append("it's windy, so a jacket/windbreaker is recommended")

    # --- Rain gear ---
    if is_raining:
        outfit.append("an umbrella")
        reasons.append("bring an umbrella because it's raining")

    # --- Sun gear ---
    if is_sunny and not is_raining:
        outfit.append("sunglasses")

    return outfit, reasons


def print_recommendation(outfit, reasons):
    print("\nRecommended outfit:")
    for item in outfit:
        print(f"  - {item}")
    if reasons:
        print("\nWhy:")
        for r in reasons:
            print(f"  - {r}")
    print()


# ---------------------------------------------------------------------------
# MANUAL INPUT MODE (menu-based, no free typing needed except temperature)
# ---------------------------------------------------------------------------

def ask_temperature():
    while True:
        raw = input("Enter today's temperature in F: ").strip()
        try:
            return float(raw)
        except ValueError:
            print("Please enter a number, e.g. 45")


def ask_yes_no(question):
    while True:
        print(question)
        print("  1. Yes")
        print("  2. No")
        choice = input("Choose 1 or 2: ").strip()
        if choice == "1":
            return True
        elif choice == "2":
            return False
        else:
            print("Please enter 1 or 2.\n")


def ask_wind_level():
    while True:
        print("How windy is it?")
        print("  1. Low")
        print("  2. Medium")
        print("  3. High")
        choice = input("Choose 1, 2, or 3: ").strip()
        if choice == "1":
            return "low"
        elif choice == "2":
            return "medium"
        elif choice == "3":
            return "high"
        else:
            print("Please enter 1, 2, or 3.\n")


def manual_mode():
    print("\n--- Manual Weather Entry ---")
    temperature = ask_temperature()
    is_raining = ask_yes_no("\nIs it raining?")
    wind_level = ask_wind_level()
    is_sunny = ask_yes_no("\nIs it sunny?")

    outfit, reasons = get_outfit_recommendation(temperature, is_raining, wind_level, is_sunny)
    print_recommendation(outfit, reasons)


# ---------------------------------------------------------------------------
# STRETCH GOAL: auto-fetch real weather (uses Open-Meteo - free, no API key)
# ---------------------------------------------------------------------------

def get_json(url, params):
    """Download a web address and turn the JSON answer into a Python dictionary."""
    full_url = url + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(full_url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def get_coordinates(city_name):
    """Look up latitude/longitude for a city name."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1}
    data = get_json(url, params)
    if "results" not in data or len(data["results"]) == 0:
        return None
    result = data["results"][0]
    return result["latitude"], result["longitude"], result["name"]


def fetch_weather(latitude, longitude):
    """Fetch current weather for a set of coordinates."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,precipitation,wind_speed_10m,is_day",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
    }
    data = get_json(url, params)
    return data["current"]


def wind_speed_to_level(speed_mph):
    if speed_mph < 8:
        return "low"
    elif speed_mph < 20:
        return "medium"
    else:
        return "high"


def auto_mode():
    print("\n--- Auto Weather Lookup ---")
    city = input("Enter your city (e.g. 'New Haven, CT'): ").strip()

    try:
        location = get_coordinates(city)
        if location is None:
            print("Couldn't find that city. Try being more specific.")
            return
        lat, lon, matched_name = location

        current = fetch_weather(lat, lon)
        temperature = current["temperature_2m"]
        precipitation = current["precipitation"]
        wind_speed = current["wind_speed_10m"]
        is_day = current["is_day"]

        is_raining = precipitation > 0
        wind_level = wind_speed_to_level(wind_speed)
        is_sunny = bool(is_day) and precipitation == 0

        print(f"\nCurrent weather for {matched_name}:")
        print(f"  Temperature: {temperature} F")
        print(f"  Raining: {'Yes' if is_raining else 'No'}")
        print(f"  Wind: {wind_level} ({wind_speed} mph)")
        print(f"  Sunny: {'Yes' if is_sunny else 'No'}")

        outfit, reasons = get_outfit_recommendation(temperature, is_raining, wind_level, is_sunny)
        print_recommendation(outfit, reasons)

    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"\nCouldn't reach the weather service: {e}")
        print("Check your internet connection and try again.")


# ---------------------------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------------------------

def main():
    print("=" * 40)
    print("   OUTFIT PICKER")
    print("=" * 40)

    while True:
        print("\nWhat would you like to do?")
        print("  1. Enter today's weather manually")
        print("  2. Auto-fetch weather for my city")
        print("  3. Exit")
        choice = input("Choose 1, 2, or 3: ").strip()

        if choice == "1":
            manual_mode()
        elif choice == "2":
            auto_mode()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()