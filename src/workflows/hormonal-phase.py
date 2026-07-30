from datetime import datetime

from dotenv import load_dotenv

from src.helpers import get_garmin_client, get_notion_client

PHASE_MENSTRUAL = "🩸 Menstrual (Días 1-5)"
PHASE_FOLICULAR = "🌱 Folicular (Días 6-12)"
PHASE_OVULATORIA = "🔥 Ovulatoria (Días 13-16)"
PHASE_LUTEA = "📉 Lútea (Días 17-28)"


def get_menstrual_data(garmin):
    today = datetime.today().date()
    return garmin.get_menstrual_data_for_date(today.isoformat())


def phase_for_cycle_day(cycle_day):
    if cycle_day is None:
        return None
    if cycle_day <= 5:
        return PHASE_MENSTRUAL
    if cycle_day <= 12:
        return PHASE_FOLICULAR
    if cycle_day <= 16:
        return PHASE_OVULATORIA
    return PHASE_LUTEA


def find_today_row(client, database_id, today_iso):
    query = client.databases.query(
        database_id=database_id,
        filter={"property": "Fecha", "date": {"equals": today_iso}}
    )
    results = query.get('results', [])
    return results[0] if results else None


def update_hormonal_field(client, page_id, phase):
    client.pages.update(page_id=page_id, properties={"Hormonal": {"select": {"name": phase}}})


def main():
    load_dotenv()

    garmin_client, _ = get_garmin_client()
    notion_client, notion_dbs = get_notion_client()

    database_id = notion_dbs.health_habits

    data = get_menstrual_data(garmin_client)
    print(f"Raw Garmin menstrual data: {data}")

    cycle_day = (data or {}).get('daySummary', {}).get('dayInCycle')
    phase = phase_for_cycle_day(cycle_day)

    if phase is None:
        print("No active cycle day reported by Garmin for today; skipping 'Hormonal' update")
        return

    today_iso = datetime.today().date().isoformat()
    row = find_today_row(notion_client, database_id, today_iso)

    if not row:
        print(f"No row found in 'Salud y Hábitos' for {today_iso}; skipping 'Hormonal' update")
        return

    update_hormonal_field(notion_client, row['id'], phase)
    print(f"Updated 'Hormonal' to '{phase}' for {today_iso}")


if __name__ == '__main__':
    main()
