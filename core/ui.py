"""Общие элементы интерфейса: фирменный стиль, шапка, хлебные крошки.

Стилизовано под АС «Представление данных» Ситуационного центра.
"""
from __future__ import annotations

import streamlit as st

from core import charts

APP_NAME = "Представление данных"
APP_SUBTITLE = "Аналитическая платформа · визуализация данных"
PRIMARY = "#2E6CB5"

# Доступные режимы оформления приложения и соответствующий шаблон Plotly.
APPEARANCES = {"Светлая": "plotly_white", "Тёмная": "plotly_dark"}

_BASE_CSS = f"""
<style>
:root {{ --primary: {PRIMARY}; }}

/* Шапка приложения (одинакова в обоих режимах) */
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
.crumbs {{ font-size: 12.5px; margin: 4px 0 14px 2px; }}
.crumbs b {{ color: var(--primary); }}

/* Бейдж уровня доступа */
.badge {{
    display:inline-block; font-size:11px; font-weight:600;
    padding:2px 9px; border-radius:11px; margin-left:6px;
}}
.badge-common {{ background:#E3F0FF; color:#1c5aa8; }}
.badge-private {{ background:#FCE8E6; color:#b3261e; }}

[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius:10px; }}
.stButton button[kind="primary"] {{
    background: var(--primary); border:0; font-weight:600;
}}
</style>
"""

# Светлый режим: мягкий фон, тёмный текст крошек/заголовков.
_LIGHT_CSS = """
<style>
.crumbs { color:#6b7a90; }
h2, h3 { color:#1B2A41; }
</style>
"""

# Тёмный режим: переопределяем фон/текст основных контейнеров Streamlit.
_DARK_CSS = """
<style>
.stApp { background-color:#0E1117; }
[data-testid="stHeader"] { background:rgba(0,0,0,0); }
section[data-testid="stSidebar"] { background-color:#161922; }

.stApp, .stMarkdown, p, li, label, span, small,
h1, h2, h3, h4, h5, h6,
[data-testid="stMetricValue"], [data-testid="stMetricLabel"],
[data-testid="stWidgetLabel"] p { color:#E6E9EF !important; }

.crumbs { color:#9aa7bd !important; }

/* Поля ввода и селекторы */
.stTextInput input, .stNumberInput input, .stTextArea textarea,
[data-baseweb="select"] > div, [data-baseweb="input"] > div {
    background-color:#1E222B !important; color:#E6E9EF !important;
}
/* Карточки/границы и таблицы */
[data-testid="stVerticalBlockBorderWrapper"] { border-color:#2A2F3A !important; }
[data-testid="stDataFrame"] { background-color:#1A1D24; }
/* Вкладки */
.stTabs [data-baseweb="tab"] { color:#cdd5e3; }
</style>
"""


def appearance() -> str:
    """Текущий режим оформления приложения (Светлая/Тёмная)."""
    return st.session_state.get("appearance", "Светлая")


def appearance_control() -> None:
    """Переключатель оформления в боковом меню. Вызывать до inject_css()."""
    with st.sidebar:
        st.radio("🎨 Оформление", list(APPEARANCES), key="appearance",
                 horizontal=True)


def inject_css() -> None:
    st.markdown(_BASE_CSS, unsafe_allow_html=True)
    mode = appearance()
    st.markdown(_DARK_CSS if mode == "Тёмная" else _LIGHT_CSS,
                unsafe_allow_html=True)


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
