"""Операции обработки данных над pandas.DataFrame.

Каждая трансформация описывается словарём ``{"op": ..., ...параметры}``.
Список таких словарей образует воспроизводимый пайплайн обработки.
"""
from __future__ import annotations

import pandas as pd

AGG_FUNCS = ["sum", "mean", "median", "min", "max", "count", "nunique", "std"]
DTYPES = ["int", "float", "str", "datetime", "bool", "category"]


def _to_dtype(series: pd.Series, dtype: str) -> pd.Series:
    if dtype == "int":
        return pd.to_numeric(series, errors="coerce").astype("Int64")
    if dtype == "float":
        return pd.to_numeric(series, errors="coerce")
    if dtype == "datetime":
        return pd.to_datetime(series, errors="coerce")
    if dtype == "bool":
        return series.astype("boolean")
    if dtype == "category":
        return series.astype("category")
    return series.astype("string")


def apply_step(df: pd.DataFrame, step: dict) -> pd.DataFrame:
    """Применяет одну трансформацию и возвращает новый DataFrame."""
    op = step["op"]
    df = df.copy()

    if op == "select":
        cols = [c for c in step["columns"] if c in df.columns]
        return df[cols]

    if op == "rename":
        return df.rename(columns=step["mapping"])

    if op == "astype":
        col, dtype = step["column"], step["dtype"]
        df[col] = _to_dtype(df[col], dtype)
        return df

    if op == "filter":
        return _filter(df, step)

    if op == "dropna":
        subset = step.get("columns") or None
        return df.dropna(subset=subset)

    if op == "fillna":
        col, value = step["column"], step["value"]
        method = step.get("method")
        if method == "ffill":
            df[col] = df[col].ffill()
        elif method == "bfill":
            df[col] = df[col].bfill()
        else:
            df[col] = df[col].fillna(value)
        return df

    if op == "drop_duplicates":
        return df.drop_duplicates(subset=step.get("columns") or None)

    if op == "sort":
        return df.sort_values(by=step["columns"],
                              ascending=step.get("ascending", True))

    if op == "groupby":
        return _groupby(df, step)

    if op == "compute":
        # Новый столбец из выражения над df (pandas eval).
        df[step["column"]] = df.eval(step["expr"])
        return df

    if op == "head":
        return df.head(int(step.get("n", 100)))

    raise ValueError(f"Неизвестная операция: {op}")


def _filter(df: pd.DataFrame, step: dict) -> pd.DataFrame:
    col, comp, value = step["column"], step["comparator"], step.get("value")
    s = df[col]
    if comp == "==":
        return df[s == value]
    if comp == "!=":
        return df[s != value]
    if comp == ">":
        return df[pd.to_numeric(s, errors="coerce") > float(value)]
    if comp == ">=":
        return df[pd.to_numeric(s, errors="coerce") >= float(value)]
    if comp == "<":
        return df[pd.to_numeric(s, errors="coerce") < float(value)]
    if comp == "<=":
        return df[pd.to_numeric(s, errors="coerce") <= float(value)]
    if comp == "contains":
        return df[s.astype("string").str.contains(str(value), na=False)]
    if comp == "in":
        values = value if isinstance(value, list) else [value]
        return df[s.isin(values)]
    if comp == "isna":
        return df[s.isna()]
    if comp == "notna":
        return df[s.notna()]
    raise ValueError(f"Неизвестный оператор фильтра: {comp}")


def _groupby(df: pd.DataFrame, step: dict) -> pd.DataFrame:
    by = step["by"]
    aggs: dict[str, list[str]] = step["aggregations"]  # {col: [funcs]}
    grouped = df.groupby(by, dropna=False).agg(aggs)
    # Сглаживаем мультииндекс в плоские имена столбцов.
    grouped.columns = [f"{c}_{f}" for c, f in grouped.columns]
    return grouped.reset_index()


def apply_pipeline(df: pd.DataFrame, pipeline: list[dict]) -> pd.DataFrame:
    for step in pipeline:
        df = apply_step(df, step)
    return df


def describe_step(step: dict) -> str:
    """Человекочитаемое описание шага для UI."""
    op = step["op"]
    if op == "select":
        return f"Выбрать столбцы: {', '.join(step['columns'])}"
    if op == "rename":
        pairs = ", ".join(f"{k}→{v}" for k, v in step["mapping"].items())
        return f"Переименовать: {pairs}"
    if op == "astype":
        return f"Тип «{step['column']}» → {step['dtype']}"
    if op == "filter":
        return f"Фильтр: {step['column']} {step['comparator']} {step.get('value', '')}"
    if op == "dropna":
        return f"Удалить пустые ({', '.join(step.get('columns') or ['все'])})"
    if op == "fillna":
        return f"Заполнить пустые в «{step['column']}»"
    if op == "drop_duplicates":
        return "Удалить дубликаты"
    if op == "sort":
        return f"Сортировка по {', '.join(step['columns'])}"
    if op == "groupby":
        return f"Группировка по {', '.join(step['by'])}"
    if op == "compute":
        return f"Новый столбец «{step['column']}» = {step['expr']}"
    if op == "head":
        return f"Первые {step.get('n', 100)} строк"
    return op
