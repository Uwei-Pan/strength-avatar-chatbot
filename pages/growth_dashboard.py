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

CHART_BACKGROUND = "#11141d"
CHART_GRID = "rgba(255, 231, 196, 0.18)"
CHART_TEXT = "#f7e8cf"
CHART_MUTED = "#d4bfa2"
PAST_COLOR = "#d9a66c"
CURRENT_COLOR = "#ff7f59"
TREND_LINE_COLOR = "#f4bf4f"
TREND_AREA_COLOR = "#f7a64b"
TREND_POINT_COLOR = "#ffe08a"


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
    _render_growth_stories(dashboard)
    _render_distribution(dashboard)
    _render_trend(dashboard)
    _render_sources(dashboard)
    _render_detail_table(dashboard)


def _render_summary(summary: dict[str, Any]) -> None:
    cols = st.columns(4)
    cols[0].metric("已發現優勢", int(summary.get("current_strength_count") or 0))
    cols[1].metric("新增看見", int(summary.get("new_strength_count") or 0))
    cols[2].metric("努力足跡", int(summary.get("effort_count") or summary.get("evidence_count") or 0))
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


def _render_growth_stories(dashboard: dict[str, Any]) -> None:
    st.markdown('<p class="kid-section-title">亮點小卡</p>', unsafe_allow_html=True)
    st.info("我們一起把日記、任務、聊天和遊戲反思裡的努力時刻收藏起來，慢慢看見你的閃光點。")
    evidence_summary = list(dashboard.get("evidence_summary") or [])
    if not evidence_summary:
        st.caption("目前亮點故事還在累積中。多分享一點生活小事，這裡會慢慢長出你的成長足跡。")
        return

    for item in evidence_summary[:6]:
        strength_name = str(item.get("strength_name") or "優勢")
        st.markdown(
            f"""
            <div class="growth-story-card">
                <strong>{escape(strength_name)}</strong>
                <p>你正在展現這個亮點，這些紀錄會陪你看見自己的成長。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"看看我的成長故事｜{strength_name}"):
            source_counts = item.get("evidence_sources") or {}
            chips = []
            color_classes = ["chip-a", "chip-b", "chip-c", "chip-d", "chip-e", "chip-f"]
            for index, source in enumerate(source_counts.keys()):
                label = SOURCE_LABELS.get(str(source), str(source))
                chips.append(f'<span class="strength-chip {color_classes[index % len(color_classes)]}">{escape(label)}</span>')
            if chips:
                st.markdown(f'<div class="kid-badge-row">{"".join(chips)}</div>', unsafe_allow_html=True)
            quotes = list(item.get("evidence_quotes") or [])[:3]
            if not quotes:
                st.caption("這個亮點正在慢慢累積更多故事。")
            for quote in quotes:
                st.markdown(f"> {escape(str(quote))}")


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
        .mark_bar(size=16)
        .encode(
            x=alt.X(
                "次數:Q",
                title="被看見的次數",
                axis=alt.Axis(tickMinStep=1, titlePadding=24, labelPadding=8),
            ),
            y=alt.Y(
                "優勢:N",
                title="",
                sort=[item["strength_name"] for item in comparison[:14]],
                axis=alt.Axis(labelPadding=8),
            ),
            color=alt.Color(
                "階段:N",
                title="階段",
                scale=alt.Scale(domain=["過去", "現在"], range=[PAST_COLOR, CURRENT_COLOR]),
                legend=alt.Legend(orient="top", titlePadding=8, labelPadding=8, symbolSize=120),
            ),
            tooltip=["階段", "優勢", "次數"],
        )
        .properties(
            height=max(280, min(580, len(comparison[:14]) * 36)),
            background=CHART_BACKGROUND,
            padding={"left": 8, "right": 28, "top": 18, "bottom": 30},
        )
        .configure_view(strokeWidth=0, fill=CHART_BACKGROUND)
        .configure_axis(
            gridColor=CHART_GRID,
            domainColor=CHART_MUTED,
            tickColor=CHART_MUTED,
            labelColor=CHART_TEXT,
            titleColor=CHART_TEXT,
            labelFontSize=13,
            titleFontSize=14,
        )
        .configure_legend(labelColor=CHART_TEXT, titleColor=CHART_TEXT, orient="top")
    )
    st.markdown('<div class="growth-chart-card">', unsafe_allow_html=True)
    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if not dashboard.get("has_initial_data"):
        st.caption("目前沒有明確的初始資料，先用已知紀錄陪你看見成長。")
    if not dashboard.get("has_current_data"):
        st.caption("現在的資料還很少，日記、聊天與任務會慢慢讓圖表更完整。")


def _render_trend(dashboard: dict[str, Any]) -> None:
    st.markdown('<p class="kid-section-title">成長走勢</p>', unsafe_allow_html=True)
    trend = list(dashboard.get("trend") or [])
    if len(trend) < 2:
        st.info("目前趨勢資料還不多。持續記錄日記、完成任務或遊戲反思後，這裡會顯示你的成長變化。")
        return

    df = pd.DataFrame(trend)
    if "period_order" not in df.columns:
        df["period_order"] = range(len(df))
    df = df.sort_values("period_order").reset_index(drop=True)
    max_strength_count = max(1, int(df["strength_count"].max()))
    y_max = max_strength_count + 1
    y_values = list(range(0, y_max + 1, 1))

    base = alt.Chart(df).encode(
        x=alt.X(
            "period:N",
            title="時間",
            sort=alt.SortField(field="period_order", order="ascending"),
            axis=alt.Axis(
                labelAngle=-34,
                labelAlign="right",
                labelPadding=14,
                titlePadding=34,
                labelLimit=150,
            ),
        ),
        y=alt.Y(
            "strength_count:Q",
            title="已看見的優勢數",
            scale=alt.Scale(domain=[0, y_max], nice=False),
            axis=alt.Axis(
                values=y_values,
                tickMinStep=1,
                labelPadding=12,
                titlePadding=38,
                titleAngle=-90,
            ),
        ),
        tooltip=[
            alt.Tooltip("period:N", title="時間"),
            alt.Tooltip("strength_count:Q", title="已看見的優勢數"),
        ],
    )
    area_chart = base.mark_area(
        color=TREND_AREA_COLOR,
        opacity=0.12,
        interpolate="monotone",
    )
    line_chart = base.mark_line(
        color=TREND_LINE_COLOR,
        strokeWidth=4,
        interpolate="monotone",
    )
    point_chart = base.mark_point(
        color=TREND_POINT_COLOR,
        fill=TREND_POINT_COLOR,
        stroke=CHART_BACKGROUND,
        strokeWidth=2,
        size=95,
    )
    chart = (
        (area_chart + line_chart + point_chart)
        .properties(
            height=360,
            background=CHART_BACKGROUND,
            padding={"left": 28, "right": 34, "top": 28, "bottom": 76},
        )
        .configure_view(strokeWidth=0, fill=CHART_BACKGROUND)
        .configure_axis(
            gridColor=CHART_GRID,
            domainColor=CHART_MUTED,
            tickColor=CHART_MUTED,
            labelColor=CHART_TEXT,
            titleColor=CHART_TEXT,
            labelFontSize=13,
            titleFontSize=15,
        )
    )
    st.markdown('<div class="growth-chart-card">', unsafe_allow_html=True)
    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if dashboard.get("uses_demo_growth_data"):
        st.caption("目前使用開發展示資料預覽走勢；有真實紀錄後會優先顯示孩子自己的成長資料。")


def _render_sources(dashboard: dict[str, Any]) -> None:
    source_counts = dashboard.get("source_counts") or {}
    if not source_counts:
        return
    st.markdown('<p class="kid-section-title">亮點來自哪些努力</p>', unsafe_allow_html=True)
    chips = []
    color_classes = ["chip-a", "chip-b", "chip-c", "chip-d", "chip-e", "chip-f"]
    for index, (source, count) in enumerate(sorted(source_counts.items(), key=lambda item: item[1], reverse=True)):
        label = SOURCE_LABELS.get(str(source), str(source))
        chips.append(
            f'<span class="strength-chip {color_classes[index % len(color_classes)]}">'
            f'{escape(label)}</span>'
        )
    st.markdown(f'<div class="kid-badge-row">{"".join(chips)}</div>', unsafe_allow_html=True)


def _render_detail_table(dashboard: dict[str, Any]) -> None:
    comparison = list(dashboard.get("comparison") or [])
    if not comparison:
        return
    st.markdown('<p class="kid-section-title">成長亮點列表</p>', unsafe_allow_html=True)
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
