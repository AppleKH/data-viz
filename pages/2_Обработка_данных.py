"""Раздел 2. Обработка данных — построение пайплайна преобразований."""
from __future__ import annotations

import streamlit as st

from core import storage
from core import transforms as tf

st.set_page_config(page_title="Обработка данных", page_icon="🔧", layout="wide")
storage.ensure_dirs()

st.title("🔧 Обработка данных")

datasets = storage.list_datasets()
if not datasets:
    st.info("Сначала загрузите данные в разделе **📥 Загрузка данных**.")
    st.stop()

source = st.selectbox("Исходный датасет", list(datasets))

# Пайплайн храним в session_state, привязывая к выбранному датасету.
pipe_key = f"pipeline::{source}"
pipeline: list[dict] = st.session_state.setdefault(pipe_key, [])

base_df = storage.load_dataset(source)

# Предпросчёт результата пайплайна для подсказок по столбцам.
try:
    current_df = tf.apply_pipeline(base_df, pipeline)
    pipe_error = None
except Exception as e:  # noqa: BLE001
    current_df = base_df
    pipe_error = str(e)

columns = list(current_df.columns)

st.divider()
left, right = st.columns([1, 1])

# --------------------------------------------------------------------------- #
# Левая колонка — добавление шагов
# --------------------------------------------------------------------------- #
with left:
    st.subheader("Добавить шаг")
    op = st.selectbox(
        "Операция",
        ["filter", "astype", "rename", "select", "dropna", "fillna",
         "drop_duplicates", "sort", "groupby", "compute", "head"],
        format_func=lambda o: {
            "filter": "Фильтр строк", "astype": "Изменить тип столбца",
            "rename": "Переименовать столбцы", "select": "Выбрать столбцы",
            "dropna": "Удалить пустые", "fillna": "Заполнить пустые",
            "drop_duplicates": "Удалить дубликаты", "sort": "Сортировка",
            "groupby": "Группировка и агрегация", "compute": "Вычисляемый столбец",
            "head": "Первые N строк",
        }[o],
    )

    step: dict | None = None

    if op == "filter":
        col = st.selectbox("Столбец", columns, key="f_col")
        comp = st.selectbox("Оператор",
                            ["==", "!=", ">", ">=", "<", "<=", "contains", "in",
                             "isna", "notna"], key="f_comp")
        value = None
        if comp == "in":
            value = [v.strip() for v in st.text_input("Значения через запятую",
                     key="f_vals").split(",") if v.strip()]
        elif comp not in ("isna", "notna"):
            value = st.text_input("Значение", key="f_val")
        step = {"op": "filter", "column": col, "comparator": comp, "value": value}

    elif op == "astype":
        col = st.selectbox("Столбец", columns, key="t_col")
        dtype = st.selectbox("Новый тип", tf.DTYPES, key="t_dtype")
        step = {"op": "astype", "column": col, "dtype": dtype}

    elif op == "rename":
        col = st.selectbox("Столбец", columns, key="r_col")
        new = st.text_input("Новое имя", key="r_new")
        if new:
            step = {"op": "rename", "mapping": {col: new}}

    elif op == "select":
        cols = st.multiselect("Оставить столбцы", columns, default=columns, key="s_cols")
        step = {"op": "select", "columns": cols}

    elif op == "dropna":
        cols = st.multiselect("Учитывать столбцы (пусто = все)", columns, key="dn_cols")
        step = {"op": "dropna", "columns": cols}

    elif op == "fillna":
        col = st.selectbox("Столбец", columns, key="fn_col")
        method = st.selectbox("Способ", ["значение", "ffill", "bfill"], key="fn_m")
        if method == "значение":
            val = st.text_input("Заполнить значением", key="fn_val")
            step = {"op": "fillna", "column": col, "value": val}
        else:
            step = {"op": "fillna", "column": col, "value": None, "method": method}

    elif op == "drop_duplicates":
        cols = st.multiselect("По столбцам (пусто = все)", columns, key="dd_cols")
        step = {"op": "drop_duplicates", "columns": cols}

    elif op == "sort":
        cols = st.multiselect("Сортировать по", columns, key="so_cols")
        asc = st.checkbox("По возрастанию", value=True, key="so_asc")
        if cols:
            step = {"op": "sort", "columns": cols, "ascending": asc}

    elif op == "groupby":
        by = st.multiselect("Группировать по", columns, key="g_by")
        agg_cols = st.multiselect("Агрегировать столбцы",
                                  [c for c in columns if c not in by], key="g_cols")
        funcs = st.multiselect("Функции", tf.AGG_FUNCS, default=["sum"], key="g_funcs")
        if by and agg_cols and funcs:
            step = {"op": "groupby", "by": by,
                    "aggregations": {c: funcs for c in agg_cols}}

    elif op == "compute":
        new = st.text_input("Имя нового столбца", key="c_name")
        expr = st.text_input("Выражение (pandas eval), напр. `price * qty`",
                             key="c_expr")
        if new and expr:
            step = {"op": "compute", "column": new, "expr": expr}

    elif op == "head":
        n = st.number_input("N строк", min_value=1, value=100, key="h_n")
        step = {"op": "head", "n": int(n)}

    if st.button("➕ Добавить шаг", type="primary", disabled=step is None):
        pipeline.append(step)
        st.rerun()

# --------------------------------------------------------------------------- #
# Правая колонка — текущий пайплайн
# --------------------------------------------------------------------------- #
with right:
    st.subheader("Пайплайн обработки")
    if not pipeline:
        st.caption("Шагов пока нет — данные передаются как есть.")
    for i, s in enumerate(pipeline):
        cols = st.columns([6, 1, 1])
        cols[0].write(f"{i + 1}. {tf.describe_step(s)}")
        if cols[1].button("↑", key=f"up_{i}", disabled=i == 0):
            pipeline[i - 1], pipeline[i] = pipeline[i], pipeline[i - 1]
            st.rerun()
        if cols[2].button("✖", key=f"rm_{i}"):
            pipeline.pop(i)
            st.rerun()
    if pipeline and st.button("Очистить пайплайн"):
        st.session_state[pipe_key] = []
        st.rerun()

st.divider()
if pipe_error:
    st.error(f"Ошибка в пайплайне: {pipe_error}")
else:
    st.subheader("Результат")
    st.dataframe(current_df.head(100), use_container_width=True)
    st.caption(f"{len(current_df)} строк × {current_df.shape[1]} столбцов")

    cc = st.columns([3, 1])
    out_name = cc[0].text_input("Сохранить результат как", value=f"{source}_обработан")
    if cc[1].button("💾 Сохранить", type="primary", disabled=bool(pipe_error)):
        storage.save_dataset(out_name, current_df, source="transform",
                             meta={"from": source, "pipeline": pipeline})
        st.success(f"Сохранено как «{out_name}»")
