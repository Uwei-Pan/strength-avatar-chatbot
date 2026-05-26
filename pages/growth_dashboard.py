from __future__ import annotations

from html import escape
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from database.db_connection import DatabaseConnectionError
from services.avatar_assets import (
    character_visual_html,
    get_character_profile,
    get_selected_outfit_profile,
    outfit_visual_html,
)
from services.child_service import get_child
from services.growth_dashboard_service import build_growth_dashboard


SOURCE_LABELS = {
    "initial_profile": "初始資料",
    "counseling_record": "過去紀錄",
    "chat": "聊天",
    "diary": "心情日記",
    "todo": "任務",
    "game": "遊戲",
    "game_reflection": "遊戲反思",
    "journal": "心情日記",
    "task": "任務",
    "game_response": "遊戲回答",
    "platform_interaction": "平台互動",
    "unknown": "其他",
}

CONFIDENCE_LABELS = {
    "high": "high",
    "medium": "medium",
    "low": "low",
}


def render() -> None:
    child_id = st.session_state.get("child_id")
    try:
        child = get_child(child_id)
        dashboard = build_growth_dashboard(str(child_id))
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return

    if not child:
        st.error("請先登入。")
        return

    character = get_character_profile(child.get("selected_character"))
    outfit = get_selected_outfit_profile(child)
    summary = dashboard["summary"]

    st.markdown(
        f"""
        <div class="growth-hero">
            <div class="growth-hero-visual">
                {character_visual_html(character, "is-large")}
                {outfit_visual_html(outfit, "is-mini")}
            </div>
            <div>
                <p class="kid-hero-title">{escape(str(child["name"]))}的成長足跡</p>
                <p class="kid-hero-copy">
                    每一次努力、分享與反思，都會幫助我們更認識你的閃光點。
                    這裡把一開始看到的優勢，和現在累積到的優勢放在一起看。
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_summary(summary)
    _render_via_backing(dashboard)
    _render_distribution(dashboard)
    _render_trend(dashboard)
    _render_sources(dashboard)
    _render_detail_table(dashboard)


def _render_summary(summary: dict[str, Any]) -> None:
    cols = st.columns(4)
    cols[0].metric("已發現優勢", int(summary.get("current_strength_count") or 0))
    cols[1].metric("新增看見", int(summary.get("new_strength_count") or 0))
    cols[2].metric("累積證據", int(summary.get("evidence_count") or 0))
    cols[3].metric("遊戲反思", int(summary.get("reflection_count") or 0))

    st.markdown(
        f"""
        <div class="growth-summary-strip">
            <span>常出現的優勢：<strong>{escape(str(summary.get("top_strength") or "還在累積中"))}</strong></span>
            <span>成長最多：<strong>{escape(str(summary.get("growth_strength") or "正在慢慢展開"))}</strong></span>
            <span>完成任務：<strong>{int(summary.get("completed_todo_count") or 0)}</strong></span>
            <span>日記篇數：<strong>{int(summary.get("diary_count") or 0)}</strong></span>
            <span>遊戲局數：<strong>{int(summary.get("game_session_count") or 0)}</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_via_backing(dashboard: dict[str, Any]) -> None:
    st.markdown('<p class="kid-section-title">VIA 優勢觀察背書</p>', unsafe_allow_html=True)
    st.info(
        "本分析依據 VIA 24 項品格優勢架構進行，但不是正式心理測驗結果；"
        "它是學習與輔導情境中的優勢觀察。證據少的項目會標示為需要更多觀察，不能稱為弱點。"
    )

    evidence_summary = list(dashboard.get("evidence_summary") or [])
    if not evidence_summary:
        st.caption("目前還沒有足夠的具體行為證據。")
        return

    for item in evidence_summary[:6]:
        with st.container(border=True):
            top_cols = st.columns([1.2, 1, 1.6], vertical_alignment="center")
            top_cols[0].markdown(f"**{escape(str(item.get('strength_name') or '優勢'))}**")
            top_cols[1].markdown(f"信心程度：`{CONFIDENCE_LABELS.get(str(item.get('confidence_level')), 'low')}`")
            top_cols[2].markdown(f"證據數：`{int(item.get('evidence_count') or 0)}`")

            source_counts = item.get("evidence_sources") or {}
            chips = []
            color_classes = ["chip-a", "chip-b", "chip-c", "chip-d", "chip-e", "chip-f"]
            for index, (source, count) in enumerate(source_counts.items()):
                label = SOURCE_LABELS.get(str(source), str(source))
                chips.append(
                    f'<span class="strength-chip {color_classes[index % len(color_classes)]}">'
                    f'{escape(label)}：{int(count)}</span>'
                )
            if chips:
                st.markdown(f'<div class="kid-badge-row">{"".join(chips)}</div>', unsafe_allow_html=True)

            for quote in item.get("evidence_quotes", [])[:3]:
                st.markdown(f"> {escape(str(quote))}")
            st.caption(str(item.get("reasoning_summary") or ""))


def _render_distribution(dashboard: dict[str, Any]) -> None:
    st.markdown('<p class="kid-section-title">品格優勢分布：過去 vs 現在</p>', unsafe_allow_html=True)
    comparison = list(dashboard.get("comparison") or [])
    if not comparison:
        st.info("尚無足夠資料可顯示分布。使用平台後，這裡會逐步長出你的優勢輪廓。")
        return

    rows = []
    for item in comparison[:14]:
        rows.append(
            {
                "優勢": item["strength_name"],
                "階段": "過去",
                "次數": int(item.get("past_count") or 0),
            }
        )
        rows.append(
            {
                "優勢": item["strength_name"],
                "階段": "現在",
                "次數": int(item.get("current_count") or 0),
            }
        )

    chart = (
        alt.Chart(pd.DataFrame(rows))
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            x=alt.X("次數:Q", title="被看見的次數", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("優勢:N", title="", sort=[item["strength_name"] for item in comparison[:14]]),
            color=alt.Color(
                "階段:N",
                title="階段",
                scale=alt.Scale(domain=["過去", "現在"], range=["#9fb7d8", "#ff9f43"]),
            ),
            tooltip=["階段", "優勢", "次數"],
        )
        .properties(height=max(260, min(560, len(comparison[:14]) * 34)))
    )
    st.altair_chart(chart, use_container_width=True)

    if not dashboard.get("has_initial_data"):
        st.caption("目前沒有明確的初始 profile，先用已知紀錄做保守比較。")
    if not dashboard.get("has_current_data"):
        st.caption("現在的資料還很少，日記、聊天與任務會慢慢讓圖表更完整。")


def _render_trend(dashboard: dict[str, Any]) -> None:
    st.markdown('<p class="kid-section-title">成長走勢</p>', unsafe_allow_html=True)
    trend = list(dashboard.get("trend") or [])
    if len(trend) < 2:
        st.info("目前趨勢資料還不多。持續記錄日記、完成任務或遊戲反思後，這裡會顯示你的成長變化。")
        return

    df = pd.DataFrame(trend)
    coverage_chart = (
        alt.Chart(df)
        .mark_line(point=True, strokeWidth=4)
        .encode(
            x=alt.X("period:N", title="時間", sort=None),
            y=alt.Y("strength_count:Q", title="已看見的優勢數", axis=alt.Axis(tickMinStep=1)),
            color=alt.value("#48a8f5"),
            tooltip=[
                alt.Tooltip("period:N", title="時間"),
                alt.Tooltip("strength_count:Q", title="優勢數"),
                alt.Tooltip("evidence_count:Q", title="累積證據"),
            ],
        )
    )
    evidence_chart = (
        alt.Chart(df)
        .mark_area(opacity=0.24, line={"color": "#69c779"}, color="#69c779")
        .encode(
            x=alt.X("period:N", sort=None),
            y=alt.Y("evidence_count:Q", title="累積證據"),
            tooltip=[
                alt.Tooltip("period:N", title="時間"),
                alt.Tooltip("evidence_count:Q", title="累積證據"),
            ],
        )
    )
    st.altair_chart((evidence_chart + coverage_chart).resolve_scale(y="independent"), use_container_width=True)


def _render_sources(dashboard: dict[str, Any]) -> None:
    source_counts = dashboard.get("source_counts") or {}
    if not source_counts:
        return
    st.markdown('<p class="kid-section-title">優勢從哪裡被看見</p>', unsafe_allow_html=True)
    chips = []
    color_classes = ["chip-a", "chip-b", "chip-c", "chip-d", "chip-e", "chip-f"]
    for index, (source, count) in enumerate(sorted(source_counts.items(), key=lambda item: item[1], reverse=True)):
        label = SOURCE_LABELS.get(str(source), str(source))
        chips.append(
            f'<span class="strength-chip {color_classes[index % len(color_classes)]}">'
            f'{escape(label)}：{int(count)}</span>'
        )
    st.markdown(f'<div class="kid-badge-row">{"".join(chips)}</div>', unsafe_allow_html=True)


def _render_detail_table(dashboard: dict[str, Any]) -> None:
    comparison = list(dashboard.get("comparison") or [])
    if not comparison:
        return
    st.markdown('<p class="kid-section-title">細節列表</p>', unsafe_allow_html=True)
    df = pd.DataFrame(
        [
            {
                "優勢": item["strength_name"],
                "類別": item.get("category") or "尚未分類",
                "過去": int(item.get("past_count") or 0),
                "現在": int(item.get("current_count") or 0),
                "增加": int(item.get("growth") or 0),
            }
            for item in comparison
        ]
    )
    st.dataframe(df, hide_index=True, use_container_width=True)
