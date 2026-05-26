import json
import uuid
from typing import Any

from database.db_connection import execute, get_connection
from services.token_service import (
    GAME_START_COST,
    spend_game_start_tokens,
)


SNAKE_TOKEN_THRESHOLD = 100
BLOCK_TOKEN_THRESHOLD = 150
MAX_GAME_TOKENS_PER_ROUND = 5


def start_game(child_id: str) -> dict[str, Any]:
    new_balance = spend_game_start_tokens(child_id)
    return {
        "tokens_spent": GAME_START_COST,
        "new_balance": new_balance,
    }


def new_game_id() -> str:
    return uuid.uuid4().hex[:12]


def finish_game(
    child_id: str,
    score: int,
    game_events: list[dict[str, Any]],
    *,
    game_type: str = "snake",
    tokens_earned: int = 0,
    game_over_reason: str = "",
    game_id: str | None = None,
    tokens_spent: int = GAME_START_COST,
) -> dict[str, Any]:
    payload = {
        "game_id": game_id,
        "game_type": game_type,
        "game_over_reason": game_over_reason,
        "events": game_events,
    }
    execute(
        """
        INSERT INTO game_sessions
            (child_id, score, tokens_spent, tokens_earned, fruits_eaten_json)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            child_id,
            score,
            int(tokens_spent),
            tokens_earned,
            json.dumps(payload, ensure_ascii=False),
        ),
    )
    return {
        "score": score,
        "tokens_spent": int(tokens_spent),
        "tokens_earned": tokens_earned,
        "new_balance": None,
    }


def award_game_token_once(
    child_id: str,
    *,
    game_type: str,
    game_id: str,
    threshold: int,
) -> dict[str, Any]:
    reason = f"game_{game_type}_{game_id}_{int(threshold)}"
    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM token_transactions
                    WHERE child_id = %s AND reason = %s
                    LIMIT 1
                    """,
                    (child_id, reason),
                )
                existing = cursor.fetchone()
                cursor.execute(
                    "SELECT tokens FROM children WHERE child_id = %s FOR UPDATE",
                    (child_id,),
                )
                child = cursor.fetchone()
                if not child:
                    raise ValueError("找不到 child，無法發放遊戲代幣。")
                current_balance = int(child["tokens"])
                if existing:
                    return {
                        "awarded": False,
                        "new_balance": current_balance,
                        "reason": reason,
                    }

                new_balance = current_balance + 1
                cursor.execute(
                    "UPDATE children SET tokens = %s WHERE child_id = %s",
                    (new_balance, child_id),
                )
                cursor.execute(
                    """
                    INSERT INTO token_transactions (child_id, amount, reason)
                    VALUES (%s, %s, %s)
                    """,
                    (child_id, 1, reason),
                )
            conn.commit()
            return {
                "awarded": True,
                "new_balance": new_balance,
                "reason": reason,
            }
        except Exception:
            conn.rollback()
            raise


def save_game_reflection(
    *,
    child_id: str,
    game_type: str,
    question: str,
    answer: str,
    score_before_game_over: int,
    game_over_reason: str,
) -> None:
    _ensure_game_reflections_table()
    execute(
        """
        INSERT INTO game_reflections
            (child_id, game_type, question, answer, score_before_game_over, game_over_reason)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            child_id,
            game_type,
            question,
            answer,
            int(score_before_game_over),
            game_over_reason,
        ),
    )


def _ensure_game_reflections_table() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS game_reflections (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            child_id VARCHAR(64) NOT NULL,
            game_type VARCHAR(40) NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            score_before_game_over INT NOT NULL DEFAULT 0,
            game_over_reason VARCHAR(80) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_game_reflections_child
                FOREIGN KEY (child_id) REFERENCES children(child_id)
                ON DELETE CASCADE,
            INDEX idx_game_reflections_child_created (child_id, created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
