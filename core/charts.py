"""Построение виджетов из конфигурации с помощью Plotly.

Названия типов и состав приближены к АС «Представление данных»
(Гистограмма, Круговая диаграмма, Список, Процент выполненных работ и т.д.).
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Тип виджета -> отображаемое название (как в референсной системе).
CHART_TYPES = {
    "bar": "Гистограмма",
    "line": "Линейный график",
    "area": "График с областями",
    "scatter": "Точечная диаграмма",
    "pie": "Круговая диаграмма",
    "histogram": "Распределение",
    "box": "Ящик с усами",
    "table": "Список",
    "metric": "Показатель",
    "gauge": "Процент выполненных работ",
    "html": "Html",
    "image": "Изображение",
    "datetime": "Дата/время",
}

# Виджеты, не привязанные к данным (статические).
STATIC_TYPES = {"html", "image", "datetime"}

# Темы оформления (шаблоны Plotly) для дашбордов и виджетов.
THEMES = {
    "Светлая": "plotly_white",
    "Минимальная": "simple_white",
    "Презентация": "presentation",
    "Тёмная": "plotly_dark",
    "Сетка": "ggplot2",
    "Чёрно-белая": "none",
}

# Фирменная фиолетово-розовая палитра для виджетов (в стиле референса).
COLORWAY = ["#8B5CF6", "#EC4899", "#A855F7", "#F472B6", "#C026D3",
            "#7C3AED", "#D946EF", "#6366F1", "#E879F9", "#9333EA"]
# Непрерывная шкала (для числовой раскраски) — фиолетовый → розовый.
COLOR_SCALE = ["#6D28D9", "#8B5CF6", "#C026D3", "#EC4899", "#F9A8D4"]

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
        return df.groupby(group_cols, dropna=False).size().reset_index(name="count")
    valid_ys = [y for y in ys if y in df.columns]
    if not valid_ys:
        return df
    return df.groupby(group_cols, dropna=False)[valid_ys].agg(agg).reset_index()


def _scalar(df: pd.DataFrame, col: str | None, agg: str):
    """Числовой показатель по столбцу с агрегацией."""
    if col is None or col not in df.columns:
        return None
    series = pd.to_numeric(df[col], errors="coerce")
    func = agg if agg not in ("none", None) else "sum"
    return series.count() if func == "count" else getattr(series, func)()


def build_figure(df: pd.DataFrame, cfg: dict):
    """Возвращает кортеж (вид, данные):

    ('figure', go.Figure) | ('table', df) | ('metric', value) |
    ('html', str) | ('image', url) | ('datetime', None).
    """
    chart = cfg.get("chart_type", "bar")
    # Активная тема приложения (передаётся из ui.render_widget); запасной вариант —
    # сохранённая тема виджета или светлая.
    template = cfg.get("_template") or THEMES.get(cfg.get("theme", ""), "plotly_white")
    x = cfg.get("x")
    ys = cfg.get("y") or []
    if isinstance(ys, str):
        ys = [ys]
    color = cfg.get("color") or None
    agg = cfg.get("agg", "none")
    title = cfg.get("title") or cfg.get("name", "")

    # --- Статические виджеты --------------------------------------------- #
    if chart == "html":
        return ("html", cfg.get("html", ""))
    if chart == "image":
        return ("image", cfg.get("image_url", ""))
    if chart == "datetime":
        return ("datetime", None)

    # --- Данные ----------------------------------------------------------- #
    if chart == "table":
        return ("table", df)

    if chart == "metric":
        col = ys[0] if ys else (x or (df.columns[0] if len(df.columns) else None))
        value = _scalar(df, col, agg)
        return ("metric", value if value is not None else "—")

    if chart == "gauge":
        col = ys[0] if ys else x
        value = _scalar(df, col, agg) or 0
        gmax = float(cfg.get("gauge_max") or 100)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=float(value),
            number={"suffix": cfg.get("gauge_suffix", ""), "font": {"color": "#E7E4F0"}},
            title={"text": title},
            gauge={
                "axis": {"range": [0, gmax]},
                "bar": {"color": "#8B5CF6"},
                "bordercolor": "rgba(139,92,246,.25)",
                "threshold": {"line": {"color": "#EC4899", "width": 3},
                              "value": float(cfg.get("gauge_target") or gmax)},
            },
        ))
        fig.update_layout(template=template, height=cfg.get("height", 300),
                          margin=dict(l=20, r=20, t=50, b=10),
                          paper_bgcolor="rgba(0,0,0,0)", font_color="#E7E4F0")
        return ("figure", fig)

    # Для линий/областей без явной агрегации суммируем по X — иначе несколько
    # значений на одну дату дают «зигзаг» из вертикальных линий.
    plot_agg = "sum" if (agg == "none" and chart in ("line", "area")) else agg
    plot_df = _aggregate(df, x, ys, color, plot_agg)
    if x and x in plot_df.columns:
        plot_df = plot_df.sort_values(by=x)  # линия слева направо
    y = "count" if (plot_agg == "count") else (ys[0] if ys else None)
    y_multi = ys if (plot_agg != "count" and len(ys) > 1) else y

    common = dict(title=title, template=template,
                  color_discrete_sequence=COLORWAY)
    if color:
        common["color"] = color

    if chart == "line":
        fig = px.line(plot_df, x=x, y=y_multi, **common)
        _smooth_fill(fig)
    elif chart == "bar":
        fig = px.bar(plot_df, x=x, y=y_multi, barmode="group", **common)
    elif chart == "area":
        fig = px.area(plot_df, x=x, y=y_multi, **common)
        fig.update_traces(line_shape="spline")
    elif chart == "scatter":
        fig = px.scatter(plot_df, x=x, y=y, **common)
    elif chart == "pie":
        fig = px.pie(plot_df, names=x, values=y, title=title, template=template,
                     color_discrete_sequence=COLORWAY)
    elif chart == "histogram":
        fig = px.histogram(plot_df, x=x or y, **common)
    elif chart == "box":
        fig = px.box(plot_df, x=x, y=y, **common)
    else:
        fig = go.Figure()

    _style(fig, cfg)
    return ("figure", fig)


def _style(fig, cfg: dict) -> None:
    """Единое оформление: прозрачный фон (под фиолетовые карточки), палитра."""
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        height=cfg.get("height", 350),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=COLORWAY,
        font_color="#E7E4F0",
        legend_font_color="#E7E4F0",
    )
    fig.update_xaxes(gridcolor="rgba(139,92,246,.15)", zerolinecolor="rgba(139,92,246,.25)")
    fig.update_yaxes(gridcolor="rgba(139,92,246,.15)", zerolinecolor="rgba(139,92,246,.25)")


def _rgba(color: str, alpha: float) -> str:
    """HEX (#RRGGBB) -> rgba(...) с заданной прозрачностью."""
    c = (color or "").lstrip("#")
    if len(c) == 6:
        r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
        return f"rgba({r},{g},{b},{alpha})"
    return color or f"rgba(139,92,246,{alpha})"


def _smooth_fill(fig) -> None:
    """Сглаживание (spline) + полупрозрачная заливка под линией — как на референсе."""
    for tr in fig.data:
        base = tr.line.color or COLORWAY[0]
        tr.update(line_shape="spline", line_width=2.6, mode="lines",
                  fill="tozeroy", fillcolor=_rgba(base, 0.16))


def current_datetime() -> str:
    """Текущая дата и время для виджета «Дата/время»."""
    return datetime.now().strftime("%d.%m.%Y  %H:%M:%S")
