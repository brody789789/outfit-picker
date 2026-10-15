
import os
import urllib.request
import urllib.parse

from outfit_picker import (
    get_coordinates,
    fetch_weather,
    wind_speed_to_level,
    get_outfit_recommendation
)

# -----------------------------------------
# SETTINGS
# -----------------------------------------

# Change this to your preferred city
CITY = "Hamden, CT"


# -----------------------------------------
# CREATE MORNING MESSAGE
# -----------------------------------------

def morning_message(outfit, reasons, temperature, city):

    message = "Good morning! ☀️\n\n"

    message += f"Today's weather in {city}:\n"
    message += f"Temperature: {temperature}°F\n\n"

    message += "👕 Your Recommended Outfit:\n"

    for item in outfit:
        message += f"• {item.capitalize()}\n"

    message += "\n💡 Why This Outfit:\n"

    for reason in reasons:
        message += f"• {reason.capitalize()}\n"

    message += "\nHave a great day!"

    return message


# -----------------------------------------
# GET WEATHER AND PICK OUTFIT
# -----------------------------------------

def send_morning_outfit():

    # Get private topic from GitHub Secrets
    topic = os.environ["NTFY_TOPIC"]

    print("Starting morning outfit notification...")

    # Find city coordinates
    location = get_coordinates(CITY)

    if location is None:
        raise ValueError(f"City not found: {CITY}")

    lat, lon, matched_name = location

    # Get current weather
    current = fetch_weather(lat, lon)

    temperature = current["temperature_2m"]
    precipitation = current["precipitation"]
    wind_speed = current["wind_speed_10m"]
    is_day = current["is_day"]

    # Convert weather data
    is_raining = precipitation > 0

    wind_level = wind_speed_to_level(wind_speed)

    is_sunny = bool(is_day) and precipitation == 0

    # Call original outfit recommendation function
    outfit, reasons = get_outfit_recommendation(
        temperature,
        is_raining,
        wind_level,
        is_sunny
    )

    # Create morning notification
    message = morning_message(
        outfit,
        reasons,
        temperature,
        matched_name
    )

    # -----------------------------------------
    # SEND NOTIFICATION TO NTFY
    # -----------------------------------------

    safe_topic = urllib.parse.quote(topic, safe="")

    url = "https://ntfy.sh/" + safe_topic

    request = urllib.request.Request(
        url,
        data=message.encode("utf-8"),
        headers={
            "Title": "Your Morning Outfit",
            "Priority": "default",
            "Tags": "shirt,sunny"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        print("ntfy HTTP status:", response.status)

    print("Morning outfit notification sent!")


# -----------------------------------------
# RUN PROGRAM
# -----------------------------------------

if __name__ == "__main__":
    send_morning_outfit()
