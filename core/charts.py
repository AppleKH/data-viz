"""Построение графиков (виджетов) из конфигурации с помощью Plotly Express."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CHART_TYPES = {
    "line": "Линейный",
    "bar": "Столбчатый",
    "area": "С областями",
    "scatter": "Точечный",
    "pie": "Круговой",
    "histogram": "Гистограмма",
    "box": "Ящик с усами",
    "table": "Таблица",
    "metric": "Показатель (KPI)",
}

AGGS = {
    "none": "без агрегации",
    "sum": "сумма",
    "mean": "среднее",
    "median": "медиана",
    "min": "минимум",
    "max": "максимум",
    "count": "количество",
    "nunique": "уникальные",
}


def _aggregate(df: pd.DataFrame, x: str, ys: list[str], color: str | None,
               agg: str) -> pd.DataFrame:
    if agg == "none" or not x:
        return df
    group_cols = [c for c in [x, color] if c]
    if not group_cols:
        return df
    if agg == "count":
        out = df.groupby(group_cols, dropna=False).size().reset_index(name="count")
        return out
    valid_ys = [y for y in ys if y in df.columns]
    if not valid_ys:
        return df
    return df.groupby(group_cols, dropna=False)[valid_ys].agg(agg).reset_index()


def build_figure(df: pd.DataFrame, cfg: dict):
    """Строит Plotly-фигуру (или возвращает ('metric', value) / ('table', df))."""
    chart = cfg.get("chart_type", "bar")
    x = cfg.get("x")
    ys = cfg.get("y") or []
    if isinstance(ys, str):
        ys = [ys]
    color = cfg.get("color") or None
    agg = cfg.get("agg", "none")
    title = cfg.get("title") or cfg.get("name", "")

    if chart == "table":
        return ("table", df)

    if chart == "metric":
        col = ys[0] if ys else (x or (df.columns[0] if len(df.columns) else None))
        if col is None or col not in df.columns:
            return ("metric", "—")
        series = pd.to_numeric(df[col], errors="coerce")
        func = agg if agg != "none" else "sum"
        value = getattr(series, func)() if func != "count" else series.count()
        return ("metric", value)

    plot_df = _aggregate(df, x, ys, color, agg)
    y = "count" if (agg == "count") else (ys[0] if ys else None)
    y_multi = ys if (agg != "count" and len(ys) > 1) else y

    common = dict(title=title)
    if color:
        common["color"] = color

    if chart == "line":
        fig = px.line(plot_df, x=x, y=y_multi, markers=True, **common)
    elif chart == "bar":
        fig = px.bar(plot_df, x=x, y=y_multi, barmode="group", **common)
    elif chart == "area":
        fig = px.area(plot_df, x=x, y=y_multi, **common)
    elif chart == "scatter":
        fig = px.scatter(plot_df, x=x, y=y, **common)
    elif chart == "pie":
        fig = px.pie(plot_df, names=x, values=y, title=title)
    elif chart == "histogram":
        fig = px.histogram(plot_df, x=x or y, **common)
    elif chart == "box":
        fig = px.box(plot_df, x=x, y=y, **common)
    else:
        fig = go.Figure()

    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=cfg.get("height", 350))
    return ("figure", fig)
