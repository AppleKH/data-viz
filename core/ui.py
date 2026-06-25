"""Общие элементы интерфейса: фирменный стиль, шапка, хлебные крошки.

Стилизовано под АС «Представление данных» Ситуационного центра.
"""
from __future__ import annotations

import streamlit as st

from core import charts

APP_NAME = "Представление данных"
APP_SUBTITLE = "Аналитическая платформа · визуализация данных"
PRIMARY = "#8B5CF6"        # фиолетовый акцент
ACCENT2 = "#C026D3"        # пурпурный (для градиента шапки)

_BASE_CSS = f"""
<style>
:root {{ --primary: {PRIMARY}; }}

/* Шапка приложения */
.app-header {{
    background: linear-gradient(90deg, {PRIMARY} 0%, {ACCENT2} 100%);
    color: #fff;
    padding: 14px 22px;
    border-radius: 10px;
    margin-bottom: 8px;
    box-shadow: 0 4px 14px rgba(139,92,246,.30);
}}
.app-header .title {{ font-size: 20px; font-weight: 700; letter-spacing:.2px; }}
.app-header .subtitle {{ font-size: 12.5px; opacity:.85; margin-top:2px; }}

/* Хлебные крошки (нейтральный серый — читаем в обеих темах) */
.crumbs {{ font-size: 12.5px; margin: 4px 0 14px 2px; color:#8895a7; }}
.crumbs b {{ color: var(--primary); }}

/* Бейдж уровня доступа */
.badge {{
    display:inline-block; font-size:11px; font-weight:600;
    padding:2px 9px; border-radius:11px; margin-left:6px;
}}
.badge-common {{ background:#E3F0FF; color:#1c5aa8; }}
.badge-private {{ background:#FCE8E6; color:#b3261e; }}

[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius:10px;
    border-color: rgba(139,92,246,.30);
}}
.stButton button[kind="primary"] {{
    background: var(--primary); border:0; font-weight:600;
}}
.stButton button[kind="primary"]:hover {{ background:{ACCENT2}; }}

/* Значения метрик (KPI) — фиолетовым акцентом, как на референсе */
[data-testid="stMetricValue"] {{ color: var(--primary) !important; }}

/* Активный пункт навигации — сиреневая «пилюля» */
[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background: rgba(139,92,246,.20) !important;
    border-radius: 8px !important;
}}
[data-testid="stSidebarNav"] a[aria-current="page"] [data-testid="stIconMaterial"] {{
    color: var(--primary) !important;
}}

/* Слайдер/ссылки в акцентном цвете */
a, .stMarkdown a {{ color: var(--primary); }}

/* === Свёрнутая боковая панель: узкая полоса с иконками разделов === */
section[data-testid="stSidebar"][aria-expanded="false"] {{
    transform: none !important;
    width: 3.5rem !important;
    min-width: 3.5rem !important;
    max-width: 3.5rem !important;
    margin-left: 0 !important;
    visibility: visible !important;
}}
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"][aria-expanded="false"] > div {{
    overflow: visible !important;
}}
/* Прячем подписи ссылок и заголовки групп — оставляем только иконки */
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNavLink"] > span:last-child,
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] header,
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarUserContent"] {{
    display: none !important;
}}
/* Заголовки групп (Навигация/Данные/Панели) — пункты списка без ссылки */
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] li:not(:has(a)) {{
    display: none !important;
}}
/* Обнуляем ВСЕ вертикальные отступы внутри навигации (между группами тоже) */
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] * {{
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}}
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] ul {{
    padding: 0 !important;
    gap: 0 !important;
}}
/* Каждая иконка-ссылка — одинаковой высоты => равномерный шаг */
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNavLink"] {{
    justify-content: center !important;
    padding: 9px 0 !important;
    margin: 0 !important;
}}
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {{
    font-size: 22px !important;
}}
</style>
"""


def is_dark_theme() -> bool:
    try:
        return st.context.theme.type == "dark"
    except Exception:  # noqa: BLE001 — на случай старого Streamlit
        return True


def active_template() -> str:
    """Шаблон Plotly под активную тему Streamlit (светлая/тёмная)."""
    return "plotly_dark" if is_dark_theme() else "plotly_white"


def inject_css() -> None:
    # Тёмно-фиолетовый фон задаётся темой в config.toml (нативно).
    # Здесь — только фирменные акценты (шапка, KPI, меню, рамки карточек).
    st.markdown(_BASE_CSS, unsafe_allow_html=True)


def app_header() -> None:
    st.markdown(
        f'<div class="app-header">'
        f'<div class="title">📊 {APP_NAME}</div>'
        f'<div class="subtitle">{APP_SUBTITLE}</div></div>',
        unsafe_allow_html=True,
    )


def breadcrumb(*items: str) -> None:
    """Хлебные крошки: breadcrumb('Главная', 'Виджеты', 'Добавление')."""
    parts = []
    for i, it in enumerate(items):
        parts.append(f"<b>{it}</b>" if i == len(items) - 1 else it)
    st.markdown(f'<div class="crumbs">{" › ".join(parts)}</div>',
                unsafe_allow_html=True)


def access_badge(level: str) -> str:
    """HTML-бейдж уровня доступа (Общий/Личный)."""
    if level == "Личный":
        return '<span class="badge badge-private">Личный</span>'
    return '<span class="badge badge-common">Общий</span>'


def render_widget(cfg: dict, df=None, *, key: str) -> None:
    """Отрисовывает виджет любого типа. ``key`` обеспечивает уникальные ID.

    ``df`` может быть None для статических виджетов (Html/Изображение/Дата-время).
    Графики автоматически следуют активной теме приложения (светлая/тёмная).
    """
    try:
        kind, payload = charts.build_figure(df, {**cfg, "_template": active_template()})
    except Exception as e:  # noqa: BLE001
        st.error(f"Ошибка построения виджета: {e}")
        return
    if kind == "metric":
        st.metric(cfg.get("title") or cfg.get("name", ""), payload)
    elif kind == "table":
        st.dataframe(payload, width="stretch", key=f"tbl_{key}")
    elif kind == "html":
        st.markdown(payload or "_Пусто_", unsafe_allow_html=True)
    elif kind == "image":
        if payload:
            st.image(payload, width="stretch")
        else:
            st.caption("URL изображения не задан")
    elif kind == "datetime":
        st.metric(cfg.get("title") or "Дата/время", charts.current_datetime())
    else:
        st.plotly_chart(payload, width="stretch", key=f"chart_{key}")
