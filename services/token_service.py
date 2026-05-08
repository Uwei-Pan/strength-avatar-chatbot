from database.db_connection import fetch_one, get_connection


CHAT_REWARD = 10
GAME_START_COST = 5
GAME_SCORE_REWARD = 10
DIARY_REWARD = 10
TODO_COMPLETED_REWARD = 10


class InsufficientTokensError(ValueError):
    pass


def get_balance(child_id: str) -> int:
    row = fetch_one("SELECT tokens FROM children WHERE child_id = %s", (child_id,))
    if not row:
        raise ValueError("找不到 child，無法取得 token 餘額。")
    return int(row["tokens"])


def add_tokens(child_id: str, amount: int, reason: str) -> int:
    if amount <= 0:
        raise ValueError("add_tokens amount 必須大於 0。")
    return _change_tokens(child_id, amount, reason)


def spend_tokens(child_id: str, amount: int, reason: str) -> int:
    if amount <= 0:
        raise ValueError("spend_tokens amount 必須大於 0。")
    return _change_tokens(child_id, -amount, reason)


def _change_tokens(child_id: str, amount: int, reason: str) -> int:
    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT tokens FROM children WHERE child_id = %s FOR UPDATE",
                    (child_id,),
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError("找不到 child，無法異動 token。")
                new_balance = int(row["tokens"]) + amount
                if new_balance < 0:
                    raise InsufficientTokensError("代幣不足，不能進行這個操作。")

                cursor.execute(
                    "UPDATE children SET tokens = %s WHERE child_id = %s",
                    (new_balance, child_id),
                )
                cursor.execute(
                    """
                    INSERT INTO token_transactions (child_id, amount, reason)
                    VALUES (%s, %s, %s)
                    """,
                    (child_id, amount, reason),
                )
            conn.commit()
            return new_balance
        except Exception:
            conn.rollback()
            raise


def award_chat_tokens(child_id: str) -> int:
    return add_tokens(child_id, CHAT_REWARD, "chat_reward")


def spend_game_start_tokens(child_id: str) -> int:
    return spend_tokens(child_id, GAME_START_COST, "game_start_cost")


def award_game_score_tokens(child_id: str) -> int:
    return add_tokens(child_id, GAME_SCORE_REWARD, "game_score_reward")


def award_diary_tokens(child_id: str) -> int:
    return add_tokens(child_id, DIARY_REWARD, "diary_reward")


def award_todo_completed_tokens(child_id: str, amount: int = TODO_COMPLETED_REWARD) -> int:
    return add_tokens(child_id, amount, "todo_completed_reward")
