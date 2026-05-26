from html import escape
from typing import Any


DEFAULT_CHARACTER = "fox"

CHARACTER_OPTIONS = [
    "fox",
    "rabbit",
    "bear",
    "owl",
    "deer",
    "turtle",
    "cat",
    "inventor",
]

CHARACTER_CATALOG: dict[str, dict[str, str]] = {
    "fox": {
        "display_name": "小狐狸",
        "emoji": "🦊",
        "title": "靈巧探路員",
        "description": "喜歡觀察路線，適合練習好奇心、判斷力和勇敢。",
        "accent": "chip-f",
    },
    "rabbit": {
        "display_name": "小兔子",
        "emoji": "🐰",
        "title": "溫柔跳跳隊友",
        "description": "一步一步往前跳，適合練習仁慈、希望和自我規範。",
        "accent": "chip-d",
    },
    "bear": {
        "display_name": "小熊",
        "emoji": "🐻",
        "title": "穩穩守護者",
        "description": "慢慢來也很有力量，適合練習堅持、寬恕和團體合作。",
        "accent": "chip-a",
    },
    "owl": {
        "display_name": "小貓頭鷹",
        "emoji": "🦉",
        "title": "夜光想想家",
        "description": "會停下來想一想，適合練習洞察力、喜愛學習和審慎。",
        "accent": "chip-e",
    },
    "deer": {
        "display_name": "小鹿",
        "emoji": "🦌",
        "title": "森林暖心信使",
        "description": "敏銳又親切，適合練習感激、欣賞美好和社交智慧。",
        "accent": "chip-b",
    },
    "turtle": {
        "display_name": "小烏龜",
        "emoji": "🐢",
        "title": "慢慢前進高手",
        "description": "照自己的節奏前進，適合練習勤奮、謙遜和自我規範。",
        "accent": "chip-c",
    },
    "cat": {
        "display_name": "小貓",
        "emoji": "🐱",
        "title": "安靜觀察員",
        "description": "會留意自己的感覺，也能練習真誠、好奇心和欣賞美好。",
        "accent": "chip-d",
    },
    "inventor": {
        "display_name": "小小發明家",
        "emoji": "🔧",
        "title": "點子製造員",
        "description": "把想法變成小實驗，適合練習創造力、判斷力和熱誠。",
        "accent": "chip-c",
    },
}

