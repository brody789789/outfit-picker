# Outfit Picker

## What it does now
Outfit Picker is a CIS 245 Group 5 Python project that recommends clothing for the whole day based on weather. The Streamlit app (`app.py`) looks up a city's forecast for 8 AM, noon, and 6 PM (or lets you type the weather in), then shows what to wear in the morning, which layers to take off or put on later, what to wear all day, and a "bring with you" list. A GitHub Actions job (`morning_notification.py`) sends the same plan to each person's phone through ntfy at the time they pick. It does not yet pick from a saved wardrobe.

## How to run it
1. Install Python 3.14 and open the project folder in VS Code.
2. Open the VS Code terminal in the project folder (the one containing `app.py`).
3. Install the one package once: `py -m pip install -r requirements.txt` on Windows, or `python3 -m pip install -r requirements.txt` on a Mac.
4. Start the app: `py -m streamlit run app.py` on Windows, or `python3 -m streamlit run app.py` on a Mac. The first time, it asks for an email; leave it blank and press Enter. The app opens in your browser.
5. Run the tests: `py test_core.py` (or `python3 test_core.py`). No output means every test passed. The tests do not use the internet. They only write `data/test_scratch.json`, never the real data files.
6. Morning messages: see "Setting up the morning message" below.

## Files: what each one does, and which part it belongs to
- `core.py` — core. All rules and decisions: the temperature table, rain and wind rules, the day plan, the morning message text, the send-time check, and reading/writing our JSON files. No `print()`, `input()`, web requests, or interface code.
- `app.py` — interface. The Streamlit app: "Today's outfit" tab and "Morning message" tab (settings and the "Send it now" button).
- `online.py` — interface. Everything that uses the internet: Open-Meteo city lookup and forecast (10-second wait, retries), and sending to ntfy. Used by both `app.py` and `morning_notification.py`.
- `morning_notification.py` — interface. The script GitHub Actions runs. `--now` sends to everyone immediately for testing.
- `test_core.py` — plain `assert` tests for every function in `core.py`.
- `data/profiles.json` — each person's city, coordinates, time zone, send time, and the name of their ntfy secret. Edited by the app's "Morning message" tab.
- `data/sent_log.json` — the date each person was last messaged, so nobody gets two messages a day. Updated by the GitHub job.
- `data/sample_forecast.json` — a forecast in Open-Meteo's exact format, used by the tests. It matches our 45/68/55 example; it is not a real download. Replace it with a real saved response when convenient and update the three tests that check its values. [CHECK]
- `.github/workflows/morning_outfit.yml` — the GitHub Actions schedule.
- `.streamlit/config.toml` — the app's accent color.
- `.gitignore` — keeps `__pycache__` and the test scratch file out of GitHub.
- `requirements.txt` — packages to install, one per line.
- `CIS 245 Course Project.docx`, `Team Charter.docx`, Part 2 PDF — course documents, not code.

## Packages
- `streamlit` — the interface. It is the only package to install.
- Standard library (comes with Python): `json`, `os`, `sys`, `time`, `datetime`, `zoneinfo`, `urllib.error`, `urllib.parse`, `urllib.request`.
- Do not install a new package until the group agrees on it and records it here.

## The rules (Feature A)
Layers stack. The first row the temperature reaches is used.

| Temperature | Layers |
|---|---|
| 70°F and up | t-shirt |
| 60–69°F | t-shirt, sweatshirt |
| 50–59°F | t-shirt, sweatshirt, light jacket |
| below 50°F | t-shirt, sweatshirt, heavy coat |

- **Wind:** under 15 mph is calm, 15–19 mph is breezy (no change), 20 mph and up is windy and moves you one row colder. These match the National Weather Service's "breezy" and "windy" definitions.
- **Rain:** a 50% or higher chance of rain counts as rain. Rain at any time means sneakers instead of slides and an umbrella in the bring list. If it is dry at 8 AM but rain is likely later, the plan warns you to bring an umbrella or rain jacket. Rain does not add warm layers.
- **75°F and raining:** t-shirt, shorts, sneakers, umbrella.
- **Bottoms:** shorts if the coldest of the three times is 65°F or higher, otherwise pants (polls most often put "shorts weather" in the 60s).
- **Shoes:** slides only if the coldest time is 70°F or higher and no rain is likely; otherwise sneakers.
- **Sunglasses:** if any daytime hour is clear and dry.
- All of these numbers live in `TEMPERATURE_TABLE` and `WEATHER_RULES` at the top of `core.py`, so changing a rule means changing one number.

## The day plan (Feature D)
The plan uses 8 AM (Morning), noon (Afternoon), and 6 PM (Evening). The morning line lists every layer; later lines say what to take off or put on. Anything worn at some times but not all goes in the bring list. Example (45°F, 68°F, 55°F): morning t-shirt, sweatshirt, heavy coat; afternoon take off the heavy coat; evening put on a light jacket; bring heavy coat and light jacket.

