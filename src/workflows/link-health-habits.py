import os
from notion_client import Client

def main():
    notion_token = os.getenv("NOTION_TOKEN")
    steps_db_id = os.getenv("NOTION_STEPS_DB_ID")
    health_db_id = os.getenv("NOTION_HEALTH_DB_ID")

    client = Client(auth=notion_token)

    print("Reading Daily Steps entries...")
    steps_pages = []
    cursor = None
    while True:
        response = client.databases.query(
            database_id=steps_db_id,
            start_cursor=cursor
        )
        steps_pages.extend(response["results"])
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    # Build a map: date -> steps page id
    date_to_steps_page = {}
    for page in steps_pages:
        date_prop = page["properties"].get("Date", {}).get("date")
        if date_prop and date_prop.get("start"):
            date_str = date_prop["start"][:10]
            date_to_steps_page[date_str] = page["id"]

    print(f"Found {len(date_to_steps_page)} days of steps data.")

    print("Reading Salud y Habitos entries...")
    health_pages = []
    cursor = None
    while True:
        response = client.databases.query(
            database_id=health_db_id,
            start_cursor=cursor
        )
        health_pages.extend(response["results"])
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    linked_count = 0
    for page in health_pages:
        date_prop = page["properties"].get("Fecha", {}).get("date")
        if not date_prop or not date_prop.get("start"):
            continue
        date_str = date_prop["start"][:10]

        if date_str in date_to_steps_page:
            existing_relation = page["properties"].get("Pasos", {}).get("relation", [])
            existing_ids = [r["id"] for r in existing_relation]
            target_id = date_to_steps_page[date_str]

            if target_id not in existing_ids:
                client.pages.update(
                    page_id=page["id"],
                    properties={
                        "Pasos": {
                            "relation": [{"id": target_id}]
                        }
                    }
                )
                linked_count += 1
                print(f"Linked {date_str}")

    print(f"Done. Linked {linked_count} new days.")

if __name__ == "__main__":
    main()