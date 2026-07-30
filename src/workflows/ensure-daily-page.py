from datetime import datetime

from dotenv import load_dotenv

from src.helpers import get_notion_client


def find_today_row(client, database_id, today_iso):
    query = client.databases.query(
        database_id=database_id,
        filter={"property": "Fecha", "date": {"equals": today_iso}}
    )
    results = query.get('results', [])
    return results[0] if results else None


def create_today_row(client, database_id, today_iso):
    properties = {
        "Día": {"title": [{"text": {"content": today_iso}}]},
        "Fecha": {"date": {"start": today_iso}},
    }
    client.pages.create(parent={"database_id": database_id}, properties=properties)


def main():
    load_dotenv()

    notion_client, notion_dbs = get_notion_client()
    database_id = notion_dbs.health_habits

    today_iso = datetime.today().date().isoformat()

    if find_today_row(notion_client, database_id, today_iso):
        print(f"Row for {today_iso} already exists in 'Salud y Hábitos'; skipping.")
        return

    create_today_row(notion_client, database_id, today_iso)
    print(f"Created row for {today_iso} in 'Salud y Hábitos'.")


if __name__ == '__main__':
    main()
