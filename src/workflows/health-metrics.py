from datetime import datetime

from dotenv import load_dotenv

from src.helpers import get_garmin_client, get_notion_client


def safe_call(label, fn, *args):
    """Garmin can return nothing (or fail) for a metric that isn't ready yet; never crash the whole run."""
    try:
        return fn(*args)
    except Exception as e:
        print(f"Could not fetch {label}: {e}")
        return None


def extract_hrv(hrv_data):
    """Overnight average HRV (ms)."""
    if not hrv_data:
        return None
    value = (hrv_data.get('hrvSummary') or {}).get('lastNightAvg')
    return round(value) if value else None


def extract_sleep_score(sleep_data):
    if not sleep_data:
        return None
    scores = (sleep_data.get('dailySleepDTO') or {}).get('sleepScores') or {}
    value = (scores.get('overall') or {}).get('value')
    return round(value) if value else None


def extract_stress(stress_data):
    """Average stress level of the day so far."""
    if not stress_data:
        return None
    value = stress_data.get('avgStressLevel')
    # Garmin uses negative numbers when there is not enough data
    return round(value) if value and value > 0 else None


def extract_body_battery(battery_data):
    """Highest Body Battery level so far today (the 'charged on waking' value)."""
    levels = []
    for day in battery_data or []:
        for point in day.get('bodyBatteryValuesArray') or []:
            if len(point) > 1 and point[1] is not None:
                levels.append(point[1])
    return round(max(levels)) if levels else None


def find_health_habits_row(client, database_id, date_iso):
    query = client.databases.query(
        database_id=database_id,
        filter={"property": "Fecha", "date": {"equals": date_iso}}
    )
    results = query.get('results', [])
    return results[0] if results else None


def main():
    load_dotenv()

    garmin_client, _ = get_garmin_client()
    notion_client, notion_dbs = get_notion_client()

    today_iso = datetime.today().date().isoformat()

    metrics = {
        "HRV (ms)": extract_hrv(safe_call("HRV", garmin_client.get_hrv_data, today_iso)),
        "Sleep Score": extract_sleep_score(safe_call("sleep score", garmin_client.get_sleep_data, today_iso)),
        "Estrés": extract_stress(safe_call("stress", garmin_client.get_stress_data, today_iso)),
        "Body Battery": extract_body_battery(safe_call("body battery", garmin_client.get_body_battery, today_iso, today_iso)),
    }

    # Only write what Garmin actually returned, so a 6 AM run with partial data never blanks out anything
    properties = {name: {"number": value} for name, value in metrics.items() if value is not None}
    if not properties:
        print(f"No health metrics available yet for {today_iso}; nothing to update.")
        return

    row = find_health_habits_row(notion_client, notion_dbs.health_habits, today_iso)
    if not row:
        print(f"No row found in 'Salud y Hábitos' for {today_iso}; skipping.")
        return

    notion_client.pages.update(page_id=row['id'], properties=properties)
    print(f"Updated {', '.join(properties)} for {today_iso}")


if __name__ == '__main__':
    main()
