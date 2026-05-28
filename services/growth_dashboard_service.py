from __future__ import annotations

import os
from collections import Counter
from datetime import date, datetime
from typing import Any

from database.db_connection import DatabaseConnectionError, fetch_all, fetch_one
from services.student_profile_service import get_top_strengths
from services.strength_service import detect_strengths_rule_based, normalize_strength_name


SOURCE_ALIASES = {
    "initial_profile": "counseling_record",
    "counseling_record": "counseling_record",
    "diary": "journal",
    "journal": "journal",
    "todo": "task",
    "task": "task",
    "game": "game_response",
    "game_reflection": "game_response",
    "game_response": "game_response",
    "chat": "platform_interaction",
    "platform_interaction": "platform_interaction",
    "unknown": "platform_interaction",
}

DASHBOARD_DEMO_GROWTH_ENV = "DASHBOARD_USE_DEMO_GROWTH"

LOW_OBSERVATION_PHRASES = [
    "想知道我的優勢",
    "可以給我建議",
    "可以鼓勵我",
    "請給我一個小任務",
    "我不知道怎麼",
    "呼叫不到你",
    "不知道",
    "還好",
    "嗨",
]


def build_growth_dashboard(child_id: str) -> dict[str, Any]:
    records = _dedupe_records(_fetch_strength_records(child_id) + _fetch_inferred_activity_records(child_id))
    initial_rows = _initial_strength_rows(child_id, records)

    initial_counts = _count_strengths(initial_rows)
    current_counts = _count_strengths(records)
    for strength_name, count in initial_counts.items():
        current_counts[strength_name] = max(current_counts.get(strength_name, 0), count)

    comparison = _comparison_rows(initial_counts, current_counts, initial_rows, records)
    trend = _trend_rows(records, initial_counts, initial_rows)
    source_counts = Counter(_canonical_source(str(row.get("source") or "unknown")) for row in records)
    summary = _summary(initial_counts, current_counts, records, comparison, child_id)
    uses_demo_growth_data = _should_use_demo_growth_data(records, initial_counts)
    if uses_demo_growth_data:
        demo = get_demo_growth_data()
        comparison = demo["comparison"]
        trend = demo["trend"]
        source_counts = Counter(demo["source_counts"])
        summary = {**summary, **demo["summary"]}

    return {
        "initial_distribution": _distribution_rows(initial_counts, initial_rows),
        "current_distribution": _distribution_rows(current_counts, records),
        "comparison": comparison,
        "trend": trend,
        "source_counts": dict(source_counts),
        "evidence_summary": _evidence_summary(records),
        "summary": summary,
        "has_initial_data": bool(initial_counts),
        "has_current_data": bool(current_counts),
        "has_trend_data": len(trend) >= 2,
        "uses_demo_growth_data": uses_demo_growth_data,
    }


def get_demo_growth_data() -> dict[str, Any]:
    """Development-only dashboard sample data; never writes to or replaces student records."""
    trend = [
        {"period": "初始｜2026-05-12", "period_order": 0, "strength_count": 1, "effort_count": 0},
        {"period": "2026-05-15", "period_order": 1, "strength_count": 3, "effort_count": 4},
        {"period": "2026-05-18", "period_order": 2, "strength_count": 5, "effort_count": 8},
        {"period": "2026-05-21", "period_order": 3, "strength_count": 7, "effort_count": 13},
        {"period": "2026-05-26", "period_order": 4, "strength_count": 9, "effort_count": 18},
        {"period": "2026-05-28", "period_order": 5, "strength_count": 12, "effort_count": 24},
    ]
    comparison_specs = [
        ("勤奮", "勇氣", 1, 4),
        ("希望", "靈性及超越", 1, 3),
        ("好奇心", "智慧及知識", 0, 3),
        ("仁慈", "人性", 0, 3),
        ("自我規範", "節制", 0, 2),
        ("感激", "靈性及超越", 0, 2),
        ("創造力", "智慧及知識", 0, 2),
        ("團體合作", "正義", 0, 2),
        ("真誠", "勇氣", 0, 1),
        ("勇敢", "勇氣", 0, 1),
        ("欣賞美好", "靈性及超越", 0, 1),
        ("社交智慧", "人性", 0, 1),
    ]
    comparison = [
        {
            "strength_name": strength_name,
            "category": category,
            "past_count": past_count,
            "current_count": current_count,
            "growth": current_count - past_count,
        }
        for strength_name, category, past_count, current_count in comparison_specs
    ]
    return {
        "trend": trend,
        "comparison": comparison,
        "source_counts": {
            "journal": 8,
            "task": 6,
            "platform_interaction": 5,
            "game_response": 5,
        },
        "summary": {
            "initial_strength_count": 1,
            "current_strength_count": 12,
            "new_strength_count": 11,
            "effort_count": 24,
            "evidence_count": 24,
            "top_strength": "勤奮",
            "growth_strength": "勤奮",
        },
    }