OUTFIT_CATALOG: dict[str, dict[str, str | None]] = {
    "starter_scarf": {
        "display_name": "初心圍巾",
        "emoji": "🧣",
        "short_description": "提醒你願意開始，就已經很棒。",
        "strength_name": None,
        "accent": "chip-c",
    },
    "creativity_brush": {
        "display_name": "創意畫筆",
        "emoji": "🖌️",
        "short_description": "把新點子畫出來，讓事情多一種可能。",
        "strength_name": "創造力",
        "accent": "chip-d",
    },
    "curiosity_hat": {
        "display_name": "好奇帽",
        "emoji": "🎩",
        "short_description": "戴上它，提醒自己多問一個為什麼。",
        "strength_name": "好奇心",
        "accent": "chip-c",
    },
    "judgment_lens": {
        "display_name": "判斷放大鏡",
        "emoji": "🔎",
        "short_description": "先看清楚，再做出適合自己的選擇。",
        "strength_name": "判斷力",
        "accent": "chip-b",
    },
    "learning_glasses": {
        "display_name": "學習眼鏡",
        "emoji": "👓",
        "short_description": "幫你看見今天想多懂一點的小知識。",
        "strength_name": "喜愛學習",
        "accent": "chip-c",
    },
    "perspective_map": {
        "display_name": "洞察地圖",
        "emoji": "🗺️",
        "short_description": "把經驗整理成方向，找到下一步。",
        "strength_name": "洞察力",
        "accent": "chip-e",
    },
    "bravery_cape": {
        "display_name": "勇敢披風",
        "emoji": "🦸",
        "short_description": "有點害怕也可以慢慢試一次。",
        "strength_name": "勇敢",
        "accent": "chip-f",
    },
    "perseverance_boots": {
        "display_name": "堅持靴",
        "emoji": "🥾",
        "short_description": "一步一步走完小任務，累了也能休息再前進。",
        "strength_name": "勤奮",
        "accent": "chip-a",
    },
    "honesty_badge": {
        "display_name": "真誠徽章",
        "emoji": "🏅",
        "short_description": "幫你練習說出真正的想法和感覺。",
        "strength_name": "真誠",
        "accent": "chip-b",
    },
    "zest_scarf": {
        "display_name": "熱誠領巾",
        "emoji": "🌈",
        "short_description": "把喜歡的事情變成今天的小能量。",
        "strength_name": "熱誠",
        "accent": "chip-d",
    },
    "love_pin": {
        "display_name": "關愛別針",
        "emoji": "💗",
        "short_description": "提醒你和重要的人保持溫暖連結。",
        "strength_name": "愛與被愛",
        "accent": "chip-d",
    },
    "kindness_cloak": {
        "display_name": "仁慈披風",
        "emoji": "🫶",
        "short_description": "把一句鼓勵或一個小幫忙送出去。",
        "strength_name": "仁慈",
        "accent": "chip-b",
    },
    "social_bridge_badge": {
        "display_name": "社交橋徽章",
        "emoji": "🌉",
        "short_description": "幫你注意自己和別人的感受。",
        "strength_name": "社交智慧",
        "accent": "chip-c",
    },
    "teamwork_scarf": {
        "display_name": "合作圍巾",
        "emoji": "🤝",
        "short_description": "和隊友一起完成，比一個人更有力量。",
        "strength_name": "團體合作",
        "accent": "chip-b",
    },
    "fairness_scale": {
        "display_name": "公平天秤",
        "emoji": "⚖️",
        "short_description": "提醒自己看見每個人的需要。",
        "strength_name": "公平",
        "accent": "chip-e",
    },
    "leadership_flag": {
        "display_name": "領導小旗",
        "emoji": "🚩",
        "short_description": "把大家帶到下一個小步驟。",
        "strength_name": "領導力",
        "accent": "chip-f",
    },
    "forgiveness_leaf": {
        "display_name": "寬恕葉片",
        "emoji": "🍃",
        "short_description": "先照顧受傷的地方，再慢慢放下。",
        "strength_name": "寬恕",
        "accent": "chip-b",
    },
    "humility_patch": {
        "display_name": "謙遜布章",
        "emoji": "🪡",
        "short_description": "看見自己做得好，也願意繼續學。",
        "strength_name": "謙遜",
        "accent": "chip-a",
    },
    "prudence_lantern": {
        "display_name": "審慎燈籠",
        "emoji": "🏮",
        "short_description": "行動前先停一下，照亮安全的選擇。",
        "strength_name": "審慎",
        "accent": "chip-f",
    },
    "self_regulation_shield": {
        "display_name": "自我規範盾牌",
        "emoji": "🛡️",
        "short_description": "深呼吸，幫自己穩穩做下一步。",
        "strength_name": "自我規範",
        "accent": "chip-c",
    },
    "beauty_camera": {
        "display_name": "美好相機",
        "emoji": "📷",
        "short_description": "捕捉生活裡漂亮、有趣或感動的小細節。",
        "strength_name": "欣賞美好",
        "accent": "chip-d",
    },
    "gratitude_badge": {
        "display_name": "感恩燈籠",
        "emoji": "✨",
        "short_description": "想起值得謝謝的人，讓心裡亮一點。",
        "strength_name": "感激",
        "accent": "chip-a",
    },
    "hope_compass": {
        "display_name": "希望星星",
        "emoji": "⭐",
        "short_description": "提醒你未來還有可能，今天先走一小步。",
        "strength_name": "希望",
        "accent": "chip-c",
    },
    "humor_button": {
        "display_name": "幽默鈕扣",
        "emoji": "😄",
        "short_description": "用一點微笑，讓氣氛變柔軟。",
        "strength_name": "幽默",
        "accent": "chip-a",
    },
    "spirit_star": {
        "display_name": "靈性星星",
        "emoji": "🌟",
        "short_description": "記得自己重視的原因，照亮努力的方向。",
        "strength_name": "靈性",
        "accent": "chip-e",
    },
}

