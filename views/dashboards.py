"""Панель «Дашборды»: конструктор и просмотр дашбордов."""
from __future__ import annotations

import streamlit as st

from core import charts, storage, ui

ui.app_header()
ui.breadcrumb("Главная", "Панели", "Дашборды")
storage.ensure_dirs()

widgets = storage.get_widgets()
widget_by_id = {w["id"]: w for w in widgets}
datasets = storage.list_datasets()


def render_on_dashboard(cfg: dict, theme: str) -> None:
    df = (storage.load_dataset(cfg["dataset"])
          if cfg.get("dataset") in datasets else None)
    if cfg["chart_type"] not in charts.STATIC_TYPES and df is None:
        st.warning(f"«{cfg['name']}»: датасет удалён")
        return
    # Тема дашборда переопределяет тему виджета.
    ui.render_widget({**cfg, "theme": theme}, df, key=f"dash_{cfg['id']}")


tab_view, tab_edit = st.tabs(["👁️ Просмотр", "🛠️ Добавление дашборда"])

# --------------------------------------------------------------------------- #
# Конструктор
# --------------------------------------------------------------------------- #
with tab_edit:
    dashboards = storage.get_dashboards()
    options = ["➕ Новый дашборд"] + [d["name"] for d in dashboards]
    choice = st.selectbox("Дашборд", options, key="edit_choice")

    if choice == "➕ Новый дашборд":
        current = {"id": "", "name": "Новый дашборд", "widgets": [],
                   "columns": 2, "access": "Общий", "theme": "Светлая"}
    else:
        current = next(d for d in dashboards if d["name"] == choice)

    c1, c2, c3 = st.columns([2, 1, 1])
    name = c1.text_input("Название дашборда *", value=current["name"])
    access = c2.selectbox("Уровень доступа", ["Общий", "Личный"],
                          index=0 if current.get("access", "Общий") == "Общий" else 1)
    theme = c3.selectbox("Тема оформления", list(charts.THEMES),
                         index=list(charts.THEMES).index(current.get("theme", "Светлая"))
                         if current.get("theme") in charts.THEMES else 0)
    ncols = st.slider("Столбцов в сетке", 1, 4, current.get("columns", 2))

    if not widgets:
        st.info("Сначала создайте виджеты в разделе **Виджеты**.")
    else:
        chosen = st.multiselect(
            "Виджеты на дашборде",
            options=[w["id"] for w in widgets],
            default=[wid for wid in current.get("widgets", []) if wid in widget_by_id],
            format_func=lambda wid: widget_by_id[wid]["name"],
        )

        b1, b2 = st.columns(2)
        if b1.button("✅ Сохранить дашборд", type="primary"):
            current.update(name=name, columns=ncols, widgets=chosen,
                           access=access, theme=theme)
            storage.save_dashboard(current)
            st.success(f"Дашборд «{name}» сохранён.")
            st.rerun()
        if choice != "➕ Новый дашборд" and b2.button("🗑️ Удалить дашборд"):
            storage.delete_dashboard(current["id"])
            st.rerun()

# --------------------------------------------------------------------------- #
# Просмотр
# --------------------------------------------------------------------------- #
with tab_view:
    dashboards = storage.get_dashboards()
    if not dashboards:
        st.info("Дашбордов пока нет — создайте во вкладке «Добавление дашборда».")
    else:
        names = [d["name"] for d in dashboards]
        sel = st.selectbox("Выберите дашборд", names, key="view_choice")
        dash = next(d for d in dashboards if d["name"] == sel)
        st.markdown(f"### {dash['name']} {ui.access_badge(dash.get('access', 'Общий'))}",
                    unsafe_allow_html=True)

        wids = [wid for wid in dash.get("widgets", []) if wid in widget_by_id]
        if not wids:
            st.info("На дашборде нет виджетов.")
        else:
            theme = dash.get("theme", "Светлая")
            ncols = dash.get("columns", 2)
            grid = st.columns(ncols)
            for i, wid in enumerate(wids):
                with grid[i % ncols]:
                    with st.container(border=True):
                        render_on_dashboard(widget_by_id[wid], theme)
