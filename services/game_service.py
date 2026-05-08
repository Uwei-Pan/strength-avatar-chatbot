import json
from typing import Any

from database.db_connection import execute
from services.token_service import (
    GAME_SCORE_REWARD,
    GAME_START_COST,
    award_game_score_tokens,
    spend_game_start_tokens,
)


SCORE_REWARD_THRESHOLD = 30


def start_game(child_id: str) -> dict[str, Any]:
    new_balance = spend_game_start_tokens(child_id)
    return {
        "tokens_spent": GAME_START_COST,
        "new_balance": new_balance,
    }


def finish_game(child_id: str, score: int, fruits_eaten: list[dict[str, Any]]) -> dict[str, Any]:
    tokens_earned = 0
    new_balance = None
    if score >= SCORE_REWARD_THRESHOLD:
        tokens_earned = GAME_SCORE_REWARD
        new_balance = award_game_score_tokens(child_id)

    execute(
        """
        INSERT INTO game_sessions
            (child_id, score, tokens_spent, tokens_earned, fruits_eaten_json)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            child_id,
            score,
            GAME_START_COST,
            tokens_earned,
            json.dumps(fruits_eaten, ensure_ascii=False),
        ),
    )
    return {
        "score": score,
        "tokens_spent": GAME_START_COST,
        "tokens_earned": tokens_earned,
        "new_balance": new_balance,
    }