OUTFIT_VISUALS = {
    "starter_scarf": "scarf",
    "creativity_brush": "brush",
    "curiosity_hat": "hat",
    "judgment_lens": "lens",
    "learning_glasses": "glasses",
    "perspective_map": "map",
    "bravery_cape": "cape",
    "perseverance_boots": "boots",
    "honesty_badge": "badge",
    "zest_scarf": "scarf",
    "love_pin": "pin",
    "kindness_cloak": "cloak",
    "social_bridge_badge": "bridge",
    "teamwork_scarf": "scarf",
    "fairness_scale": "scale",
    "leadership_flag": "flag",
    "forgiveness_leaf": "leaf",
    "humility_patch": "patch",
    "prudence_lantern": "lantern",
    "self_regulation_shield": "shield",
    "beauty_camera": "camera",
    "gratitude_badge": "lantern",
    "hope_compass": "star",
    "humor_button": "button",
    "spirit_star": "star",
}

OUTFIT_BUFFS: dict[str, dict[str, Any]] = {
    "starter_scarf": {
        "buff_type": "score_multiplier",
        "target_game": "all",
        "buff_value": 1.05,
        "buff_label": "兩個遊戲分數 +5%",
        "buff_description": "初心圍巾給你一點暖身力量，貪食蛇和方塊消除得分都小小提高。",
    },
    "creativity_brush": {
        "buff_type": "score_multiplier",
        "target_game": "block_puzzle",
        "buff_value": 1.10,
        "buff_label": "方塊消除分數 +10%",
        "buff_description": "創意畫筆幫你看見新的排列方法，方塊消除得分提高。",
    },
    "curiosity_hat": {
        "buff_type": "score_multiplier",
        "target_game": "block_puzzle",
        "buff_value": 1.10,
        "buff_label": "方塊消除分數 +10%",
        "buff_description": "好奇帽鼓勵你多試幾種放法，方塊消除得分提高。",
    },
    "judgment_lens": {
        "buff_type": "score_multiplier",
        "target_game": "block_puzzle",
        "buff_value": 1.08,
        "buff_label": "方塊消除分數 +8%",
        "buff_description": "判斷放大鏡提醒你先看清楚位置，方塊消除得分提高。",
    },
    "learning_glasses": {
        "buff_type": "score_multiplier",
        "target_game": "block_puzzle",
        "buff_value": 1.08,
        "buff_label": "方塊消除分數 +8%",
        "buff_description": "學習眼鏡幫你累積每次嘗試的收穫，方塊消除得分提高。",
    },
    "perspective_map": {
        "buff_type": "score_multiplier",
        "target_game": "block_puzzle",
        "buff_value": 1.08,
        "buff_label": "方塊消除分數 +8%",
        "buff_description": "洞察地圖幫你從大局看棋盤，方塊消除得分提高。",
    },
    "bravery_cape": {
        "buff_type": "score_multiplier",
        "target_game": "snake",
        "buff_value": 1.12,
        "buff_label": "貪食蛇分數 +12%",
        "buff_description": "勇敢披風幫你追逐優勢果實，貪食蛇得分提高。",
    },
    "perseverance_boots": {
        "buff_type": "score_multiplier",
        "target_game": "snake",
        "buff_value": 1.10,
        "buff_label": "貪食蛇分數 +10%",
        "buff_description": "堅持靴讓每次前進更有力量，貪食蛇得分提高。",
    },
    "self_regulation_shield": {
        "buff_type": "speed_multiplier",
        "target_game": "snake",
        "buff_value": 0.88,
        "buff_label": "貪食蛇速度放慢 12%",
        "buff_description": "自我規範盾牌讓節奏更穩，貪食蛇移動速度稍微放慢。",
    },
    "prudence_lantern": {
        "buff_type": "speed_multiplier",
        "target_game": "snake",
        "buff_value": 0.90,
        "buff_label": "貪食蛇速度放慢 10%",
        "buff_description": "審慎燈籠提醒你慢慢看路，貪食蛇移動速度稍微放慢。",
    },
    "teamwork_scarf": {
        "buff_type": "score_multiplier",
        "target_game": "block_puzzle",
        "buff_value": 1.08,
        "buff_label": "方塊消除分數 +8%",
        "buff_description": "合作圍巾讓每個方塊各就各位，方塊消除得分提高。",
    },
    "kindness_cloak": {
        "buff_type": "score_multiplier",
        "target_game": "all",
        "buff_value": 1.06,
        "buff_label": "兩個遊戲分數 +6%",
        "buff_description": "仁慈披風給你溫暖能量，兩個遊戲得分都小小提高。",
    },
    "gratitude_badge": {
        "buff_type": "score_multiplier",
        "target_game": "all",
        "buff_value": 1.06,
        "buff_label": "兩個遊戲分數 +6%",
        "buff_description": "感恩燈籠把努力照亮，兩個遊戲得分都小小提高。",
    },
    "hope_compass": {
        "buff_type": "score_multiplier",
        "target_game": "all",
        "buff_value": 1.06,
        "buff_label": "兩個遊戲分數 +6%",
        "buff_description": "希望星星提醒你可以再試，兩個遊戲得分都小小提高。",
    },
}

