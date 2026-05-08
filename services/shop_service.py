from typing import Any

from database.db_connection import fetch_all, fetch_one, get_connection
from services.token_service import InsufficientTokensError


def list_shop_outfits(child_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            o.outfit_id,
            o.name,
            o.display_name,
            o.cost,
            s.name_zh AS strength_name,
            s.category,
            CASE WHEN co.id IS NULL THEN FALSE ELSE TRUE END AS is_owned
        FROM outfits o
        LEFT JOIN strengths s ON s.strength_id = o.related_strength_id
        LEFT JOIN child_outfits co
            ON co.outfit_id = o.outfit_id
            AND co.child_id = %s
        ORDER BY is_owned ASC, o.cost ASC, o.display_name ASC
        """,
        (child_id,),
    )


def purchase_outfit(child_id: str, outfit_id: str) -> int:
    outfit = fetch_one(
        "SELECT outfit_id, cost FROM outfits WHERE outfit_id = %s",
        (outfit_id,),
    )
    if not outfit:
        raise ValueError("找不到這個商品。")

    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM child_outfits
                    WHERE child_id = %s AND outfit_id = %s
                    FOR UPDATE
                    """,
                    (child_id, outfit_id),
                )
                if cursor.fetchone():
                    raise ValueError("你已經擁有這套服裝。")

                cursor.execute(
                    "SELECT tokens FROM children WHERE child_id = %s FOR UPDATE",
                    (child_id,),
                )
                child = cursor.fetchone()
                if not child:
                    raise ValueError("找不到孩子資料。")

                cost = int(outfit["cost"] or 0)
                new_balance = int(child["tokens"]) - cost
                if new_balance < 0:
                    raise InsufficientTokensError("代幣不足，還不能購買這套服裝。")

                cursor.execute(
                    """
                    INSERT INTO child_outfits (child_id, outfit_id, unlocked_source)
                    VALUES (%s, %s, %s)
                    """,
                    (child_id, outfit_id, "shop_purchase"),
                )
                cursor.execute(
                    "UPDATE children SET tokens = %s WHERE child_id = %s",
                    (new_balance, child_id),
                )
                if cost:
                    cursor.execute(
                        """
                        INSERT INTO token_transactions (child_id, amount, reason)
                        VALUES (%s, %s, %s)
                        """,
                        (child_id, -cost, "shop_purchase"),
                    )
            conn.commit()
            return new_balance
        except Exception:
            conn.rollback()
            raise
