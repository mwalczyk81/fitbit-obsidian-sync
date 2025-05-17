import datetime
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from fitbit import Fitbit

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
VAULT_DIR = os.getenv("VAULT_DIR", "vault")
TOKEN_FILE = "fitbit_tokens.json"
DATE_FORMAT = "%Y-%m-%d"


def refresh_tokens(client_id, client_secret, refresh_token):
    response = requests.post(
        "https://api.fitbit.com/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        },
        auth=(client_id, client_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    new_tokens = response.json()
    new_tokens["expires_at"] = int(time.time()) + new_tokens["expires_in"]
    return new_tokens


def get_client():
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(f"{TOKEN_FILE} not found. Generate your tokens first.")
    with open(TOKEN_FILE) as f:
        try:
            tokens = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(
                f"{TOKEN_FILE} is invalid or empty. Please regenerate your tokens."
            )

    if "expires_at" not in tokens:
        tokens["expires_at"] = int(time.time()) + int(tokens.get("expires_in", 0))

    if tokens["expires_at"] < int(time.time()):
        tokens = refresh_tokens(CLIENT_ID, CLIENT_SECRET, tokens["refresh_token"])
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f)

    return Fitbit(
        CLIENT_ID,
        CLIENT_SECRET,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_at=tokens["expires_at"],
        refresh_cb=lambda new_t: json.dump(new_t, open(TOKEN_FILE, "w")),
    )


def fetch_data(fitbit_client, date_str):
    summary = fitbit_client.activities(date=date_str)["summary"]

    sleep_data = fitbit_client.sleep(date=date_str).get("sleep", [])
    sleep_minutes = sleep_data[0]["minutesAsleep"] if sleep_data else 0
    sleep_hours = sleep_minutes / 60

    # Get today's weight if available
    weight_data = fitbit_client.body(date=date_str).get("weight", [])
    if weight_data:
        weight = weight_data[0]["weight"]
    else:
        # If none for today, fetch most recent weight from the last 30 days
        weight_range = fitbit_client.get_bodyweight(
            base_date=date_str, period="1m"
        ).get("weight", [])
        weight = weight_range[-1]["weight"] if weight_range else None

    # ✅ Correct way to get workouts
    activities = fitbit_client.make_request(
        f"https://api.fitbit.com/1/user/-/activities/date/{date_str}.json"
    ).get("activities", [])

    workout_summary = []
    total_workout_minutes = 0
    for activity in activities:
        workout_summary.append(activity["name"])
        total_workout_minutes += activity.get("duration", 0) // 60000

    return {
        "steps": summary.get("steps", 0),
        "calories": summary.get("caloriesOut", 0),
        "sleep_hours": sleep_hours,
        "weight": weight,
        "workouts": workout_summary,
        "workout_minutes": total_workout_minutes,
    }


def write_to_obsidian(
    date_str, steps, calories, sleep_hours, weight, workouts, workout_minutes
):
    filename = f"{date_str}.md"
    daily_note_path = Path(VAULT_DIR) / "01 - Daily Notes" / filename
    daily_note_path.parent.mkdir(parents=True, exist_ok=True)

    iso_week = datetime.datetime.strptime(date_str, DATE_FORMAT).isocalendar()[1]

    properties_block = f"""---
type: daily-note
tags: [journal, daily, health]
date: {date_str}
week: {iso_week}
---
"""

    workout_str = ", ".join(workouts) if workouts else "None"
    weight_str = f"{weight}" if weight else "N/A"

    fitbit_block = f"""## 🧠 Health Summary
Weight:: {weight_str}  
Workout:: {workout_str} ({workout_minutes} min)  
Sleep:: {sleep_hours:.2f} hrs  
Steps:: {steps:,}  
Calories Burned:: {calories:,}  
"""

    default_body = """## ✅ Tasks
- [ ] Main priority  
- [ ] Secondary task  

## 📝 Notes
"""

    if daily_note_path.exists():
        with open(daily_note_path, "r+", encoding="utf-8") as f:
            content = f.read()
            if "## 🧠 Health Summary" in content:
                parts = content.split("## 🧠 Health Summary")
                before = parts[0]
                after = parts[1]
                updated = f"{before}{fitbit_block}{after}"
            else:
                updated = f"{content.rstrip()}\n\n{fitbit_block}"
            f.seek(0)
            f.write(updated)
            f.truncate()
    else:
        with open(daily_note_path, "w", encoding="utf-8") as f:
            f.write(f"{properties_block}\n{fitbit_block}{default_body}")


def run_daily_sync():
    today = datetime.date.today().strftime(DATE_FORMAT)
    fb = get_client()
    data = fetch_data(fb, today)
    write_to_obsidian(today, **data)