FALLBACK_BUFF = {
    "buff_type": "none",
    "target_game": "none",
    "buff_value": 0,
    "buff_label": "本遊戲沒有加成",
    "buff_description": "這件裝備目前只作為外觀展示，不會影響本局分數。",
}


def get_character_profile(character_key: str | None) -> dict[str, str]:
    key = character_key or DEFAULT_CHARACTER
    profile = CHARACTER_CATALOG.get(key, CHARACTER_CATALOG[DEFAULT_CHARACTER])
    return {"key": key, **profile}


def list_character_profiles() -> list[dict[str, str]]:
    return [get_character_profile(character_key) for character_key in CHARACTER_OPTIONS]


def get_outfit_profile(outfit: dict[str, Any] | str | None) -> dict[str, Any]:
    if isinstance(outfit, dict):
        outfit_id = str(outfit.get("outfit_id") or "")
        source = outfit
    else:
        outfit_id = str(outfit or "")
        source = {}

    catalog = OUTFIT_CATALOG.get(outfit_id, {})
    display_name = (
        source.get("display_name")
        or catalog.get("display_name")
        or outfit_id.replace("_", " ").strip()
        or "神祕裝備"
    )
    strength_name = source.get("strength_name") or catalog.get("strength_name")
    short_description = (
        catalog.get("short_description")
        or source.get("strength_description")
        or ("可以讓角色換上新的樣子。" if not strength_name else f"和「{strength_name}」有關的小裝備。")
    )
    return {
        "outfit_id": outfit_id,
        "display_name": display_name,
        "emoji": catalog.get("emoji", "🎒"),
        "visual": OUTFIT_VISUALS.get(outfit_id, "badge"),
        "short_description": short_description,
        "strength_name": strength_name,
        "category": source.get("category") or catalog.get("category") or "",
        "strength_description": source.get("strength_description") or "",
        "strength_suggestion": source.get("strength_suggestion") or "",
        "accent": catalog.get("accent", "chip-c"),
        "buff": OUTFIT_BUFFS.get(outfit_id, FALLBACK_BUFF),
        "cost": int(source.get("cost") or 0),
        "is_owned": bool(source.get("is_owned", False)),
        "unlocked_source": source.get("unlocked_source", ""),
    }


