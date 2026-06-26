"""Экспорт дашборда в один PNG-файл.

Каждый виджет рендерится в изображение (графики — через Plotly/kaleido,
показатели/таблицы — как Plotly Indicator/Table), затем всё собирается в
сетку через Pillow. Цвета — в тон тёмно-фиолетовой теме приложения.
"""
from __future__ import annotations

import io
import re

import plotly.graph_objects as go
from PIL import Image, ImageDraw

from core import charts, storage

FONT = "Arial, Helvetica, sans-serif"
RADIUS = 22         # скругление углов карточки (px)
BORDER = (96, 78, 140)  # цвет рамки карточки (фиолетовый)

BG = "#17131F"      # фон холста
CARD = "#221C33"    # фон карточки виджета
FG = "#E7E4F0"      # текст
CW, CH = 540, 360   # размер карточки (layout-единицы)
SCALE = 2           # для чёткости (итоговый пиксель = CW*SCALE)
PAD = 16 * SCALE
TITLE_H = 70 * SCALE


def _text_fig(title: str, text: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=f"<b>{title}</b><br><br>{text}", showarrow=False,
        x=0.5, y=0.5, xref="paper", yref="paper",
        font=dict(color=FG, size=20), align="center")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _widget_fig(cfg: dict, df) -> go.Figure | None:
    """Plotly-фигура для любого типа виджета (или None для изображения)."""
    kind, payload = charts.build_figure(df, {**cfg, "_template": "plotly_dark"})
    name = cfg.get("title") or cfg.get("name", "")

    if kind == "figure":
        return payload
    if kind == "metric":
        try:
            return go.Figure(go.Indicator(
                mode="number", value=float(payload),
                number={"font": {"color": FG, "size": 56}},
                title={"text": name, "font": {"color": FG, "size": 20}}))
        except (TypeError, ValueError):
            return _text_fig(name, str(payload))
    if kind == "table":
        d = payload.head(12)
        fig = go.Figure(go.Table(
            header=dict(values=[f"<b>{c}</b>" for c in d.columns],
                        fill_color="#2E2746", font=dict(color=FG, size=13),
                        align="left"),
            cells=dict(values=[d[c].astype(str) for c in d.columns],
                       fill_color=CARD, font=dict(color=FG, size=12),
                       align="left", height=24)))
        fig.update_layout(title=name)
        return fig
    if kind == "datetime":
        return _text_fig(name or "Дата/время", charts.current_datetime())
    if kind == "html":
        return _text_fig(name, re.sub("<[^>]+>", "", payload or "")[:240])
    if kind == "image":
        return None
    return _text_fig(name, "")


def _fig_png(fig: go.Figure) -> Image.Image:
    fig.update_layout(width=CW, height=CH, paper_bgcolor=CARD, plot_bgcolor=CARD,
                      font=dict(color=FG, family=FONT),
                      title_font=dict(color=FG, family=FONT, size=18),
                      margin=dict(l=30, r=20, t=50, b=30))
    # Сетка — едва заметная (как в приложении), без жирных линий.
    fig.update_xaxes(gridcolor="rgba(139,92,246,.08)", zerolinecolor="rgba(139,92,246,.12)")
    fig.update_yaxes(gridcolor="rgba(139,92,246,.08)", zerolinecolor="rgba(139,92,246,.12)")
    data = fig.to_image(format="png", scale=SCALE)
    return Image.open(io.BytesIO(data)).convert("RGB")


def _round_card(img: Image.Image) -> Image.Image:
    """Скруглённые углы + тонкая фиолетовая рамка (как карточки в приложении)."""
    r = RADIUS * SCALE
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    out = Image.new("RGB", (w, h), BG)
    out.paste(img, (0, 0), mask)
    ImageDraw.Draw(out).rounded_rectangle(
        [1, 1, w - 2, h - 2], radius=r, outline=BORDER, width=2)
    return out


def _placeholder(text: str) -> Image.Image:
    return _fig_png(_text_fig("", text))


def _image_widget(cfg: dict) -> Image.Image:
    url = cfg.get("image_url", "")
    try:
        import requests
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        src = Image.open(io.BytesIO(resp.content)).convert("RGB")
        card = Image.new("RGB", (CW * SCALE, CH * SCALE), CARD)
        src.thumbnail((CW * SCALE - 20, CH * SCALE - 20))
        card.paste(src, ((card.width - src.width) // 2,
                         (card.height - src.height) // 2))
        return card
    except Exception:  # noqa: BLE001
        return _placeholder("Изображение недоступно")


def _widget_image(cfg: dict, datasets: dict) -> Image.Image:
    df = (storage.load_dataset(cfg["dataset"])
          if cfg.get("dataset") in datasets else None)
    if cfg["chart_type"] not in charts.STATIC_TYPES and df is None:
        return _placeholder(f"«{cfg.get('name', '')}»: датасет удалён")
    if cfg["chart_type"] == "image":
        return _image_widget(cfg)
    try:
        return _fig_png(_widget_fig(cfg, df))
    except Exception as e:  # noqa: BLE001
        return _placeholder(f"Ошибка рендера:\n{e}")


def export_png(dashboard: dict, widget_by_id: dict, datasets: dict) -> bytes | None:
    """Собирает дашборд в один PNG. Возвращает байты или None, если пусто."""
    wids = [w for w in dashboard.get("widgets", []) if w in widget_by_id]
    if not wids:
        return None
    ncols = max(1, dashboard.get("columns", 2))
    nrows = -(-len(wids) // ncols)  # ceil
    cwpx, chpx = CW * SCALE, CH * SCALE

    width = PAD + ncols * (cwpx + PAD)
    height = TITLE_H + PAD + nrows * (chpx + PAD)
    canvas = Image.new("RGB", (width, height), BG)

    # Заголовок дашборда (через Plotly — корректная кириллица).
    title_fig = _text_fig(dashboard.get("name", "Дашборд"), "")
    title_fig.update_layout(width=width // SCALE, height=TITLE_H // SCALE,
                            paper_bgcolor=BG, plot_bgcolor=BG,
                            margin=dict(l=10, r=10, t=10, b=10))
    title_img = Image.open(io.BytesIO(title_fig.to_image(format="png", scale=SCALE)))
    canvas.paste(title_img.convert("RGB"), (0, 0))

    for i, wid in enumerate(wids):
        img = _widget_image(widget_by_id[wid], datasets)
        if img.size != (cwpx, chpx):
            img = img.resize((cwpx, chpx))
        img = _round_card(img)
        r, c = divmod(i, ncols)
        x = PAD + c * (cwpx + PAD)
        y = TITLE_H + PAD + r * (chpx + PAD)
        canvas.paste(img, (x, y))

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()
