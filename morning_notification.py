"""
Outfit Picker - morning phone notification
CIS 245 Course Project - Group 5

GitHub Actions runs this every 15 minutes during morning hours. For each
person in data/profiles.json whose send time has come (and who hasn't been
messaged today), it gets the forecast, builds the message with core.py,
and sends it through ntfy.

    python morning_notification.py        send to whoever is due
    python morning_notification.py --now  send to everyone right now (testing)
"""

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from core import (
    DATA_FILES,
    build_day_plan,
    build_message,
    failure_message,
    format_date,
    is_due,
    load_json,
    save_json,
)
from online import WEB_ERRORS, get_forecast_with_retries, send_ntfy

HERE = os.path.dirname(os.path.abspath(__file__))


def data_path(name):
    return os.path.join(HERE, DATA_FILES[name])


def message_for(profile):
    """Get the forecast (with retries) and return the text to send."""
    forecast = get_forecast_with_retries(profile)
    if forecast is None:
        return failure_message(profile["city"])
    plan = build_day_plan(forecast["times"], forecast["high"], forecast["low"])
    return build_message(profile["city"], format_date(forecast["date"]), plan)


def run(send_everyone_now):
    profiles = load_json(data_path("profiles"), {})
    sent_log = load_json(data_path("sent_log"), {})

    for name, profile in profiles.items():
        topic = os.environ.get(profile["topic_env"], "")
        if not topic:
            print(f"{name}: no {profile['topic_env']} secret set, skipping.")
            continue

        now = datetime.now(ZoneInfo(profile["timezone"]))
        today = now.date().isoformat()
        if not send_everyone_now and not is_due(
            now.strftime("%H:%M"), profile["send_time"], today, sent_log.get(name, "")
        ):
            print(f"{name}: not due (send time {profile['send_time']}, now {now:%H:%M}).")
            continue

        message = message_for(profile)
        try:
            status = send_ntfy(topic, message)
        except WEB_ERRORS as error:
            print(f"{name}: couldn't reach ntfy ({error}); will try again next run.")
            continue
        print(f"{name}: sent (ntfy status {status}).")

        if not send_everyone_now:
            sent_log[name] = today
            save_json(data_path("sent_log"), sent_log)


if __name__ == "__main__":
    run("--now" in sys.argv)
