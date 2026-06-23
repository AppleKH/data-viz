"""Общие элементы интерфейса: фирменный стиль, шапка, хлебные крошки.

Стилизовано под АС «Представление данных» Ситуационного центра.
"""
from __future__ import annotations

import streamlit as st

from core import charts

APP_NAME = "Представление данных"
APP_SUBTITLE = "Аналитическая платформа · визуализация данных"
PRIMARY = "#2E6CB5"

_CSS = f"""
<style>
:root {{ --primary: {PRIMARY}; }}

/* Шапка приложения */
.app-header {{
    background: linear-gradient(90deg, {PRIMARY} 0%, #244e88 100%);
    color: #fff;
    padding: 14px 22px;
    border-radius: 10px;
    margin-bottom: 8px;
    box-shadow: 0 2px 8px rgba(36,78,136,.18);
}}
.app-header .title {{ font-size: 20px; font-weight: 700; letter-spacing:.2px; }}
.app-header .subtitle {{ font-size: 12.5px; opacity:.85; margin-top:2px; }}

/* Хлебные крошки */
.crumbs {{
    color: #6b7a90; font-size: 12.5px; margin: 4px 0 14px 2px;
}}
.crumbs b {{ color: var(--primary); }}

/* Бейдж уровня доступа */
.badge {{
    display:inline-block; font-size:11px; font-weight:600;
    padding:2px 9px; border-radius:11px; margin-left:6px;
}}
.badge-common {{ background:#E3F0FF; color:#1c5aa8; }}
.badge-private {{ background:#FCE8E6; color:#b3261e; }}

/* Карточки виджетов */
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius:10px; }}

/* Первичные кнопки */
.stButton button[kind="primary"] {{
    background: var(--primary); border:0; font-weight:600;
}}

/* Заголовки секций */
h2, h3 {{ color:#1B2A41; }}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


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
    """
    try:
        kind, payload = charts.build_figure(df, cfg)
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
