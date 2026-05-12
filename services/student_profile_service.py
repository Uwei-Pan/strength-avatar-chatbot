import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

from services.strength_service import normalize_strength_name


PROFILE_PATH = Path(__file__).resolve().parents[1] / "data" / "student_strength_profiles.json"


@lru_cache(maxsize=1)
def load_student_profiles() -> dict[str, dict[str, Any]]:
    if not PROFILE_PATH.exists():
        return {}
    data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    return {
        profile["child_id"]: profile
        for profile in data.get("students", [])
        if profile.get("child_id")
    }


def get_student_profile(child_id: str) -> dict[str, Any] | None:
    return load_student_profiles().get(child_id)


def get_student_strength_cases(child_id: str, strength_name: str) -> list[dict[str, Any]]:
    profile = get_student_profile(child_id)
    if not profile:
        return []
    normalized = normalize_strength_name(strength_name)
    cases = profile.get("strength_cases", {}).get(normalized, [])
    return list(cases) if isinstance(cases, list) else []


def get_random_strength_case(child_id: str, strength_name: str) -> dict[str, Any] | None:
    cases = get_student_strength_cases(child_id, strength_name)
    if not cases:
        return None
    return random.choice(cases)


def get_top_strengths(child_id: str) -> list[dict[str, Any]]:
    profile = get_student_profile(child_id)
    if not profile:
        return []
    strengths = profile.get("top_strengths", [])
    return list(strengths) if isinstance(strengths, list) else []


def get_initial_equipment(child_id: str) -> list[dict[str, Any]]:
    return [
        {
            "strength_name": item.get("strength_name"),
            "category": item.get("category"),
            "outfit_reward": item.get("outfit_reward"),
            "source": "counseling_record",
        }
        for item in get_top_strengths(child_id)
        if item.get("outfit_reward")
    ]


def get_ai_case_context(child_id: str, max_strengths: int = 5, max_cases_each: int = 2) -> str:
    profile = get_student_profile(child_id)
    if not profile:
        return "沒有可引用的過去案例。"

    lines = []
    for strength in profile.get("top_strengths", [])[:max_strengths]:
        strength_name = strength.get("strength_name")
        if not strength_name:
            continue
        cases = get_student_strength_cases(child_id, strength_name)[:max_cases_each]
        if not cases:
            continue
        descriptions = "；".join(case.get("description", "") for case in cases)
        lines.append(f"- {strength_name}：{descriptions}")

    if not lines:
        return "沒有可引用的過去案例。"
    return "\n".join(lines)
