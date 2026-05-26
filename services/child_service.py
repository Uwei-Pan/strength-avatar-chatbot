from typing import Any

from database.db_connection import execute, fetch_all, fetch_one
from services.strength_service import get_child_strengths


def authenticate_child(username: str, password: str) -> dict[str, Any] | None:
    child = fetch_one(
        """
        SELECT child_id, username, password_hash, name, tokens,
               selected_character, selected_outfit
        FROM children
        WHERE username = %s
        """,
        (username,),
    )
    if not child:
        return None

    # MVP: seed data uses a simple password value in password_hash.
    # The column name keeps the future migration path to real hashes clear.
    if child["password_hash"] != password:
        return None
    child.pop("password_hash", None)
    return hydrate_child(child)


def get_child(child_id: str) -> dict[str, Any] | None:
    child = fetch_one(
        """
        SELECT child_id, username, name, tokens, selected_character, selected_outfit
        FROM children
        WHERE child_id = %s
        """,
        (child_id,),
    )
    if not child:
        return None
    return hydrate_child(child)


def hydrate_child(child: dict[str, Any]) -> dict[str, Any]:
    child = dict(child)
    child["owned_strengths"] = get_child_strengths(child["child_id"])
    child["unlocked_outfits"] = get_child_outfits(child["child_id"])
    return child


def get_child_outfits(child_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            o.outfit_id,
            o.name,
            o.display_name,
            o.cost,
            co.unlocked_source,
            s.strength_id AS related_strength_id,
            s.name_zh AS strength_name,
            s.category,
            s.description AS strength_description,
            s.suggestion AS strength_suggestion
        FROM child_outfits co
        JOIN outfits o ON o.outfit_id = co.outfit_id
        LEFT JOIN strengths s ON s.strength_id = o.related_strength_id
        WHERE co.child_id = %s
        ORDER BY o.display_name
        """,
        (child_id,),
    )


def update_selected_outfit(child_id: str, outfit_id: str) -> None:
    owned = fetch_one(
        """
        SELECT 1
        FROM child_outfits
        WHERE child_id = %s AND outfit_id = %s
        """,
        (child_id, outfit_id),
    )
    if not owned:
        raise ValueError("這套服裝尚未解鎖，不能切換。")

    execute(
        "UPDATE children SET selected_outfit = %s WHERE child_id = %s",
        (outfit_id, child_id),
    )


def update_selected_character(child_id: str, character: str) -> None:
    execute(
        "UPDATE children SET selected_character = %s WHERE child_id = %s",
        (character, child_id),
    )
