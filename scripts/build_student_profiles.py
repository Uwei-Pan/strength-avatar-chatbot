import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = Path("/Users/webb/Downloads")
OUTPUT_PATH = PROJECT_ROOT / "data" / "student_strength_profiles.json"
SEED_PATH = PROJECT_ROOT / "database" / "seed_data.sql"

STRENGTH_META = {
    "創造力": ("智慧及知識", "creativity_brush"),
    "好奇心": ("智慧及知識", "curiosity_hat"),
    "判斷力": ("智慧及知識", "judgment_lens"),
    "喜愛學習": ("智慧及知識", "learning_glasses"),
    "洞察力": ("智慧及知識", "perspective_map"),
    "勇敢": ("勇氣", "bravery_cape"),
    "勤奮": ("勇氣", "perseverance_boots"),
    "真誠": ("勇氣", "honesty_badge"),
    "熱誠": ("勇氣", "zest_scarf"),
    "愛與被愛": ("仁愛", "love_pin"),
    "仁慈": ("仁愛", "kindness_cloak"),
    "社交智慧": ("仁愛", "social_bridge_badge"),
    "團體合作": ("公義", "teamwork_scarf"),
    "公平": ("公義", "fairness_scale"),
    "領導力": ("公義", "leadership_flag"),
    "寬恕": ("節制", "forgiveness_leaf"),
    "謙遜": ("節制", "humility_patch"),
    "審慎": ("節制", "prudence_lantern"),
    "自我規範": ("節制", "self_regulation_shield"),
    "欣賞美好": ("靈性及超越", "beauty_camera"),
    "感激": ("靈性及超越", "gratitude_badge"),
    "希望": ("靈性及超越", "hope_compass"),
    "幽默": ("靈性及超越", "humor_button"),
    "靈性": ("靈性及超越", "spirit_star"),
}

STRENGTH_IDS = {
    "創造力": "creativity",
    "好奇心": "curiosity",
    "判斷力": "judgment",
    "喜愛學習": "love_of_learning",
    "洞察力": "perspective",
    "勇敢": "bravery",
    "勤奮": "perseverance",
    "真誠": "honesty",
    "熱誠": "zest",
    "愛與被愛": "love",
    "仁慈": "kindness",
    "社交智慧": "social_intelligence",
    "團體合作": "teamwork",
    "公平": "fairness",
    "領導力": "leadership",
    "寬恕": "forgiveness",
    "謙遜": "humility",
    "審慎": "prudence",
    "自我規範": "self_regulation",
    "欣賞美好": "appreciation_of_beauty",
    "感激": "gratitude",
    "希望": "hope",
    "幽默": "humor",
    "靈性": "spirituality",
}

CHARACTER_CYCLE = ["fox", "cat", "rabbit", "inventor"]

ALIASES = {
    "毅力": "勤奮",
    "恆毅力": "勤奮",
    "堅毅": "勤奮",
    "生命力": "熱誠",
    "活力": "熱誠",
    "自制力": "自我規範",
    "自律": "自我規範",
    "自我調節": "自我規範",
    "正直": "真誠",
    "誠實": "真誠",
    "仁愛": "仁慈",
    "善良": "仁慈",
    "愛": "仁慈",
    "社會智能": "社交智慧",
    "社交智能": "社交智慧",
    "合作": "團體合作",
    "觀點": "洞察力",
    "智力展現": "判斷力",
    "智慧": "判斷力",
    "開明思想": "判斷力",
    "謹慎": "審慎",
    "喜好學習": "喜愛學習",
    "感恩": "感激",
    "謙虛": "謙遜",
}

ALL_STRENGTH_TERMS = sorted(
    set(STRENGTH_META) | set(ALIASES),
    key=len,
    reverse=True,
)
STRENGTH_LABEL_PATTERN = re.compile(
    r"(?P<name>"
    + "|".join(re.escape(term) for term in ALL_STRENGTH_TERMS)
    + r")\s*(?:[（(][A-Za-z -]{2,40}[）)])?\s*[：:]"
)
DATE_PATTERN = re.compile(r"(?<!\d)(9|10|11|12|1)/([0-3]?\d)(?!\d)")