## Setting up the morning message (Feature H)
1. Each person installs the ntfy app and subscribes to a topic name nobody would guess.
2. In GitHub: Settings → Secrets and variables → Actions → New repository secret. Ben's secret is `NTFY_TOPIC` (already in use). Others use `NTFY_TOPIC_JARIANA`, `NTFY_TOPIC_MARLEY`, `NTFY_TOPIC_CODY`. A new name needs a matching line in the workflow's `env:` section.
3. In the app's "Morning message" tab, pick your name (or add yourself), enter your city and send time, and click Save settings. Then commit and push `data/profiles.json`, because GitHub reads the copy in the repo, not the one on your laptop.
4. Use "Send it now" in the app to test with your topic, or in GitHub: Actions → Morning outfit → Run workflow, with "Send to everyone right now" checked.

How it runs: GitHub runs the job every 15 minutes from about 5 AM to noon Eastern. Each run sends to anyone whose send time has passed (within 3 hours) and who hasn't been messaged today, then commits `data/sent_log.json` so they aren't messaged twice. If the forecast doesn't answer within 10 seconds, it tries 3 more times, 5 minutes apart. If all 4 tries fail, it sends "Couldn't get today's forecast for (city). Check the weather before you head out." It never sends a guessed outfit. GitHub can start scheduled runs late, especially at the top of the hour, so messages may arrive up to about 15 minutes after the chosen time. Send times outside 5 AM–noon Eastern will not be picked up unless the workflow's hours change.

## Current status: what works, what is next
**Present in the code:** Streamlit app with city lookup and typed-in weather, Feature A rules, Feature D day plan, Feature H message with retries and failure message, user-picked send times, "Send it now", GitHub Actions workflow, and core tests. Tested offline only: the live city lookup, live forecast, ntfy sending, and the GitHub workflow have not been run against the real services yet. [CHECK]

**Next:**
1. Run the app's city lookup and "Send it now" on a real laptop, and run the workflow once with "Run workflow". [CHECK]
2. Save a real Open-Meteo response as `data/sample_forecast.json`.
3. Wardrobe (Feature B): saved items with type, warmth level, and waterproof flag; pick owned items; name a similar replacement when something isn't owned.
4. Test and document operation on each teammate's laptop and the GitHub workflow.

**Other committed features to plan:** daily activities (class/gym/work/interview), laundry and repeat avoidance, seven-day outfits with a laundry day, and personal temperature preferences.

## Who owns what (from Part 2, section 5c)
- Jariana (Member 1) — Feature A rules: `table_row_for_temp`, `wind_speed_to_level`, `layers_for_temp`, `will_rain`, `pick_bottoms`, `pick_shoes`, `pick_accessories`, `manual_times`; typed-in weather entry in the app.
- Marley (Member 2) — Feature B wardrobe (not started); wardrobe page.
- Cody (Member 3) — Feature D day splitter: `join_items`, `describe_change`, `bring_list`, `build_day_plan`; the three-column day view.
- Ben (Member 4) — Feature H: `normalize_city`, `geocoding_params`, `read_location`, `location_label`, `forecast_params`, `parse_forecast`, `format_date`, `build_message`, `failure_message`, `time_to_minutes`, `is_due`, `load_json`, `save_json`; `online.py`, `morning_notification.py`, the workflow, send-time setting, and "Send it now".

Owner comments sit above each function in `core.py`. Each owner should be able to explain their functions line by line.

## Decisions
- Course: CIS 245: Applied Python With AI Tools; four-person group; Python 3.14 and VS Code on individual laptops.
- Code check-in: November 11, 2026. Final project due December 2, 2026.
- Interface: Streamlit. Weather: Open-Meteo. Phone messages: ntfy, run by GitHub Actions.
- Core contains decision logic and may read/write files; interface owns input/output, web requests, and user-visible messages.
- Rule numbers come from popular opinion online (polls and National Weather Service definitions); the group can change any of them in `core.py`.
- City lookup accepts "New Haven, CT", "New Haven CT", and "New Haven Connecticut".
- Each person's time zone comes from the city lookup and is saved in `data/profiles.json`.
- ntfy topics are never saved in the code or data files; they live in GitHub secrets, and the app asks for one only when testing.

## Change log
- 2026-10-28 — Created initial README from the uploaded Python file and updated team instructions; documented what exists, revised MVP, team ownership, and open decisions. No program code changed.
- 2026-11-04 — Split `outfit_picker.py` and `streamlit_app.py` into `core.py`, `app.py`, and `test_core.py`; `morning_notification.py` now imports from `core.py`; added `requirements.txt`. Outfit rules unchanged. Removed the old terminal menu (Streamlit is the final interface).
- 2026-11-04 — Added Feature A rules, Feature D day plan, Feature H message format with retries and failure message, user-picked send times with `data/profiles.json` and `data/sent_log.json`, city input without a comma, `online.py`, the GitHub Actions workflow, and a cleaner app layout with two tabs. Replaced `get_outfit_recommendation` and the earlier weather helpers.
