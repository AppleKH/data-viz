"""Загрузка данных из разных источников: файлы, SQL-базы, REST API/URL."""
from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd


# --------------------------------------------------------------------------- #
# Файлы (CSV / Excel / JSON)
# --------------------------------------------------------------------------- #
def read_file(uploaded_file, *, sep: str = ",", sheet: Any = 0,
              header: int | None = 0) -> pd.DataFrame:
    """Читает загруженный через Streamlit файл по его расширению."""
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()

    if name.endswith((".csv", ".txt", ".tsv")):
        actual_sep = "\t" if name.endswith(".tsv") else sep
        return pd.read_csv(io.BytesIO(data), sep=actual_sep, header=header)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(data), sheet_name=sheet, header=header)
    if name.endswith(".json"):
        return pd.json_normalize(json.loads(data.decode("utf-8")))
    if name.endswith(".parquet"):
        return pd.read_parquet(io.BytesIO(data))
    raise ValueError(f"Неподдерживаемый формат файла: {name}")


def excel_sheet_names(uploaded_file) -> list[str]:
    xls = pd.ExcelFile(io.BytesIO(uploaded_file.getvalue()))
    return xls.sheet_names


# --------------------------------------------------------------------------- #
# SQL-базы
# --------------------------------------------------------------------------- #
def read_sql(connection_string: str, query: str) -> pd.DataFrame:
    """Выполняет SQL-запрос. connection_string — формат SQLAlchemy, напр.:
        postgresql+psycopg2://user:pass@host:5432/db
        mysql+pymysql://user:pass@host:3306/db
        sqlite:///C:/path/to/file.db
    """
    from sqlalchemy import create_engine, text

    engine = create_engine(connection_string)
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)
    finally:
        engine.dispose()


def list_sql_tables(connection_string: str) -> list[str]:
    from sqlalchemy import create_engine, inspect

    engine = create_engine(connection_string)
    try:
        return list(inspect(engine).get_table_names())
    finally:
        engine.dispose()


# --------------------------------------------------------------------------- #
# REST API / URL
# --------------------------------------------------------------------------- #
def read_api(url: str, *, fmt: str = "auto", json_path: str = "",
             headers: dict | None = None, params: dict | None = None,
             timeout: int = 30) -> pd.DataFrame:
    """Загружает данные по URL. fmt: auto|json|csv.

    json_path — путь к вложенному списку через точку, напр. "data.items".
    """
    import requests

    resp = requests.get(url, headers=headers or {}, params=params or {},
                        timeout=timeout)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "").lower()
    if fmt == "auto":
        fmt = "csv" if ("csv" in content_type or url.lower().endswith(".csv")) else "json"

    if fmt == "csv":
        return pd.read_csv(io.StringIO(resp.text))

    payload = resp.json()
    if json_path:
        for key in json_path.split("."):
            payload = payload[key]
    if isinstance(payload, dict):
        payload = [payload]
    return pd.json_normalize(payload)
