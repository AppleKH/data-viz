"""Главная страница приложения визуализации данных (аналог DataLens).

Запуск:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from core import storage

st.set_page_config(page_title="Визуализация данных", page_icon="📊", layout="wide")

storage.ensure_dirs()

st.title("📊 Визуализация данных")
st.caption("Загрузка → Обработка → Виджеты → Дашборд")

datasets = storage.list_datasets()
widgets = storage.get_widgets()
dashboards = storage.get_dashboards()

c1, c2, c3 = st.columns(3)
c1.metric("Датасеты", len(datasets))
c2.metric("Виджеты", len(widgets))
c3.metric("Дашборды", len(dashboards))

st.divider()

st.markdown(
    """
### Как пользоваться

Разделы открываются на панели слева 👈

1. **📥 Загрузка данных** — загрузите CSV/Excel, подключитесь к SQL-базе
   или получите данные по REST API/URL. Каждый источник сохраняется как
   именованный датасет.
2. **🔧 Обработка данных** — стройте пайплайн преобразований: смена типов,
   фильтры, заполнение пропусков, группировки и агрегации, вычисляемые столбцы.
   Результат сохраняется в новый датасет.
3. **📊 Виджеты** — создавайте графики (линейные, столбчатые, круговые,
   точечные, гистограммы, KPI, таблицы) поверх любого датасета.
4. **📋 Дашборд** — собирайте виджеты в сетку и просматривайте дашборды целиком.

Всё состояние хранится в каталоге `workspace/` и переживает перезапуск.
"""
)

if not datasets:
    st.info("Пока нет ни одного датасета. Начните с раздела **📥 Загрузка данных**.")
