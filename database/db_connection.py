import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:  # pragma: no cover - handled at runtime with a clear message.
    pymysql = None
    DictCursor = None


load_dotenv()


class DatabaseConnectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


def get_db_config() -> DatabaseConfig:
    return DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "ai_for_children"),
    )


def get_connection(use_database: bool = True):
    if pymysql is None:
        raise DatabaseConnectionError(
            "缺少 pymysql 套件，請先執行 `pip install -r requirements.txt`。"
        )

    config = get_db_config()
    try:
        return pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database if use_database else None,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )
    except Exception as exc:
        target = config.database if use_database else "MySQL server"
        raise DatabaseConnectionError(
            f"無法連線到 {target}。請確認 MySQL 已啟動、.env 設定正確，"
            f"並已建立資料庫 `{config.database}`。原始錯誤：{exc}"
        ) from exc


def fetch_one(sql: str, params: tuple[Any, ...] | dict[str, Any] | None = None):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def fetch_all(sql: str, params: tuple[Any, ...] | dict[str, Any] | None = None):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def execute(sql: str, params: tuple[Any, ...] | dict[str, Any] | None = None) -> int:
    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                affected = cursor.execute(sql, params)
            conn.commit()
            return affected
        except Exception:
            conn.rollback()
            raise
