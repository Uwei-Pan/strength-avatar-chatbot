from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any

from database.db_connection import DatabaseConnectionError, fetch_all, fetch_one
from services.student_profile_service import get_top_strengths
from services.strength_service import normalize_strength_name


def build_growth_dashboard(child_id: str) -> dict[str, Any]:
    records = _fetch_strength_records(child_id)
    initial_rows = _initial_strength_rows(child_id, records)

    initial_counts = _count_strengths(initial_rows)
    current_counts = _count_strengths(records)
    for strength_name, count in initial_counts.items():
        current_counts[strength_name] = max(current_counts.get(strength_name, 0), count)

    comparison = _comparison_rows(initial_counts, current_counts, initial_rows, records)
    trend = _trend_rows(records, initial_counts)
    source_counts = Counter(str(row.get("source") or "unknown") for row in records)
    summary = _summary(initial_counts, current_counts, records, comparison, child_id)

    return {
        "initial_distribution": _distribution_rows(initial_counts, initial_rows),
        "current_distribution": _distribution_rows(current_counts, records),
        "comparison": comparison,
        "trend": trend,
        "source_counts": dict(source_counts),
        "summary": summary,
        "has_initial_data": bool(initial_counts),
        "has_current_data": bool(current_counts),
        "has_trend_data": len(trend) >= 2,
    }


def _fetch_strength_records(child_id: str) -> list[dict[str, Any]]:
    return list(
        fetch_all(
            """
            SELECT
                s.name_zh AS strength_name,
                s.category,
                cs.source,
                cs.evidence_text,
                cs.created_at
            FROM child_strengths cs
            JOIN strengths s ON s.strength_id = cs.strength_id
            WHERE cs.child_id = %s
            ORDER BY cs.created_at ASC, cs.id ASC
            """,
            (child_id,),
        )
    )


def _initial_strength_rows(child_id: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profile_rows = []
    for item in get_top_strengths(child_id):
        strength_name = normalize_strength_name(str(item.get("strength_name") or ""))
        if not strength_name:
            continue
        profile_rows.append(
            {
                "strength_name": strength_name,
                "category": item.get("category") or "",
                "source": "initial_profile",
                "created_at": None,
            }
        )
    if profile_rows:
        return profile_rows

    return [
        row
        for row in records
        if str(row.get("source") or "") == "counseling_record"
    ]


def _count_strengths(rows: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        strength_name = normalize_strength_name(str(row.get("strength_name") or ""))
        if strength_name:
            counter[strength_name] += 1
    return counter


def _distribution_rows(counter: Counter[str], source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    categories = _category_lookup(source_rows)
    return [
        {
            "strength_name": strength_name,
            "category": categories.get(strength_name, ""),
            "count": int(count),
        }
        for strength_name, count in counter.most_common()
    ]


def _comparison_rows(
    initial_counts: Counter[str],
    current_counts: Counter[str],
    initial_rows: list[dict[str, Any]],
    current_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    categories = {
        **_category_lookup(initial_rows),
        **_category_lookup(current_rows),
    }
    names = sorted(
        set(initial_counts) | set(current_counts),
        key=lambda name: (current_counts.get(name, 0), initial_counts.get(name, 0), name),
        reverse=True,
    )
    return [
        {
            "strength_name": name,
            "category": categories.get(name, ""),
            "past_count": int(initial_counts.get(name, 0)),
            "current_count": int(current_counts.get(name, 0)),
            "growth": int(current_counts.get(name, 0) - initial_counts.get(name, 0)),
        }
        for name in names
    ]


def _trend_rows(records: list[dict[str, Any]], initial_counts: Counter[str]) -> list[dict[str, Any]]:
    if not records and not initial_counts:
        return []

    seen = set(initial_counts.keys())
    evidence_count = 0 if records else int(sum(initial_counts.values()))
    by_period: dict[str, dict[str, Any]] = {}
    if initial_counts:
        by_period["初始"] = {
            "period": "初始",
            "evidence_count": evidence_count,
            "strength_count": len(seen),
        }
    for row in records:
        strength_name = normalize_strength_name(str(row.get("strength_name") or ""))
        if not strength_name:
            continue
        seen.add(strength_name)
        evidence_count += 1
        period = _period_label(row.get("created_at"))
        by_period[period] = {
            "period": period,
            "evidence_count": evidence_count,
            "strength_count": len(seen),
        }
    return list(by_period.values())


def _summary(
    initial_counts: Counter[str],
    current_counts: Counter[str],
    records: list[dict[str, Any]],
    comparison: list[dict[str, Any]],
    child_id: str,
) -> dict[str, Any]:
    current_total = len(current_counts)
    initial_total = len(initial_counts)
    new_strengths = max(0, current_total - initial_total)
    top_strength = ""
    if current_counts:
        top_strength = current_counts.most_common(1)[0][0]
    growth_strength = ""
    positive_growth = [row for row in comparison if int(row.get("growth", 0)) > 0]
    if positive_growth:
        growth_strength = max(positive_growth, key=lambda row: int(row["growth"]))["strength_name"]

    return {
        "initial_strength_count": initial_total,
        "current_strength_count": current_total,
        "new_strength_count": new_strengths,
        "evidence_count": len(records),
        "top_strength": top_strength or "還在累積中",
        "growth_strength": growth_strength or "正在慢慢展開",
        "reflection_count": _safe_count("SELECT COUNT(*) AS count FROM game_reflections WHERE child_id = %s", child_id),
        "diary_count": _safe_count("SELECT COUNT(*) AS count FROM diary_entries WHERE child_id = %s", child_id),
        "completed_todo_count": _safe_count(
            "SELECT COUNT(*) AS count FROM todo_items WHERE child_id = %s AND is_completed = TRUE",
            child_id,
        ),
        "game_session_count": _safe_count("SELECT COUNT(*) AS count FROM game_sessions WHERE child_id = %s", child_id),
    }


def _category_lookup(rows: list[dict[str, Any]]) -> dict[str, str]:
    result = {}
    for row in rows:
        strength_name = normalize_strength_name(str(row.get("strength_name") or ""))
        if strength_name and row.get("category"):
            result[strength_name] = str(row.get("category"))
    return result


def _safe_count(sql: str, child_id: str) -> int:
    try:
        row = fetch_one(sql, (child_id,))
    except DatabaseConnectionError:
        raise
    except Exception:
        return 0
    return int((row or {}).get("count") or 0)


def _period_label(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%m/%d")
    if isinstance(value, date):
        return value.strftime("%m/%d")
    text = str(value or "")
    if len(text) >= 10:
        return text[5:10]
    return text or "今天"