REPLACEMENTS = {
    "瑋芯": "某生",
    "郁金": "某生",
    "昱翰": "某生",
    "威丞": "某生",
    "安妮": "某生",
    "世德": "某老師",
    "以琳": "某老師",
    "秀儒": "某老師",
    "芷伃": "某老師",
    "若妤": "某老師",
    "浩軒": "某生",
    "禹揚": "某生",
    "Andy": "某老師",
    "碩碩": "某生",
    "常閎": "某生",
    "大安高工": "目標學校",
    "大安": "目標學校",
    "南港高工": "目標學校",
    "松山高中": "某高中",
    "明星高中": "某高中",
    "能仁高職": "某高職",
    "遠雄人壽": "家人工作地點",
    "基隆": "外縣市",
    "101": "地標附近",
    "教會": "信仰活動",
    "受洗": "參與信仰儀式",
    "追思禮拜": "家中儀式",
    "阿祖過世": "家中發生變故",
    "阿公過世": "家中發生變故",
    "車禍": "意外事件",
    "蝴蝶刀": "不適合到校的物品",
    "媽媽": "家人",
    "爸爸": "家人",
    "阿公": "家人",
    "舅舅": "家人",
    "哥哥": "家人",
    "兄長": "家人",
    "兄弟": "家人",
    "弟弟": "家人",
    "妹妹": "家人",
    "姐姐": "家人",
    "姊姊": "家人",
    "阿姨": "師長",
    "家庭": "家中狀況",
    "家中": "家中狀況",
    "家人": "家人",
    "公司": "工作地點",
    "母親": "家中成員",
    "宗教背景": "個人信念",
    "電機與冷凍科系": "目標科系",
}


