"""Раздел «Источники данных»: загрузка из файлов, SQL-баз и REST API."""
from __future__ import annotations

import streamlit as st

from core import data_sources as ds
from core import storage, ui

ui.breadcrumb("Главная", "Источники данных")
storage.ensure_dirs()

tab_file, tab_sql, tab_api, tab_manage = st.tabs(
    ["📄 Файл", "🗄️ SQL-база", "🌐 REST API / URL", "🗂️ Мои датасеты"]
)

# --------------------------------------------------------------------------- #
# Файл
# --------------------------------------------------------------------------- #
with tab_file:
    uploaded = st.file_uploader(
        "Выберите файл", type=["csv", "tsv", "txt", "xlsx", "xls", "json", "parquet"]
    )
    if uploaded:
        name = uploaded.name.lower()
        sep, sheet, header = ",", 0, 0
        cc = st.columns(3)
        if name.endswith((".csv", ".txt")):
            sep = cc[0].text_input("Разделитель", value=",")
        if name.endswith((".xlsx", ".xls")):
            try:
                sheets = ds.excel_sheet_names(uploaded)
                sheet = cc[0].selectbox("Лист", sheets)
            except Exception as e:  # noqa: BLE001
                st.warning(f"Не удалось прочитать список листов: {e}")
        has_header = cc[1].checkbox("Первая строка — заголовки", value=True)
        header = 0 if has_header else None

        if st.button("Предпросмотр", key="prev_file"):
            try:
                st.session_state["_loaded_df"] = ds.read_file(
                    uploaded, sep=sep, sheet=sheet, header=header
                )
            except Exception as e:  # noqa: BLE001
                st.error(f"Ошибка чтения: {e}")

        df = st.session_state.get("_loaded_df")
        if df is not None:
            st.dataframe(df.head(50), width="stretch")
            st.caption(f"{len(df)} строк × {df.shape[1]} столбцов")
            default_name = uploaded.name.rsplit(".", 1)[0]
            dname = st.text_input("Имя датасета", value=default_name, key="fname")
            if st.button("💾 Сохранить датасет", key="save_file", type="primary"):
                storage.save_dataset(dname, df, source="file",
                                     meta={"filename": uploaded.name})
                st.success(f"Сохранено как «{dname}»")
                st.session_state.pop("_loaded_df", None)

# --------------------------------------------------------------------------- #
# SQL
# --------------------------------------------------------------------------- #
with tab_sql:
    st.markdown(
        "Строка подключения в формате **SQLAlchemy**, например:\n"
        "- `postgresql+psycopg2://user:pass@host:5432/db`\n"
        "- `mysql+pymysql://user:pass@host:3306/db`\n"
        "- `sqlite:///C:/путь/к/файлу.db`"
    )
    conn = st.text_input("Строка подключения", key="sql_conn",
                         placeholder="postgresql+psycopg2://...")
    if conn and st.button("Показать таблицы", key="sql_tables"):
        try:
            tables = ds.list_sql_tables(conn)
            st.info("Таблицы: " + (", ".join(tables) if tables else "нет"))
        except Exception as e:  # noqa: BLE001
            st.error(f"Ошибка подключения: {e}")

    query = st.text_area("SQL-запрос", value="SELECT * FROM ... LIMIT 1000",
                         key="sql_query", height=120)
    if conn and query and st.button("Выполнить запрос", key="run_sql"):
        try:
            st.session_state["_sql_df"] = ds.read_sql(conn, query)
        except Exception as e:  # noqa: BLE001
            st.error(f"Ошибка запроса: {e}")

    df = st.session_state.get("_sql_df")
    if df is not None:
        st.dataframe(df.head(50), width="stretch")
        st.caption(f"{len(df)} строк × {df.shape[1]} столбцов")
        dname = st.text_input("Имя датасета", value="sql_result", key="sqlname")
        if st.button("💾 Сохранить датасет", key="save_sql", type="primary"):
            storage.save_dataset(dname, df, source="sql")
            st.success(f"Сохранено как «{dname}»")
            st.session_state.pop("_sql_df", None)

# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
with tab_api:
    url = st.text_input("URL", key="api_url",
                        placeholder="https://api.example.com/data")
    cc = st.columns(2)
    fmt = cc[0].selectbox("Формат", ["auto", "json", "csv"], key="api_fmt")
    json_path = cc[1].text_input("Путь к списку в JSON (через точку)",
                                 key="api_path", placeholder="data.items")
    headers_raw = st.text_input("Заголовки (key:value через ;)", key="api_headers",
                                placeholder="Authorization: Bearer xxx")
    if url and st.button("Загрузить", key="run_api"):
        headers = {}
        for part in filter(None, (h.strip() for h in headers_raw.split(";"))):
            if ":" in part:
                k, v = part.split(":", 1)
                headers[k.strip()] = v.strip()
        try:
            st.session_state["_api_df"] = ds.read_api(
                url, fmt=fmt, json_path=json_path.strip(), headers=headers
            )
        except Exception as e:  # noqa: BLE001
            st.error(f"Ошибка загрузки: {e}")

    df = st.session_state.get("_api_df")
    if df is not None:
        st.dataframe(df.head(50), width="stretch")
        st.caption(f"{len(df)} строк × {df.shape[1]} столбцов")
        dname = st.text_input("Имя датасета", value="api_result", key="apiname")
        if st.button("💾 Сохранить датасет", key="save_api", type="primary"):
            storage.save_dataset(dname, df, source="api", meta={"url": url})
            st.success(f"Сохранено как «{dname}»")
            st.session_state.pop("_api_df", None)

# --------------------------------------------------------------------------- #
# Управление
# --------------------------------------------------------------------------- #
with tab_manage:
    datasets = storage.list_datasets()
    if not datasets:
        st.info("Датасетов пока нет.")
    for name, info in datasets.items():
        with st.expander(f"**{name}** — {info['rows']} × {info['cols']} "
                         f"({info['source']}, {info['updated']})"):
            st.write("Столбцы:", ", ".join(info["columns"]))
            st.dataframe(storage.load_dataset(name).head(20),
                         width="stretch")
            d1, d2 = st.columns([3, 1])
            new_name = d1.text_input("Переименовать", value=name, key=f"rn_{name}")
            if d1.button("Переименовать", key=f"rnbtn_{name}"):
                storage.rename_dataset(name, new_name)
                st.rerun()
            if d2.button("🗑️ Удалить", key=f"del_{name}"):
                storage.delete_dataset(name)
                st.rerun()
