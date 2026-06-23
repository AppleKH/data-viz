"""Главная страница: сводка, загрузка демо-данных, описание разделов."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core import storage, ui

DEMO_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "sales_demo.csv"
DEMO_NAME = "Демо: продажи 2025"

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

# --------------------------------------------------------------------------- #
# Демо-данные
# --------------------------------------------------------------------------- #
if DEMO_CSV.exists():
    st.subheader("🎬 Демо-данные")
    cols = st.columns([3, 1])
    cols[0].caption(
        "Загрузите готовый датасет продаж за 2025 год (регионы, категории, "
        "каналы, продажи и прибыль) — чтобы сразу опробовать все разделы."
    )
    already = DEMO_NAME in datasets
    if cols[1].button("📥 Загрузить демо" if not already else "🔄 Перезагрузить демо"):
        demo_df = pd.read_csv(DEMO_CSV)
        storage.save_dataset(DEMO_NAME, demo_df, source="demo",
                             meta={"file": DEMO_CSV.name})
        st.success(f"Датасет «{DEMO_NAME}» загружен ({len(demo_df)} строк).")
    if already:
        cols[0].caption(f"✅ Датасет «{DEMO_NAME}» уже загружен.")
    st.divider()

st.markdown(
    """
### Разделы

- **Источники данных** — загрузка из CSV/Excel/JSON, SQL-баз и REST API.
- **Обработка данных** — пайплайн преобразований: типы, фильтры, группировки,
  вычисляемые столбцы.
- **Панели → Виджеты** — гистограммы, круговые и линейные диаграммы, списки,
  показатели, процент выполненных работ, Html, изображения, дата/время.
- **Панели → Дашборды** — сборка виджетов в сетку с темой оформления и
  уровнем доступа (Общий / Личный).

Навигация — на панели слева. Всё состояние хранится в каталоге `workspace/`.
"""
)

if not datasets:
    st.info("Начните с раздела **Источники данных** или загрузите демо-данные выше.")
