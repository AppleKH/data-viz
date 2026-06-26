"""Панель «Виджеты»: создание, просмотр и редактирование виджетов."""
from __future__ import annotations

import streamlit as st

from core import charts, storage, ui

ui.breadcrumb("Главная", "Панели", "Виджеты")
storage.ensure_dirs()

datasets = storage.list_datasets()

tab_new, tab_list = st.tabs(["➕ Добавление виджета", "🗂️ Список виджетов"])

# --------------------------------------------------------------------------- #
# Добавление / редактирование
# --------------------------------------------------------------------------- #
with tab_new:
    edit_id = st.session_state.get("_edit_widget")
    editing = storage.get_widget(edit_id) if edit_id else None
    if editing:
        st.info(f"Редактирование виджета «{editing['name']}».")
        if st.button("Отменить редактирование"):
            st.session_state.pop("_edit_widget", None)
            st.rerun()

    c1, c2, c3 = st.columns([2, 2, 1])
    name = c1.text_input("Название виджета *",
                         value=editing["name"] if editing else "Новый виджет")
    chart_keys = list(charts.CHART_TYPES)
    default_chart = editing["chart_type"] if editing else "bar"
    chart_type = c2.selectbox(
        "Тип виджета *", chart_keys,
        index=chart_keys.index(default_chart) if default_chart in chart_keys else 0,
        format_func=lambda k: charts.CHART_TYPES[k],
    )
    access = c3.selectbox("Уровень доступа", ["Общий", "Личный"],
                          index=0 if not editing else
                          (0 if editing.get("access", "Общий") == "Общий" else 1))

    st.caption("Цветовая тема графика следует теме приложения "
               "(переключается в меню «⋮» → Settings → Appearance).")

    cfg: dict = {
        "id": editing["id"] if editing else "",
        "name": name,
        "title": name,
        "chart_type": chart_type,
        "access": access,
        "dataset": editing.get("dataset", "") if editing else "",
    }

    df = None
    is_static = chart_type in charts.STATIC_TYPES

    if is_static:
        # --- Статические виджеты ----------------------------------------- #
        if chart_type == "html":
            cfg["html"] = st.text_area(
                "HTML / Markdown содержимое",
                value=editing.get("html", "") if editing else "<b>Текст</b>",
                height=160)
        elif chart_type == "image":
            cfg["image_url"] = st.text_input(
                "URL изображения",
                value=editing.get("image_url", "") if editing else "")
        elif chart_type == "datetime":
            st.caption("Виджет показывает текущие дату и время.")
    else:
        # --- Виджеты на данных ------------------------------------------- #
        if not datasets:
            st.warning("Нет ни одного датасета. Загрузите данные в разделе "
                       "**Источники данных**.")
        else:
            ds_names = list(datasets)
            default_ds = (editing["dataset"] if editing
                          and editing.get("dataset") in datasets else ds_names[0])
            dataset = st.selectbox("Датасет", ds_names,
                                   index=ds_names.index(default_ds))
            df = storage.load_dataset(dataset)
            columns = list(df.columns)
            cfg["dataset"] = dataset

            if chart_type == "table":
                st.caption("«Список» показывает датасет целиком (с учётом обработки).")
            elif chart_type in ("metric", "gauge"):
                col = st.selectbox("Столбец-показатель", columns)
                agg = st.selectbox("Агрегация",
                                   [a for a in charts.AGGS if a != "none"],
                                   format_func=lambda a: charts.AGGS[a])
                cfg.update(y=[col], agg=agg)
                if chart_type == "gauge":
                    g1, g2, g3 = st.columns(3)
                    cfg["gauge_max"] = g1.number_input("Максимум шкалы", value=100.0)
                    cfg["gauge_target"] = g2.number_input("Целевое значение",
                                                          value=80.0)
                    cfg["gauge_suffix"] = g3.text_input("Единица", value=" %")
            else:
                cc = st.columns(3)
                if chart_type in ("pie", "histogram"):
                    x = cc[0].selectbox("Категория / ось X", columns)
                    y_sel = cc[1].selectbox("Значение", ["—"] + columns)
                    ys = [] if y_sel == "—" else [y_sel]
                else:
                    x = cc[0].selectbox("Ось X", columns)
                    ys = cc[1].multiselect("Ось Y (значения)",
                                           [c for c in columns if c != x])
                color_sel = cc[2].selectbox("Разбивка по цвету", ["—"] + columns)
                agg = st.selectbox("Агрегация", list(charts.AGGS),
                                   format_func=lambda a: charts.AGGS[a])
                cfg.update(x=x, y=ys,
                           color=None if color_sel == "—" else color_sel, agg=agg)

    st.divider()
    st.subheader("Предпросмотр")
    if not is_static and not datasets:
        st.caption("Недоступно без датасета.")
    else:
        ui.render_widget(cfg, df, key="preview")

    can_save = bool(name) and (is_static or bool(datasets))
    if st.button("✅ Добавить виджет", type="primary", disabled=not can_save):
        saved = storage.save_widget(cfg)
        st.session_state.pop("_edit_widget", None)
        st.success(f"Виджет «{saved['name']}» сохранён.")

# --------------------------------------------------------------------------- #
# Список виджетов
# --------------------------------------------------------------------------- #
with tab_list:
    widgets = storage.get_widgets()
    query = st.text_input("🔎 Поиск виджетов", placeholder="по названию")
    if query:
        widgets = [w for w in widgets if query.lower() in w["name"].lower()]
    if not widgets:
        st.info("Виджетов пока нет.")
    for w in widgets:
        with st.container(border=True):
            st.markdown(
                f"**{w['name']}** · {charts.CHART_TYPES.get(w['chart_type'], w['chart_type'])}"
                f"{' · `' + w['dataset'] + '`' if w.get('dataset') else ''}"
                f"{ui.access_badge(w.get('access', 'Общий'))}",
                unsafe_allow_html=True)
            df = (storage.load_dataset(w["dataset"])
                  if w.get("dataset") in datasets else None)
            if w["chart_type"] not in charts.STATIC_TYPES and df is None:
                st.warning("Датасет виджета удалён.")
            else:
                ui.render_widget(w, df, key=w["id"])
            a, b = st.columns(2)
            if a.button("✏️ Редактировать", key=f"edit_{w['id']}"):
                st.session_state["_edit_widget"] = w["id"]
                st.rerun()
            if b.button("🗑️ Удалить", key=f"delw_{w['id']}"):
                storage.delete_widget(w["id"])
                st.rerun()
