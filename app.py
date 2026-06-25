"""Datavisor — платформа визуализации данных на Streamlit.

Точка входа: логотип, оформление и сгруппированная навигация
(«Источники данных», «Обработка», группа «Панели» → Виджеты, Дашборды).

Запуск:  python -m streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from core import storage, ui

st.set_page_config(page_title="Datavisor", page_icon="📊", layout="wide")
storage.ensure_dirs()
ui.inject_css()
ui.sidebar_logo()  # собственный логотип вверху боковой панели

home = st.Page("views/home.py", title="Главная", icon=":material/home:",
               default=True)
sources = st.Page("views/sources.py", title="Источники данных",
                  icon=":material/database:")
transform = st.Page("views/transform.py", title="Обработка данных",
                    icon=":material/tune:")
widgets = st.Page("views/widgets.py", title="Виджеты", icon=":material/widgets:")
dashboards = st.Page("views/dashboards.py", title="Дашборды",
                     icon=":material/dashboard:")

nav = st.navigation({
    "Навигация": [home],
    "Данные": [sources, transform],
    "Панели": [widgets, dashboards],
})
nav.run()
