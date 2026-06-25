"""Общие элементы интерфейса: фирменный стиль, шапка, хлебные крошки.

Стилизовано под АС «Представление данных» Ситуационного центра.
"""
from __future__ import annotations

import streamlit as st

from core import charts

APP_NAME = "Datavisor"
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

/* Логотип должен стоять НАД меню навигации (которое Streamlit ставит вверху) */
[data-testid="stSidebarContent"] {{
    display: flex !important;
    flex-direction: column !important;
}}
[data-testid="stSidebarUserContent"] {{ order: -1 !important; }}

/* Собственный логотип вверху боковой панели */
.dv-logo {{
    display: flex; align-items: center; gap: 11px;
    padding: 14px 6px 6px 6px;
}}
.dv-logo svg {{ width: 36px; height: 36px; flex: none; }}
.dv-logo-text {{
    font-size: 22px; font-weight: 700; letter-spacing: .3px;
    background: linear-gradient(90deg, #C4B5FD, #F9A8D4);
    -webkit-background-clip: text; background-clip: text; color: transparent;
    white-space: nowrap;
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
/* Свёрнутый вид: у логотипа прячем текст, иконку центрируем в полосе */
section[data-testid="stSidebar"][aria-expanded="false"] .dv-logo {{
    justify-content: center !important;
    padding: 14px 0 8px 0 !important;
}}
section[data-testid="stSidebar"][aria-expanded="false"] .dv-logo-text {{
    display: none !important;
}}
section[data-testid="stSidebar"][aria-expanded="false"] .dv-logo svg {{
    width: 28px !important; height: 28px !important;
}}
/* Убираем стрелку «свернуть» под лого в свёрнутой панели */
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarCollapseButton"] {{
    display: none !important;
}}
/* Прячем подписи ссылок и заголовки групп — оставляем только иконки */
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNavLink"] > span:last-child,
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] header {{
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


_LOGO_HTML = """
<div class="dv-logo">
  <svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
    <defs><linearGradient id="dvg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#8B5CF6"/><stop offset="1" stop-color="#EC4899"/>
    </linearGradient></defs>
    <rect x="2" y="2" width="44" height="44" rx="13" fill="url(#dvg)"/>
    <rect x="12" y="25" width="5.5" height="10" rx="2" fill="#fff"/>
    <rect x="21.25" y="19" width="5.5" height="16" rx="2" fill="#fff"/>
    <rect x="30.5" y="13" width="5.5" height="22" rx="2" fill="#fff"/>
    <path d="M14.75 22 L24 16 L33.25 10.5" stroke="#fff" stroke-width="2"
          fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>
    <circle cx="14.75" cy="22" r="2.4" fill="#fff"/>
    <circle cx="24" cy="16" r="2.4" fill="#fff"/>
    <circle cx="33.25" cy="10.5" r="2.4" fill="#fff"/>
  </svg>
  <span class="dv-logo-text">Datavisor</span>
</div>
"""


def sidebar_logo() -> None:
    """Собственный логотип вверху боковой панели (полный контроль вёрстки)."""
    with st.sidebar:
        st.markdown(_LOGO_HTML, unsafe_allow_html=True)


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
        # Без зума: скрываем панель инструментов и отключаем зум колесом.
        st.plotly_chart(payload, width="stretch", key=f"chart_{key}",
                        config={"displayModeBar": False, "scrollZoom": False})
