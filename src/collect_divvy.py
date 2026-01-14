from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import yaml

from gbfs_client import discover_divvy_feeds, fetch_station_status


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _load_config(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_once(config_path: str = "config/config.yaml") -> Path:
    cfg = _load_config(config_path)

    gbfs_url = cfg["divvy"]["gbfs_auto_discovery_url"]
    snapshots_dir = _ensure_dir(cfg["collection"]["snapshots_dir"])

    feeds = discover_divvy_feeds(gbfs_url)
    status = fetch_station_status(feeds.station_status_url)

    # Extract station status list
    station_list = status.get("data", {}).get("stations", [])
    ts = _utc_now_iso()

    rows = []
    for s in station_list:
        rows.append({
            "timestamp_utc": ts,
            "station_id": s.get("station_id"),
            "num_bikes_available": s.get("num_bikes_available"),
            "num_docks_available": s.get("num_docks_available"),
            "is_installed": s.get("is_installed"),
            "is_renting": s.get("is_renting"),
            "is_returning": s.get("is_returning"),
        })

    df = pd.DataFrame(rows)

    # Save daily file (append)
    day = ts[:10]  # YYYY-MM-DD
    out_path = snapshots_dir / f"divvy_station_status_{day}.csv"

    if out_path.exists():
        df.to_csv(out_path, mode="a", index=False, header=False)
    else:
        df.to_csv(out_path, index=False)

    print(f"✅ Saved snapshot rows={len(df)} to {out_path}")
    return out_path


def collect_loop(config_path: str = "config/config.yaml") -> None:
    cfg = _load_config(config_path)
    interval = int(cfg["collection"]["interval_seconds"])

    print(f"Starting Divvy snapshot collection every {interval}s. Ctrl+C to stop.")
    while True:
        try:
            collect_once(config_path)
        except Exception as e:
            print(f"⚠️ Collection error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    # By default, collect once (safe). Change to collect_loop() if you want.
    collect_once()