def get_selected_outfit_profile(child: dict[str, Any]) -> dict[str, Any]:
    selected = child.get("selected_outfit")
    for outfit in child.get("unlocked_outfits", []):
        if outfit.get("outfit_id") == selected:
            return get_outfit_profile(outfit)
    if selected:
        profile = get_outfit_profile(str(selected))
        profile["short_description"] = profile.get("short_description") or "這是目前設定中的裝備。"
        return profile
    fallback = get_outfit_profile(None)
    fallback["display_name"] = "尚未選擇"
    fallback["short_description"] = "可以到角色頁選一件已解鎖的裝備。"
    return fallback


def get_game_buff_for_child(child: dict[str, Any], game_type: str) -> dict[str, Any]:
    outfit = get_selected_outfit_profile(child)
    return normalize_game_buff(outfit, game_type)


def normalize_game_buff(outfit: dict[str, Any], game_type: str) -> dict[str, Any]:
    buff = dict(outfit.get("buff") or FALLBACK_BUFF)
    target = str(buff.get("target_game") or "none")
    applies = target in {game_type, "all"}
    buff_type = str(buff.get("buff_type") or "none") if applies else "none"
    raw_value = float(buff.get("buff_value") or 0)
    score_multiplier = 1.0
    speed_multiplier = 1.0
    bonus_start_score = 0
    if buff_type == "score_multiplier":
        score_multiplier = max(1.0, min(raw_value, 1.2))
    elif buff_type == "speed_multiplier":
        speed_multiplier = max(0.82, min(raw_value, 1.05))
    elif buff_type == "bonus_start_score":
        bonus_start_score = max(0, min(int(raw_value), 50))

    return {
        "outfit_id": outfit.get("outfit_id", ""),
        "outfit_name": outfit.get("display_name", "尚未選擇"),
        "outfit_visual": outfit.get("visual", "badge"),
        "game_type": game_type,
        "applies": applies and buff_type != "none",
        "buff_type": buff_type,
        "target_game": target,
        "buff_value": raw_value,
        "score_multiplier": score_multiplier,
        "speed_multiplier": speed_multiplier,
        "bonus_start_score": bonus_start_score,
        "buff_label": buff.get("buff_label") if applies else "本遊戲沒有加成",
        "buff_description": buff.get("buff_description") if applies else "這件裝備在本遊戲只作為外觀展示。",
    }


def character_visual_html(character: dict[str, Any], extra_class: str = "") -> str:
    key = _safe_css_token(str(character.get("key") or DEFAULT_CHARACTER))
    classes = f"character-visual character-visual-{key} {extra_class}".strip()
    return (
        f'<div class="{classes}" aria-label="{escape(str(character.get("display_name", "角色")))}">'
        '<span class="character-ear character-ear-left"></span>'
        '<span class="character-ear character-ear-right"></span>'
        '<span class="character-face-shape"></span>'
        '<span class="character-eye character-eye-left"></span>'
        '<span class="character-eye character-eye-right"></span>'
        '<span class="character-mark"></span>'
        '</div>'
    )


def outfit_visual_html(outfit: dict[str, Any], extra_class: str = "") -> str:
    visual = _safe_css_token(str(outfit.get("visual") or "badge"))
    outfit_id = _safe_css_token(str(outfit.get("outfit_id") or "fallback"))
    classes = f"gear-visual gear-visual-{visual} gear-outfit-{outfit_id} {extra_class}".strip()
    return (
        f'<div class="{classes}" aria-label="{escape(str(outfit.get("display_name", "裝備")))}">'
        '<span class="gear-aura"></span>'
        '<span class="gear-core"></span>'
        '<span class="gear-detail gear-detail-one"></span>'
        '<span class="gear-detail gear-detail-two"></span>'
        '<span class="gear-spark gear-spark-one"></span>'
        '<span class="gear-spark gear-spark-two"></span>'
        '</div>'
    )


def _safe_css_token(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value.lower())
    return safe.replace("_", "-") or "fallback"
