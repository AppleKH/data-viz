"""Слой хранения: датасеты (parquet) + виджеты и дашборды (JSON).

Всё хранится в каталоге ``workspace/`` рядом с проектом, поэтому состояние
переживает перезапуск Streamlit.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
DATASETS_DIR = WORKSPACE / "datasets"
DATASETS_INDEX = WORKSPACE / "datasets.json"
WIDGETS_FILE = WORKSPACE / "widgets.json"
DASHBOARDS_FILE = WORKSPACE / "dashboards.json"


def ensure_dirs() -> None:
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    for f in (DATASETS_INDEX, WIDGETS_FILE, DASHBOARDS_FILE):
        if not f.exists():
            f.write_text("{}" if f is DATASETS_INDEX else "[]", encoding="utf-8")


def _slug(name: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", name.strip(), flags=re.UNICODE).strip("_")
    return s or uuid.uuid4().hex[:8]


def _read_json(path: Path, default: Any) -> Any:
    ensure_dirs()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write_json(path: Path, data: Any) -> None:
    ensure_dirs()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Датасеты
# --------------------------------------------------------------------------- #
def list_datasets() -> dict[str, dict]:
    """Возвращает реестр {имя: метаданные}."""
    return _read_json(DATASETS_INDEX, {})


def save_dataset(name: str, df: pd.DataFrame, source: str = "manual",
                 meta: dict | None = None) -> None:
    ensure_dirs()
    index = list_datasets()
    slug = index.get(name, {}).get("slug") or _slug(name)
    path = DATASETS_DIR / f"{slug}.parquet"
    df.to_parquet(path, index=False)
    index[name] = {
        "slug": slug,
        "source": source,
        "rows": int(len(df)),
        "cols": int(df.shape[1]),
        "columns": list(map(str, df.columns)),
        "updated": datetime.now().isoformat(timespec="seconds"),
        "meta": meta or {},
    }
    _write_json(DATASETS_INDEX, index)


def load_dataset(name: str) -> pd.DataFrame:
    index = list_datasets()
    if name not in index:
        raise KeyError(f"Датасет '{name}' не найден")
    path = DATASETS_DIR / f"{index[name]['slug']}.parquet"
    return pd.read_parquet(path)


def delete_dataset(name: str) -> None:
    index = list_datasets()
    info = index.pop(name, None)
    if info:
        path = DATASETS_DIR / f"{info['slug']}.parquet"
        path.unlink(missing_ok=True)
        _write_json(DATASETS_INDEX, index)


def rename_dataset(old: str, new: str) -> None:
    index = list_datasets()
    if old in index and new and new != old:
        index[new] = index.pop(old)
        _write_json(DATASETS_INDEX, index)


# --------------------------------------------------------------------------- #
# Виджеты
# --------------------------------------------------------------------------- #
def get_widgets() -> list[dict]:
    return _read_json(WIDGETS_FILE, [])


def get_widget(widget_id: str) -> dict | None:
    return next((w for w in get_widgets() if w["id"] == widget_id), None)


def save_widget(widget: dict) -> dict:
    widgets = get_widgets()
    if not widget.get("id"):
        widget["id"] = uuid.uuid4().hex
        widgets.append(widget)
    else:
        widgets = [widget if w["id"] == widget["id"] else w for w in widgets]
        if widget["id"] not in {w["id"] for w in widgets}:
            widgets.append(widget)
    _write_json(WIDGETS_FILE, widgets)
    return widget


def delete_widget(widget_id: str) -> None:
    _write_json(WIDGETS_FILE, [w for w in get_widgets() if w["id"] != widget_id])
    # Убираем виджет из всех дашбордов
    dashboards = get_dashboards()
    for d in dashboards:
        d["widgets"] = [w for w in d.get("widgets", []) if w != widget_id]
    _write_json(DASHBOARDS_FILE, dashboards)


# --------------------------------------------------------------------------- #
# Дашборды
# --------------------------------------------------------------------------- #
def get_dashboards() -> list[dict]:
    return _read_json(DASHBOARDS_FILE, [])


def get_dashboard(dashboard_id: str) -> dict | None:
    return next((d for d in get_dashboards() if d["id"] == dashboard_id), None)


def save_dashboard(dashboard: dict) -> dict:
    dashboards = get_dashboards()
    if not dashboard.get("id"):
        dashboard["id"] = uuid.uuid4().hex
        dashboards.append(dashboard)
    else:
        dashboards = [dashboard if d["id"] == dashboard["id"] else d
                      for d in dashboards]
        if dashboard["id"] not in {d["id"] for d in dashboards}:
            dashboards.append(dashboard)
    _write_json(DASHBOARDS_FILE, dashboards)
    return dashboard


def delete_dashboard(dashboard_id: str) -> None:
    _write_json(DASHBOARDS_FILE,
                [d for d in get_dashboards() if d["id"] != dashboard_id])