def _should_use_demo_growth_data(records: list[dict[str, Any]], initial_counts: Counter[str]) -> bool:
    if os.getenv(DASHBOARD_DEMO_GROWTH_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return not records and not initial_counts


def _fetch_strength_records(child_id: str) -> list[dict[str, Any]]:
    return list(
        fetch_all(
            """
            SELECT
                s.name_zh AS strength_name,
                s.category,
                cs.source,
                cs.evidence_text,
                cs.confidence,
                cs.created_at
            FROM child_strengths cs
            JOIN strengths s ON s.strength_id = cs.strength_id
            WHERE cs.child_id = %s
            ORDER BY cs.created_at ASC, cs.id ASC
            """,
            (child_id,),
        )
    )


def _fetch_inferred_activity_records(child_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(_infer_from_text_rows(
        _safe_fetch_rows(
            """
            SELECT content AS text, created_at
            FROM diary_entries
            WHERE child_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 30
            """,
            child_id,
        ),
        "journal",
    ))
    rows.extend(_infer_from_text_rows(
        _safe_fetch_rows(
            """
            SELECT CONCAT(
                CASE WHEN is_completed THEN '已完成任務：' ELSE '未完成任務：' END,
                title,
                CASE WHEN description IS NULL OR description = '' THEN '' ELSE CONCAT('；', description) END
            ) AS text,
            COALESCE(completed_at, created_at) AS created_at,
            is_completed
            FROM todo_items
            WHERE child_id = %s
            ORDER BY COALESCE(completed_at, created_at) DESC, id DESC
            LIMIT 30
            """,
            child_id,
        ),
        "task",
    ))
    rows.extend(_infer_from_text_rows(
        _safe_fetch_rows(
            """
            SELECT CONCAT('問題：', question, '；回答：', answer) AS text, created_at
            FROM game_reflections
            WHERE child_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 30
            """,
            child_id,
        ),
        "game_response",
    ))
    rows.extend(_infer_from_text_rows(
        _safe_fetch_rows(
            """
            SELECT user_message AS text, created_at
            FROM chat_logs
            WHERE child_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 30
            """,
            child_id,
        ),
        "platform_interaction",
    ))
    return rows


def _safe_fetch_rows(sql: str, child_id: str) -> list[dict[str, Any]]:
    try:
        return list(fetch_all(sql, (child_id,)))
    except Exception:
        return []


def _infer_from_text_rows(rows: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
    inferred = []
    for row in rows:
        text = str(row.get("text") or "").strip()
        if not text:
            continue
        detections = detect_strengths_rule_based(text, source=source)
        if source == "task" and row.get("is_completed") and not any(
            item.get("strength_name") == "勤奮" for item in detections
        ):
            detections.append(
                {
                    "strength_name": "勤奮",
                    "confidence": 0.55,
                    "confidence_level": "low",
                    "reason": "完成任務可作為勤奮的低度行為線索，仍需更多情境佐證。",
                }
            )
        for item in detections:
            inferred.append(
                {
                    "strength_name": normalize_strength_name(str(item.get("strength_name") or "")),
                    "category": "",
                    "source": _canonical_source(source),
                    "evidence_text": text,
                    "confidence": float(item.get("confidence") or 0.55),
                    "created_at": row.get("created_at"),
                }
            )
    return inferred


def _dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for row in records:
        strength_name = normalize_strength_name(str(row.get("strength_name") or ""))
        evidence = str(row.get("evidence_text") or "").strip()
        if not strength_name or not evidence:
            continue
        row = dict(row)
        row["strength_name"] = strength_name
        row["source"] = _canonical_source(str(row.get("source") or "platform_interaction"))
        if row["source"] != "counseling_record" and _is_low_observation_text(evidence):
            continue
        key = (strength_name, row["source"], evidence[:160])
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    result.sort(key=lambda item: str(item.get("created_at") or ""))
    return result


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
                "source": "counseling_record",
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


def _trend_rows(
    records: list[dict[str, Any]],
    initial_counts: Counter[str],
    initial_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not records and not initial_counts:
        return []

    # The trend is a child-facing growth trail: start from a low initial point,
    # then climb as platform interactions reveal more distinct strengths.
    seen: set[str] = set()
    initial_strength_count = 1 if initial_counts else 0
    effort_count = 0
    by_period: dict[str, dict[str, Any]] = {}
    initial_label = _initial_period_label(initial_rows, records)
    by_period[initial_label] = {
        "period": initial_label,
        "period_order": 0,
        "evidence_count": effort_count,
        "effort_count": effort_count,
        "strength_count": initial_strength_count,
    }
    for index, row in enumerate(records, start=1):
        strength_name = normalize_strength_name(str(row.get("strength_name") or ""))
        if not strength_name:
            continue
        seen.add(strength_name)
        effort_count += 1
        period = _period_label(row.get("created_at"))
        by_period[period] = {
            "period": period,
            "period_order": index,
            "evidence_count": effort_count,
            "effort_count": effort_count,
            "strength_count": min(24, initial_strength_count + len(seen)),
        }
    return sorted(by_period.values(), key=lambda item: int(item.get("period_order") or 0))


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
        "effort_count": len(records),
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


def _evidence_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        strength_name = normalize_strength_name(str(row.get("strength_name") or ""))
        if strength_name:
            grouped.setdefault(strength_name, []).append(row)

    result = []
    for strength_name, rows in grouped.items():
        source_counts = Counter(_canonical_source(str(row.get("source") or "unknown")) for row in rows)
        confidences = [_safe_float(row.get("confidence"), 0.55) for row in rows]
        evidence_count = len(rows)
        result.append(
            {
                "strength_name": strength_name,
                "confidence_level": _confidence_level(evidence_count, source_counts, max(confidences or [0.0])),
                "evidence_count": evidence_count,
                "evidence_sources": dict(source_counts),
                "evidence_quotes": _evidence_quotes(rows),
                "reasoning_summary": _reasoning_summary(strength_name, evidence_count, source_counts),
            }
        )

    result.sort(
        key=lambda item: (
            {"high": 3, "medium": 2, "low": 1}.get(item["confidence_level"], 0),
            item["evidence_count"],
            item["strength_name"],
        ),
        reverse=True,
    )
    return result


def _confidence_level(evidence_count: int, source_counts: Counter[str], max_confidence: float) -> str:
    if evidence_count >= 4 and len(source_counts) >= 2:
        return "high"
    if max_confidence >= 0.82 and evidence_count >= 2:
        return "high"
    if evidence_count >= 2 or max_confidence >= 0.65:
        return "medium"
    return "low"


def _evidence_quotes(rows: list[dict[str, Any]]) -> list[str]:
    quotes = []
    for row in sorted(rows, key=lambda item: str(item.get("created_at") or ""), reverse=True):
        text = str(row.get("evidence_text") or "").strip().replace("\n", " ")
        if not text:
            continue
        if len(text) > 180:
            text = text[:180] + "..."
        if text not in quotes:
            quotes.append(text)
        if len(quotes) >= 3:
            break
    return quotes


def _reasoning_summary(strength_name: str, evidence_count: int, source_counts: Counter[str]) -> str:
    sources = "、".join(source_counts.keys())
    if evidence_count <= 1:
        return f"目前有一個與「{strength_name}」有關的成長時刻，值得好好收藏。"
    return f"目前已從 {sources} 看見多個「{strength_name}」的努力時刻。"


def _is_low_observation_text(text: str) -> bool:
    compact = "".join(text.split())
    if len(compact) <= 8:
        return True
    return any(phrase in compact for phrase in LOW_OBSERVATION_PHRASES)


def _category_lookup(rows: list[dict[str, Any]]) -> dict[str, str]:
    result = {}
    for row in rows:
        strength_name = normalize_strength_name(str(row.get("strength_name") or ""))
        if strength_name and row.get("category"):
            result[strength_name] = str(row.get("category"))
    return result


def _canonical_source(source: str) -> str:
    return SOURCE_ALIASES.get(str(source or "unknown"), "platform_interaction")


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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


def _initial_period_label(initial_rows: list[dict[str, Any]], records: list[dict[str, Any]]) -> str:
    value = _first_date_value(initial_rows) or _first_date_value(records)
    formatted = _full_date_label(value)
    return f"初始｜{formatted}" if formatted else "初始｜開始使用時"


def _first_date_value(rows: list[dict[str, Any]]) -> Any:
    dated_rows = [row.get("created_at") for row in rows if row.get("created_at")]
    if not dated_rows:
        return None
    return sorted(dated_rows, key=lambda value: str(value))[0]


def _full_date_label(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    text = str(value or "")
    if len(text) >= 10:
        return text[:10]
    return ""
