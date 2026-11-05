"""
Outfit Picker - Streamlit interface
CIS 245 Course Project - Group 5

Run with:  python -m streamlit run app.py   (Windows: py -m streamlit run app.py)
All outfit decisions come from core.py; downloads and ntfy come from online.py.
This file only draws the screen and passes values between them.
"""

import os
from datetime import date, time

import streamlit as st

from core import (
    DATA_FILES,
    DAY_TIMES,
    SCHEDULE,
    build_day_plan,
    build_message,
    failure_message,
    format_date,
    load_json,
    location_label,
    manual_times,
    save_json,
    time_to_minutes,
)
from online import WEB_ERRORS, find_city, get_forecast, send_ntfy

HERE = os.path.dirname(os.path.abspath(__file__))


def data_path(name):
    return os.path.join(HERE, DATA_FILES[name])


def show_plan(city, date_text, plan):
    """Draw a day plan: the three times side by side, then what to bring."""
    st.subheader(city)
    st.caption(f"{date_text}  |  High {plan['high']}°F, low {plan['low']}°F")

    columns = st.columns(len(plan["parts"]))
    for index in range(len(plan["parts"])):
        part = plan["parts"][index]
        with columns[index]:
            with st.container(border=True):
                st.markdown(f"**{part['label']}** ({part['hour_text']})")
                st.markdown(f"## {part['temp']}°F")
                if index == 0:
                    st.write("Wear: " + ", ".join(part["layers"]))
                else:
                    st.write(part["change"].capitalize())
                if part["rain"]:
                    st.caption("Rain likely")
                if part["windy"]:
                    st.caption("Windy")

    all_day = [plan["bottoms"], plan["shoes"]] + plan["accessories"]
    st.write("**All day:** " + ", ".join(all_day))
    for warning in plan["warnings"]:
        st.warning(warning)
    if plan["bring"]:
        st.info("**Bring with you:** " + ", ".join(plan["bring"]))
    with st.expander("Why this outfit"):
        for reason in plan["reasons"]:
            st.write(reason)


def lookup_plan(city_text):
    """Find the city and today's forecast. Returns (label, date text, plan) or an error string."""
    try:
        location = find_city(city_text)
        if location is None:
            return "Couldn't find that city. Try the city and state, like New Haven, CT."
        forecast = get_forecast(location)
    except WEB_ERRORS as error:
        return f"The weather service didn't answer ({error}). Try again in a minute."
    plan = build_day_plan(forecast["times"], forecast["high"], forecast["low"])
    return location_label(location), format_date(forecast["date"]), plan


st.set_page_config(page_title="Outfit Picker", page_icon="👕", layout="centered")
st.title("Outfit Picker")

outfit_tab, message_tab = st.tabs(["Today's outfit", "Morning message"])

# ---------------------------------------------------------------------------
# TAB 1: TODAY'S OUTFIT
# ---------------------------------------------------------------------------

with outfit_tab:
    mode = st.radio(
        "Weather",
        ["Look up my city", "Type it in myself"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if mode == "Look up my city":
        city_text = st.text_input("City", placeholder="New Haven, CT")
        if st.button("What do I wear?", type="primary"):
            if not city_text.strip():
                st.warning("Enter a city first.")
            else:
                st.session_state["result"] = lookup_plan(city_text)

    else:
        temp_columns = st.columns(len(DAY_TIMES))
        temps = []
        for index in range(len(DAY_TIMES)):
            with temp_columns[index]:
                temps.append(st.number_input(
                    f"{DAY_TIMES[index]['hour_text']} (°F)",
                    value=60.0,
                    step=1.0,
                    key=f"temp_{index}",
                ))
        rain_labels = st.multiselect(
            "When will it rain?", [spec["label"] for spec in DAY_TIMES]
        )
        wind_level = st.selectbox(
            "Wind",
            ["low", "medium", "high"],
            format_func=lambda level: {"low": "Calm", "medium": "Breezy", "high": "Windy"}[level],
        )
        sunny = st.checkbox("Clear skies")
        if st.button("What do I wear?", type="primary"):
            times = manual_times(temps, rain_labels, wind_level, sunny)
            temps_rounded = [spot["temp"] for spot in times]
            plan = build_day_plan(times, max(temps_rounded), min(temps_rounded))
            st.session_state["result"] = ("Your weather", format_date(date.today().isoformat()), plan)

    result = st.session_state.get("result")
    if isinstance(result, str):
        st.error(result)
    elif result is not None:
        show_plan(*result)

# ---------------------------------------------------------------------------
# TAB 2: MORNING MESSAGE SETTINGS AND "SEND IT NOW"
# ---------------------------------------------------------------------------

with message_tab:
    profiles = load_json(data_path("profiles"), {})
    new_person = "Add a new person"
    choice = st.selectbox("Who is this for?", list(profiles.keys()) + [new_person])

    if choice == new_person:
        name = st.text_input("Your name").strip()
        profile = {}
    else:
        name = choice
        profile = profiles[choice]

    city_text = st.text_input("City", value=profile.get("city", ""), placeholder="New Haven, CT")
    send_minutes = time_to_minutes(profile.get("send_time", SCHEDULE["default_send_time"]))
    send_clock = st.time_input(
        "Send time",
        value=time(send_minutes // 60, send_minutes % 60),
        step=900,
    )

    if st.button("Save settings", type="primary"):
        if not name or not city_text.strip():
            st.warning("Enter a name and a city.")
        else:
            try:
                location = find_city(city_text)
            except WEB_ERRORS as error:
                location = None
                st.error(f"The weather service didn't answer ({error}). Try again in a minute.")
            else:
                if location is None:
                    st.error("Couldn't find that city. Try the city and state, like New Haven, CT.")
            if location is not None:
                profiles[name] = {
                    "city": location_label(location),
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "timezone": location["timezone"],
                    "send_time": send_clock.strftime("%H:%M"),
                    "topic_env": profile.get("topic_env", "NTFY_TOPIC_" + name.upper().replace(" ", "_")),
                }
                save_json(data_path("profiles"), profiles)
                st.success(
                    f"Saved: {profiles[name]['city']} at {profiles[name]['send_time']}. "
                    "Commit and push data/profiles.json so the morning job uses it."
                )

    st.divider()
    st.markdown("**Test it**")
    st.caption("Your ntfy topic is only used for this send and isn't saved.")
    topic = st.text_input("ntfy topic", type="password", key="ntfy_topic")
    if st.button("Send it now"):
        if choice == new_person or not topic:
            st.warning("Save your settings and enter your ntfy topic first.")
        else:
            try:
                forecast = get_forecast(profile)
                plan = build_day_plan(forecast["times"], forecast["high"], forecast["low"])
                message = build_message(profile["city"], format_date(forecast["date"]), plan)
            except WEB_ERRORS:
                message = failure_message(profile["city"])
            try:
                send_ntfy(topic, message)
                st.success("Sent. Check your phone.")
            except WEB_ERRORS as error:
                st.error(f"Couldn't reach ntfy ({error}).")
            st.code(message, language=None)
