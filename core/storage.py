"""Слой хранения датасетов, виджетов и дашбордов.

Два бэкенда с единым API:

* **БД (Postgres)** — если задана переменная окружения ``DATABASE_URL`` или
  секрет Streamlit ``DATABASE_URL``. Данные хранятся в внешней базе и
  переживают перезапуск контейнера (нужно для Streamlit Cloud).
* **Файлы** — иначе. Всё лежит в каталоге ``workspace/`` рядом с проектом
  (датасеты — parquet, виджеты/дашборды — JSON).

Бэкенд выбирается автоматически при импорте.
"""
from __future__ import annotations

import io
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

# --------------------------------------------------------------------------- #
# Выбор бэкенда
# --------------------------------------------------------------------------- #
def _database_url() -> str | None:
    """Строка подключения к БД из env или секретов Streamlit (или None)."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        try:
            import streamlit as st
            url = st.secrets.get("DATABASE_URL")  # тип: ignore[attr-defined]
        except Exception:  # noqa: BLE001 — секретов может не быть
            url = None
    if not url:
        return None
    # Нормализуем драйвер под psycopg2.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


_DB_URL = _database_url()
USE_DB = _DB_URL is not None


def backend_name() -> str:
    return "База данных" if USE_DB else "Локальные файлы"


def _df_to_parquet(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    return buf.getvalue()


def _parquet_to_df(data: bytes) -> pd.DataFrame:
    return pd.read_parquet(io.BytesIO(data))


def _dataset_meta(df: pd.DataFrame, source: str, meta: dict | None) -> dict:
    return {
        "source": source,
        "rows": int(len(df)),
        "cols": int(df.shape[1]),
        "columns": list(map(str, df.columns)),
        "updated": datetime.now().isoformat(timespec="seconds"),
        "meta": meta or {},
    }


# =========================================================================== #
# Бэкенд: база данных (SQLAlchemy Core)
# =========================================================================== #
if USE_DB:
    from sqlalchemy import (Column, Integer, LargeBinary, MetaData, String,
                            Table, Text, create_engine, delete, func, insert,
                            select, update)

    _engine = create_engine(_DB_URL, pool_pre_ping=True)
    _metadata = MetaData()
    _DATASETS = Table("dv_datasets", _metadata,
                      Column("name", String(255), primary_key=True),
                      Column("meta", Text, nullable=False),
                      Column("data", LargeBinary, nullable=False))
    _WIDGETS = Table("dv_widgets", _metadata,
                     Column("id", String(64), primary_key=True),
                     Column("seq", Integer),
                     Column("config", Text, nullable=False))
    _DASHBOARDS = Table("dv_dashboards", _metadata,
                        Column("id", String(64), primary_key=True),
                        Column("seq", Integer),
                        Column("config", Text, nullable=False))
    _db_ready = False

    def ensure_dirs() -> None:
        global _db_ready
        if not _db_ready:
            _metadata.create_all(_engine)
            _db_ready = True

    # --- датасеты --------------------------------------------------------- #
    def list_datasets() -> dict[str, dict]:
        ensure_dirs()
        with _engine.connect() as cx:
            rows = cx.execute(select(_DATASETS.c.name, _DATASETS.c.meta)).all()
        return {name: json.loads(meta) for name, meta in rows}

    def save_dataset(name: str, df: pd.DataFrame, source: str = "manual",
                     meta: dict | None = None) -> None:
        ensure_dirs()
        meta_json = json.dumps(_dataset_meta(df, source, meta), ensure_ascii=False)
        data = _df_to_parquet(df)
        with _engine.begin() as cx:
            exists = cx.execute(
                select(_DATASETS.c.name).where(_DATASETS.c.name == name)).first()
            if exists:
                cx.execute(update(_DATASETS).where(_DATASETS.c.name == name)
                           .values(meta=meta_json, data=data))
            else:
                cx.execute(insert(_DATASETS)
                           .values(name=name, meta=meta_json, data=data))

    def load_dataset(name: str) -> pd.DataFrame:
        ensure_dirs()
        with _engine.connect() as cx:
            row = cx.execute(
                select(_DATASETS.c.data).where(_DATASETS.c.name == name)).first()
        if row is None:
            raise KeyError(f"Датасет '{name}' не найден")
        return _parquet_to_df(row[0])

    def delete_dataset(name: str) -> None:
        ensure_dirs()
        with _engine.begin() as cx:
            cx.execute(delete(_DATASETS).where(_DATASETS.c.name == name))

    def rename_dataset(old: str, new: str) -> None:
        if not new or new == old:
            return
        ensure_dirs()
        with _engine.begin() as cx:
            cx.execute(update(_DATASETS).where(_DATASETS.c.name == old)
                       .values(name=new))

    # --- виджеты ---------------------------------------------------------- #
    def get_widgets() -> list[dict]:
        ensure_dirs()
        with _engine.connect() as cx:
            rows = cx.execute(
                select(_WIDGETS.c.config).order_by(_WIDGETS.c.seq)).all()
        return [json.loads(r[0]) for r in rows]

    def save_widget(widget: dict) -> dict:
        ensure_dirs()
        if not widget.get("id"):
            widget["id"] = uuid.uuid4().hex
        cfg = json.dumps(widget, ensure_ascii=False)
        with _engine.begin() as cx:
            exists = cx.execute(
                select(_WIDGETS.c.id).where(_WIDGETS.c.id == widget["id"])).first()
            if exists:
                cx.execute(update(_WIDGETS).where(_WIDGETS.c.id == widget["id"])
                           .values(config=cfg))
            else:
                seq = (cx.execute(select(func.max(_WIDGETS.c.seq))).scalar() or 0) + 1
                cx.execute(insert(_WIDGETS)
                           .values(id=widget["id"], seq=seq, config=cfg))
        return widget

    def delete_widget(widget_id: str) -> None:
        ensure_dirs()
        with _engine.begin() as cx:
            cx.execute(delete(_WIDGETS).where(_WIDGETS.c.id == widget_id))
        # Убираем виджет из всех дашбордов.
        for d in get_dashboards():
            if widget_id in d.get("widgets", []):
                d["widgets"] = [w for w in d["widgets"] if w != widget_id]
                save_dashboard(d)

    # --- дашборды --------------------------------------------------------- #
    def get_dashboards() -> list[dict]:
        ensure_dirs()
        with _engine.connect() as cx:
            rows = cx.execute(
                select(_DASHBOARDS.c.config).order_by(_DASHBOARDS.c.seq)).all()
        return [json.loads(r[0]) for r in rows]

    def save_dashboard(dashboard: dict) -> dict:
        ensure_dirs()
        if not dashboard.get("id"):
            dashboard["id"] = uuid.uuid4().hex
        cfg = json.dumps(dashboard, ensure_ascii=False)
        with _engine.begin() as cx:
            exists = cx.execute(select(_DASHBOARDS.c.id)
                                .where(_DASHBOARDS.c.id == dashboard["id"])).first()
            if exists:
                cx.execute(update(_DASHBOARDS)
                           .where(_DASHBOARDS.c.id == dashboard["id"])
                           .values(config=cfg))
            else:
                seq = (cx.execute(select(func.max(_DASHBOARDS.c.seq))).scalar() or 0) + 1
                cx.execute(insert(_DASHBOARDS)
                           .values(id=dashboard["id"], seq=seq, config=cfg))
        return dashboard

    def delete_dashboard(dashboard_id: str) -> None:
        ensure_dirs()
        with _engine.begin() as cx:
            cx.execute(delete(_DASHBOARDS).where(_DASHBOARDS.c.id == dashboard_id))


# =========================================================================== #
# Бэкенд: локальные файлы
# =========================================================================== #
else:
    WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
    DATASETS_DIR = WORKSPACE / "datasets"
    DATASETS_INDEX = WORKSPACE / "datasets.json"
    WIDGETS_FILE = WORKSPACE / "widgets.json"
    DASHBOARDS_FILE = WORKSPACE / "dashboards.json"

    def ensure_dirs() -> None:
        DATASETS_DIR.mkdir(parents=True, exist_ok=True)
        for f in (DATASETS_INDEX, WIDGETS_FILE, DASHBOARDS_FILE):
            if not f.exists():
                f.write_text("{}" if f is DATASETS_INDEX else "[]",
                             encoding="utf-8")

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
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    # --- датасеты --------------------------------------------------------- #
    def list_datasets() -> dict[str, dict]:
        return _read_json(DATASETS_INDEX, {})

    def save_dataset(name: str, df: pd.DataFrame, source: str = "manual",
                     meta: dict | None = None) -> None:
        ensure_dirs()
        index = list_datasets()
        slug = index.get(name, {}).get("slug") or _slug(name)
        df.to_parquet(DATASETS_DIR / f"{slug}.parquet", index=False)
        index[name] = {"slug": slug, **_dataset_meta(df, source, meta)}
        _write_json(DATASETS_INDEX, index)

    def load_dataset(name: str) -> pd.DataFrame:
        index = list_datasets()
        if name not in index:
            raise KeyError(f"Датасет '{name}' не найден")
        return pd.read_parquet(DATASETS_DIR / f"{index[name]['slug']}.parquet")

    def delete_dataset(name: str) -> None:
        index = list_datasets()
        info = index.pop(name, None)
        if info:
            (DATASETS_DIR / f"{info['slug']}.parquet").unlink(missing_ok=True)
            _write_json(DATASETS_INDEX, index)

    def rename_dataset(old: str, new: str) -> None:
        index = list_datasets()
        if old in index and new and new != old:
            index[new] = index.pop(old)
            _write_json(DATASETS_INDEX, index)

    # --- виджеты ---------------------------------------------------------- #
    def get_widgets() -> list[dict]:
        return _read_json(WIDGETS_FILE, [])

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
        dashboards = get_dashboards()
        for d in dashboards:
            d["widgets"] = [w for w in d.get("widgets", []) if w != widget_id]
        _write_json(DASHBOARDS_FILE, dashboards)

    # --- дашборды --------------------------------------------------------- #
    def get_dashboards() -> list[dict]:
        return _read_json(DASHBOARDS_FILE, [])

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


# --------------------------------------------------------------------------- #
# Общие функции (одинаковы для обоих бэкендов)
# --------------------------------------------------------------------------- #
def get_widget(widget_id: str) -> dict | None:
    return next((w for w in get_widgets() if w["id"] == widget_id), None)


def get_dashboard(dashboard_id: str) -> dict | None:
    return next((d for d in get_dashboards() if d["id"] == dashboard_id), None)
