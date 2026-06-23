"""Раздел 4. Создание и просмотр дашбордов — сетка из виджетов."""
from __future__ import annotations

import streamlit as st

from core import charts
from core import storage

st.set_page_config(page_title="Дашборд", page_icon="📋", layout="wide")
storage.ensure_dirs()

st.title("📋 Дашборды")

widgets = storage.get_widgets()
widget_by_id = {w["id"]: w for w in widgets}
datasets = storage.list_datasets()


def render_widget(cfg: dict) -> None:
    if cfg["dataset"] not in datasets:
        st.warning(f"«{cfg['name']}»: датасет удалён")
        return
    df = storage.load_dataset(cfg["dataset"])
    try:
        kind, payload = charts.build_figure(df, cfg)
    except Exception as e:  # noqa: BLE001
        st.error(f"{cfg['name']}: {e}")
        return
    if kind == "metric":
        st.metric(cfg.get("title") or cfg["name"], payload)
    elif kind == "table":
        st.dataframe(payload, use_container_width=True)
    else:
        st.plotly_chart(payload, use_container_width=True, key=f"dash_{cfg['id']}")


tab_view, tab_edit = st.tabs(["👁️ Просмотр", "🛠️ Конструктор"])

# --------------------------------------------------------------------------- #
# Конструктор
# --------------------------------------------------------------------------- #
with tab_edit:
    dashboards = storage.get_dashboards()
    options = ["➕ Новый дашборд"] + [d["name"] for d in dashboards]
    choice = st.selectbox("Дашборд", options, key="edit_choice")

    if choice == "➕ Новый дашборд":
        current = {"id": "", "name": "Новый дашборд", "widgets": [], "columns": 2}
    else:
        current = next(d for d in dashboards if d["name"] == choice)

    name = st.text_input("Название", value=current["name"])
    ncols = st.slider("Столбцов в сетке", 1, 4, current.get("columns", 2))

    if not widgets:
        st.info("Сначала создайте виджеты в разделе **📊 Виджеты**.")
    else:
        chosen = st.multiselect(
            "Виджеты на дашборде",
            options=[w["id"] for w in widgets],
            default=[wid for wid in current.get("widgets", []) if wid in widget_by_id],
            format_func=lambda wid: widget_by_id[wid]["name"],
        )

        c1, c2 = st.columns(2)
        if c1.button("💾 Сохранить дашборд", type="primary"):
            current.update(name=name, columns=ncols, widgets=chosen)
            storage.save_dashboard(current)
            st.success(f"Дашборд «{name}» сохранён.")
            st.rerun()
        if choice != "➕ Новый дашборд" and c2.button("🗑️ Удалить дашборд"):
            storage.delete_dashboard(current["id"])
            st.rerun()

# --------------------------------------------------------------------------- #
# Просмотр
# --------------------------------------------------------------------------- #
with tab_view:
    dashboards = storage.get_dashboards()
    if not dashboards:
        st.info("Дашбордов пока нет — создайте в **🛠️ Конструкторе**.")
        st.stop()

    names = [d["name"] for d in dashboards]
    sel = st.selectbox("Выберите дашборд", names, key="view_choice")
    dash = next(d for d in dashboards if d["name"] == sel)

    wids = [wid for wid in dash.get("widgets", []) if wid in widget_by_id]
    if not wids:
        st.info("На дашборде нет виджетов.")
        st.stop()

    ncols = dash.get("columns", 2)
    grid = st.columns(ncols)
    for i, wid in enumerate(wids):
        with grid[i % ncols]:
            with st.container(border=True):
                render_widget(widget_by_id[wid])
