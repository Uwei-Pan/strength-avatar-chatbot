from pathlib import Path

from db_connection import DatabaseConnectionError, get_connection, get_db_config


BASE_DIR = Path(__file__).resolve().parent


def _split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_string: str | None = None
    escape = False

    for char in sql_text:
        current.append(char)
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char in ("'", '"'):
            if in_string == char:
                in_string = None
            elif in_string is None:
                in_string = char
        elif char == ";" and in_string is None:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def _run_sql_file(path: Path) -> None:
    sql_text = path.read_text(encoding="utf-8")
    statements = _split_sql_statements(sql_text)
    with get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def initialize_database() -> None:
    config = get_db_config()
    with get_connection(use_database=False) as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{config.database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    _run_sql_file(BASE_DIR / "schema.sql")
    _run_sql_file(BASE_DIR / "seed_data.sql")


if __name__ == "__main__":
    try:
        initialize_database()
        print("Database initialized successfully.")
    except DatabaseConnectionError as exc:
        print(f"Database connection failed: {exc}")
        raise SystemExit(1)
    except Exception as exc:
        print(f"Database initialization failed: {exc}")
        raise SystemExit(1)
