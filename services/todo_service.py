from datetime import date
from typing import Any

from database.db_connection import execute, fetch_all, fetch_one, get_connection
from services.token_service import award_todo_completed_tokens


def create_todo(
    child_id: str,
    title: str,
    description: str = "",
    due_date: date | None = None,
    tokens_reward: int = 10,
) -> None:
    execute(
        """
        INSERT INTO todo_items
            (child_id, title, description, due_date, tokens_reward)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (child_id, title.strip(), description.strip() or None, due_date, tokens_reward),
    )


def list_todos(child_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, title, description, is_completed, tokens_reward,
               due_date, created_at, completed_at
        FROM todo_items
        WHERE child_id = %s
        ORDER BY is_completed ASC, due_date IS NULL ASC, due_date ASC, created_at DESC
        """,
        (child_id,),
    )


def complete_todo(child_id: str, todo_id: int) -> int:
    todo = fetch_one(
        """
        SELECT id, tokens_reward, is_completed
        FROM todo_items
        WHERE id = %s AND child_id = %s
        """,
        (todo_id, child_id),
    )
    if not todo:
        raise ValueError("找不到這個 Todo。")
    if todo["is_completed"]:
        raise ValueError("這個 Todo 已經完成過了。")

    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE todo_items
                    SET is_completed = TRUE, completed_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND child_id = %s AND is_completed = FALSE
                    """,
                    (todo_id, child_id),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    reward = int(todo["tokens_reward"] or 10)
    award_todo_completed_tokens(child_id, reward)
    return reward