def main() -> None:
    profiles = []
    for letter in "BCDEFGHIJKLMNOP":
        pdf_path = _find_pdf(letter)
        text = _extract_pdf_text(pdf_path)
        profile = _build_profile(letter, text, pdf_path.name)
        profiles.append(profile)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps({"students": profiles}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_seed_profiles(profiles)
    print(f"Wrote {OUTPUT_PATH}")


def _find_pdf(letter: str) -> Path:
    matches = sorted(PDF_DIR.glob(f"認輔表－{letter}*.pdf"))
    if not matches:
        raise FileNotFoundError(f"找不到 {letter} 生 PDF")
    return matches[0]


def _extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _build_profile(letter: str, text: str, source_file: str) -> dict[str, Any]:
    entries = _split_records(text)
    cases_by_strength: dict[str, list[dict[str, Any]]] = defaultdict(list)
    records = []

    for entry_index, entry in enumerate(entries, start=1):
        month = _entry_month(entry["date"])
        extracted = _extract_cases(letter, entry["text"], month, entry_index)
        key_events = []
        for strength_name, cases in extracted.items():
            cases_by_strength[strength_name].extend(cases)
            key_events.extend(case["description"] for case in cases[:1])

        records.append(
            {
                "month": month,
                "source_label": entry["date"],
                "raw_summary": _record_summary(extracted),
                "key_events": key_events[:5],
            }
        )

    strengths = []
    for strength_name, evidence in sorted(
        cases_by_strength.items(), key=lambda item: (-len(item[1]), item[0])
    ):
        category, outfit_reward = STRENGTH_META[strength_name]
        strengths.append(
            {
                "strength_name": strength_name,
                "category": category,
                "frequency": len(evidence),
                "confidence": _confidence(len(evidence)),
                "evidence": evidence,
                "source_records": sorted({case["month"] for case in evidence}),
                "usage_context": sorted(
                    {
                        context
                        for case in evidence
                        for context in case["usage_context"]
                    }
                ),
                "outfit_reward": outfit_reward,
            }
        )

    top_strengths = _top_strengths(strengths)
    owned_strengths = [
        {
            "strength_name": item["strength_name"],
            "category": item["category"],
            "source": "counseling_record",
            "evidence": _first_evidence(strengths, item["strength_name"]),
            "outfit_reward": item["outfit_reward"],
        }
        for item in top_strengths
    ]

    return {
        "child_id": f"child_{letter}",
        "student_id": letter,
        "anonymous_name": f"{letter}生",
        "source_files": [source_file],
        "records": records,
        "strengths": strengths,
        "top_strengths": top_strengths,
        "strength_cases": {
            strength["strength_name"]: strength["evidence"]
            for strength in strengths
        },
        "owned_strengths": owned_strengths,
    }


def _split_records(text: str) -> list[dict[str, str]]:
    matches = [
        match
        for match in DATE_PATTERN.finditer(text)
        if _looks_like_record_date(match)
    ]
    records = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        date = match.group(0)
        segment = text[match.start():next_start].strip()
        if len(segment) >= 20:
            records.append({"date": date, "text": segment})
    return records


def _looks_like_record_date(match: re.Match[str]) -> bool:
    month = int(match.group(1))
    day = int(match.group(2))
    if month == 1 and day < 6:
        return False
    if not 1 <= day <= 31:
        return False
    prefix = match.string[max(0, match.start() - 16):match.start()]
    if re.search(r"(完成|作業|檢查|p\.?|P\.?|第|剩)\s*$", prefix):
        return False
    return True


def _extract_cases(
    letter: str, text: str, month: str, entry_index: int
) -> dict[str, list[dict[str, Any]]]:
    cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    matches = list(STRENGTH_LABEL_PATTERN.finditer(text))
    for match_index, match in enumerate(matches):
        raw_name = match.group("name")
        strength_name = ALIASES.get(raw_name, raw_name)
        if strength_name not in STRENGTH_META:
            continue
        start = match.end()
        next_start = matches[match_index + 1].start() if match_index + 1 < len(matches) else len(text)
        description = _clean_description(text[start:next_start])
        if not description:
            description = _fallback_description(text, match.start(), match.end())
        if not description:
            continue
        case_id = f"{letter}_{_case_slug(strength_name)}_{len(cases[strength_name]) + 1:03d}"
        cases[strength_name].append(
            {
                "case_id": case_id,
                "month": month,
                "source_record": f"{letter}-{entry_index:03d}",
                "description": description,
                "usage_context": ["ai_reply", "snake_game", "profile"],
            }
        )
    return cases


def _clean_description(raw_text: str) -> str:
    text = raw_text.strip()
    text = re.sub(r"^[：:()（）\-\s]+", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.split("--- PAGE")[0]
    text = re.split(r"(?=日期 課業輔導|優勢偵探)", text)[0]
    text = re.split(r"(?=[。；;]\s*[一-龥A-Z]?[：:])", text)[0]
    text = text.strip(" ，,。；;:：")
    text = _anonymize(text)
    if len(text) < 8:
        return ""
    if len(text) > 120:
        text = text[:120].rstrip("，,。 ") + "。"
    elif not text.endswith("。"):
        text += "。"
    return text


def _fallback_description(text: str, start: int, end: int) -> str:
    window = text[max(0, start - 80):min(len(text), end + 100)]
    window = re.sub(r"\s+", " ", window)
    window = _anonymize(window).strip(" ，,。；;:：")
    if len(window) < 12:
        return ""
    if len(window) > 100:
        window = window[:100].rstrip("，,。 ") + "。"
    elif not window.endswith("。"):
        window += "。"
    return window


def _record_summary(extracted: dict[str, list[dict[str, Any]]]) -> str:
    if not extracted:
        return "本次紀錄保留為匿名化學習與生活觀察，未擷取到明確優勢案例。"
    names = "、".join(sorted(extracted))
    return f"本次紀錄整理出與「{names}」相關的匿名化優勢觀察。"


def _entry_month(date_text: str) -> str:
    month = int(date_text.split("/")[0])
    year = 2026 if month == 1 else 2025
    return f"{year}-{month:02d}"


def _top_strengths(strengths: list[dict[str, Any]]) -> list[dict[str, Any]]:
    top = strengths[:5]
    result = []
    for rank, item in enumerate(top, start=1):
        result.append(
            {
                "rank": rank,
                "strength_name": item["strength_name"],
                "category": item["category"],
                "frequency": item["frequency"],
                "confidence": item["confidence"],
                "reason": _top_reason(item),
                "outfit_reward": item["outfit_reward"],
            }
        )
    return result


def _top_reason(item: dict[str, Any]) -> str:
    sample = item["evidence"][0]["description"] if item["evidence"] else ""
    return f"在多次紀錄中出現 {item['frequency']} 則可支持案例，例如：{sample}"


def _first_evidence(strengths: list[dict[str, Any]], strength_name: str) -> str:
    for strength in strengths:
        if strength["strength_name"] == strength_name and strength["evidence"]:
            return strength["evidence"][0]["description"]
    return "此優勢來自過去輔導紀錄的綜合判斷。"


def _confidence(frequency: int) -> str:
    if frequency >= 5:
        return "high"
    if frequency >= 2:
        return "medium"
    return "low"


def _case_slug(strength_name: str) -> str:
    return STRENGTH_IDS[strength_name]


def _anonymize(text: str) -> str:
    text = re.sub(r"[A-P]生", lambda match: match.group(0), text)
    for source, target in REPLACEMENTS.items():
        text = text.replace(source, target)
    text = re.sub(r"[A-Za-z]+老師", "某老師", text)
    text = text.replace("家中狀況狀況", "個人生活")
    text = text.replace("家中狀況", "個人生活")
    text = text.replace("家人", "重要他人")
    text = text.replace("母親", "家中成員")
    text = text.replace("家中成員", "重要他人")
    text = text.replace("宗教背景", "個人信念")
    text = text.replace("目標學校或南港高工", "目標學校")
    text = text.replace("目標學校/南港高工", "目標學校")
    return text


def _write_seed_profiles(profiles: list[dict[str, Any]]) -> None:
    seed_text = SEED_PATH.read_text(encoding="utf-8")
    marker = "INSERT INTO children"
    prefix = seed_text.split(marker, maxsplit=1)[0]
    SEED_PATH.write_text(prefix + _seed_profile_block(profiles), encoding="utf-8")


def _seed_profile_block(profiles: list[dict[str, Any]]) -> str:
    child_rows = []
    strength_rows = []
    outfit_rows = []
    confidence_values = {"high": "0.950", "medium": "0.750", "low": "0.550"}

    for index, profile in enumerate(profiles):
        child_id = profile["child_id"]
        letter = profile["student_id"]
        selected_outfit = profile["top_strengths"][0]["outfit_reward"]
        character = CHARACTER_CYCLE[index % len(CHARACTER_CYCLE)]
        child_rows.append(
            "("
            f"{_sql(child_id)}, {_sql(f'student{letter}')}, '1234', "
            f"{_sql(profile['anonymous_name'])}, 100, {_sql(character)}, {_sql(selected_outfit)}"
            ")"
        )
        outfit_rows.append(f"({_sql(child_id)}, 'starter_scarf', 'seed')")

        for strength in profile["top_strengths"]:
            strength_id = STRENGTH_IDS[strength["strength_name"]]
            evidence = _first_evidence(profile["strengths"], strength["strength_name"])
            confidence = confidence_values.get(strength.get("confidence", "low"), "0.550")
            strength_rows.append(
                "("
                f"{_sql(child_id)}, {_sql(strength_id)}, 'counseling_record', "
                f"{_sql(evidence)}, {confidence}"
                ")"
            )
            outfit_rows.append(
                f"({_sql(child_id)}, {_sql(strength['outfit_reward'])}, 'counseling_record')"
            )

    return (
        "INSERT INTO children (child_id, username, password_hash, name, tokens, selected_character, selected_outfit) VALUES\n"
        + ",\n".join(child_rows)
        + "\nON DUPLICATE KEY UPDATE\n"
        + "username = VALUES(username),\n"
        + "password_hash = VALUES(password_hash),\n"
        + "name = VALUES(name),\n"
        + "tokens = VALUES(tokens),\n"
        + "selected_character = VALUES(selected_character),\n"
        + "selected_outfit = VALUES(selected_outfit);\n\n"
        + "DELETE FROM child_strengths WHERE source = 'counseling_record';\n"
        + "DELETE FROM child_outfits WHERE unlocked_source = 'counseling_record';\n\n"
        + "INSERT INTO child_strengths (child_id, strength_id, source, evidence_text, confidence) VALUES\n"
        + ",\n".join(strength_rows)
        + "\n;\n\n"
        + "INSERT IGNORE INTO child_outfits (child_id, outfit_id, unlocked_source) VALUES\n"
        + ",\n".join(outfit_rows)
        + "\n;\n"
    )


def _sql(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


if __name__ == "__main__":
    main()
