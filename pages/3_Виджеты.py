"""Раздел 3. Создание виджетов (графиков) поверх датасетов."""
from __future__ import annotations

import streamlit as st

from core import charts
from core import storage

st.set_page_config(page_title="Виджеты", page_icon="📊", layout="wide")
storage.ensure_dirs()

st.title("📊 Виджеты")

datasets = storage.list_datasets()
if not datasets:
    st.info("Сначала загрузите данные в разделе **📥 Загрузка данных**.")
    st.stop()


def render_widget(cfg: dict, df, *, key: str) -> None:
    """Рисует виджет по конфигурации внутри текущего контейнера.

    ``key`` — уникальный префикс, чтобы у одинаковых графиков не совпадали
    авто-сгенерированные ID Streamlit.
    """
    try:
        kind, payload = charts.build_figure(df, cfg)
    except Exception as e:  # noqa: BLE001
        st.error(f"Ошибка построения: {e}")
        return
    if kind == "metric":
        st.metric(cfg.get("title") or cfg.get("name", ""), payload)
    elif kind == "table":
        st.dataframe(payload, use_container_width=True, key=f"tbl_{key}")
    else:
        st.plotly_chart(payload, use_container_width=True, key=f"chart_{key}")


tab_new, tab_list = st.tabs(["➕ Создать виджет", "🗂️ Мои виджеты"])

# --------------------------------------------------------------------------- #
# Создание / редактирование
# --------------------------------------------------------------------------- #
with tab_new:
    edit_id = st.session_state.get("_edit_widget")
    editing = storage.get_widget(edit_id) if edit_id else None
    if editing:
        st.info(f"Редактирование виджета «{editing['name']}». "
                "Очистить — кнопкой ниже.")
        if st.button("Отменить редактирование"):
            st.session_state.pop("_edit_widget", None)
            st.rerun()

    ds_names = list(datasets)
    default_ds = editing["dataset"] if editing and editing["dataset"] in datasets else ds_names[0]
    dataset = st.selectbox("Датасет", ds_names, index=ds_names.index(default_ds))
    df = storage.load_dataset(dataset)
    columns = list(df.columns)

    c1, c2 = st.columns(2)
    name = c1.text_input("Название виджета",
                         value=editing["name"] if editing else "Новый виджет")
    chart_keys = list(charts.CHART_TYPES)
    default_chart = editing["chart_type"] if editing else "bar"
    chart_type = c2.selectbox(
        "Тип графика", chart_keys,
        index=chart_keys.index(default_chart),
        format_func=lambda k: charts.CHART_TYPES[k],
    )

    cfg: dict = {
        "id": editing["id"] if editing else "",
        "name": name,
        "dataset": dataset,
        "chart_type": chart_type,
        "title": name,
    }

    if chart_type == "table":
        st.caption("Таблица показывает датасет целиком (учитывая обработку).")
    elif chart_type == "metric":
        col = st.selectbox("Столбец-показатель", columns)
        agg = st.selectbox("Агрегация", [a for a in charts.AGGS if a != "none"],
                           format_func=lambda a: charts.AGGS[a])
        cfg.update(y=[col], agg=agg)
    else:
        cc = st.columns(3)
        if chart_type in ("pie", "histogram"):
            x = cc[0].selectbox("Категория / ось X", columns)
            y_opts = ["—"] + columns
            y_sel = cc[1].selectbox("Значение", y_opts)
            ys = [] if y_sel == "—" else [y_sel]
        else:
            x = cc[0].selectbox("Ось X", columns)
            ys = cc[1].multiselect("Ось Y (значения)",
                                   [c for c in columns if c != x])
        color_sel = cc[2].selectbox("Разбивка по цвету", ["—"] + columns)
        color = None if color_sel == "—" else color_sel
        agg = st.selectbox("Агрегация", list(charts.AGGS),
                           format_func=lambda a: charts.AGGS[a])
        cfg.update(x=x, y=ys, color=color, agg=agg)

    st.divider()
    st.subheader("Предпросмотр")
    render_widget(cfg, df, key="preview")

    if st.button("💾 Сохранить виджет", type="primary"):
        saved = storage.save_widget(cfg)
        st.session_state.pop("_edit_widget", None)
        st.success(f"Виджет «{saved['name']}» сохранён.")

# --------------------------------------------------------------------------- #
# Список виджетов
# --------------------------------------------------------------------------- #
with tab_list:
    widgets = storage.get_widgets()
    if not widgets:
        st.info("Виджетов пока нет.")
    for w in widgets:
        with st.container(border=True):
            st.markdown(f"**{w['name']}** · {charts.CHART_TYPES.get(w['chart_type'], w['chart_type'])} "
                        f"· датасет: `{w['dataset']}`")
            if w["dataset"] in datasets:
                render_widget(w, storage.load_dataset(w["dataset"]), key=w["id"])
            else:
                st.warning("Датасет виджета удалён.")
            a, b = st.columns(2)
            if a.button("✏️ Редактировать", key=f"edit_{w['id']}"):
                st.session_state["_edit_widget"] = w["id"]
                st.rerun()
            if b.button("🗑️ Удалить", key=f"delw_{w['id']}"):
                storage.delete_widget(w["id"])
                st.rerun()
