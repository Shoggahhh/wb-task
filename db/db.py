import sqlite3
import json
from pathlib import Path
from typing import Any
from logger.logger import logger
import pandas as pd

from config.config import DB_NAME


def merge_data(
    card_dict: dict[str, Any], search_dict: dict[str, Any]
) -> dict[str, Any]:
    for key, value in search_dict.items():
        if (
            key in card_dict
            and isinstance(card_dict[key], dict)
            and isinstance(value, dict)
        ):
            merge_data(card_dict[key], value)
        else:
            card_dict[key] = value
    return card_dict


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS data 
        (id TEXT PRIMARY KEY, json_data TEXT)
    """
    )
    conn.commit()
    conn.close()


def load_initial_data(info_from_idx: dict[str, Any]) -> None:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    updated = 0
    inserted = 0

    for item_id, item_data in info_from_idx.items():
        cursor.execute("SELECT id FROM data WHERE id = ?", (str(item_id),))
        row = cursor.fetchone()

        if row:
            cursor.execute("SELECT json_data FROM data WHERE id = ?", (str(item_id),))
            existing_json = cursor.fetchone()[0]
            existing_data = json.loads(existing_json)

            merged_data = merge_data(existing_data, item_data)

            cursor.execute(
                """
                UPDATE data
                SET json_data = ?
                WHERE id = ?
                """,
                (json.dumps(merged_data, ensure_ascii=False), str(item_id)),
            )
            updated += 1
        else:
            cursor.execute(
                """
                INSERT INTO data (id, json_data)
                VALUES (?, ?)
                """,
                (str(item_id), json.dumps(item_data, ensure_ascii=False)),
            )
            inserted += 1

    conn.commit()
    conn.close()


def update_by_id(item_id: str, new_data: dict[str, Any]) -> None:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT json_data FROM data WHERE id = ?", (str(item_id),))
        row = cursor.fetchone()

        if row:
            existing_data = json.loads(row[0])
            merged_data = merge_data(existing_data, new_data)

            cursor.execute(
                """
                UPDATE data
                SET json_data = ?
                WHERE id = ?
                """,
                (json.dumps(merged_data, ensure_ascii=False), str(item_id)),
            )
            conn.commit()
        else:
            new_data["nm_id"] = str(item_id)
            cursor.execute(
                """
                INSERT INTO data (id, json_data)
                VALUES (?, ?)
                """,
                (str(item_id), json.dumps(new_data, ensure_ascii=False)),
            )
            conn.commit()

    except Exception as e:
        logger.error(f"Error DB for ID {item_id}: {e}")
        conn.rollback()
    finally:
        conn.close()


def export_to_excel(output_file: Path) -> None:
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, json_data FROM data", conn)
    conn.close()

    if df.empty:
        logger.info("No data for export")
        return

    df["json_data"] = df["json_data"].apply(json.loads)
    df_normalized = pd.json_normalize(df["json_data"])
    final_df = pd.concat([df[["id"]], df_normalized], axis=1)
    final_df.rename(columns={"id": "nm_id"}, inplace=True)

    final_df.to_excel(output_file, index=False)
    logger.info(f"Done! Uploaded {len(final_df)} records to {output_file}")
