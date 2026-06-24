"""Главная страница: сводка и описание разделов."""
from __future__ import annotations

import streamlit as st

from core import storage, ui

ui.app_header()
ui.breadcrumb("Главная")
storage.ensure_dirs()

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
### Разделы

- **Источники данных** — загрузка из CSV/Excel/JSON, SQL-баз и REST API.
- **Обработка данных** — пайплайн преобразований: типы, фильтры, группировки,
  вычисляемые столбцы.
- **Панели → Виджеты** — гистограммы, круговые и линейные диаграммы, списки,
  показатели, процент выполненных работ, Html, изображения, дата/время.
- **Панели → Дашборды** — сборка виджетов в сетку с уровнем доступа
  (Общий / Личный).

Навигация — на панели слева. Всё состояние хранится в каталоге `workspace/`.
"""
)

if not datasets:
    st.info("Начните с раздела **Источники данных** — загрузите свои данные.")
