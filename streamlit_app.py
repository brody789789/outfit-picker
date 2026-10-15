
import streamlit as st
import urllib.error
import json

from outfit_picker import (
    get_outfit_recommendation,
    get_coordinates,
    fetch_weather,
    wind_speed_to_level
)

st.set_page_config(
    page_title="Outfit Picker",
    page_icon="👕",
    layout="centered"
)

st.title("👕 Outfit Picker")
st.write("Find the perfect outfit based on today's weather!")

mode = st.radio(
    "Choose how to enter the weather:",
    ["Manual Entry", "Automatic Weather Lookup"]
)


def display_outfit(outfit, reasons):
    st.success("Your outfit is ready!")

    st.subheader("👔 Recommended Outfit")
    for item in outfit:
        st.write("✅ " + item.capitalize())

    st.subheader("💡 Why This Outfit?")
    for reason in reasons:
        st.write("• " + reason.capitalize())


if mode == "Manual Entry":

    st.header("🌤️ Enter Today's Weather")

    temperature = st.number_input(
        "Temperature (°F)",
        value=60.0
    )

    is_raining = st.checkbox("Is it raining?")

    wind_level = st.selectbox(
        "Wind Level",
        ["low", "medium", "high"]
    )

    is_sunny = st.checkbox("Is it sunny?")

    if st.button("Get My Outfit", type="primary"):

        outfit, reasons = get_outfit_recommendation(
            temperature,
            is_raining,
            wind_level,
            is_sunny
        )

        display_outfit(outfit, reasons)


else:

    st.header("📍 Automatic Weather Lookup")

    city = st.text_input(
        "Enter your city",
        placeholder="New Haven, CT"
    )

    if st.button("Find My Outfit", type="primary"):

        if not city.strip():
            st.warning("Please enter a city.")

        else:
            try:
                location = get_coordinates(city)

                if location is None:
                    st.error("City not found.")

                else:
                    lat, lon, matched_name = location

                    current = fetch_weather(lat, lon)

                    temperature = current["temperature_2m"]
                    precipitation = current["precipitation"]
                    wind_speed = current["wind_speed_10m"]
                    is_day = current["is_day"]

                    is_raining = precipitation > 0
                    wind_level = wind_speed_to_level(wind_speed)
                    is_sunny = bool(is_day) and precipitation == 0

                    st.subheader(f"🌎 Weather in {matched_name}")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Temperature", f"{temperature}°F")
                        st.metric("Wind Speed", f"{wind_speed} mph")

                    with col2:
                        st.metric(
                            "Rain",
                            "Yes" if is_raining else "No"
                        )
                        st.metric(
                            "Sunny",
                            "Yes" if is_sunny else "No"
                        )

                    outfit, reasons = get_outfit_recommendation(
                        temperature,
                        is_raining,
                        wind_level,
                        is_sunny
                    )

                    display_outfit(outfit, reasons)

            except (
                urllib.error.URLError,
                TimeoutError,
                json.JSONDecodeError
            ) as e:
                st.error(f"Weather service error: {e}")
