from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import yaml

from gbfs_client import discover_divvy_feeds, fetch_station_information


STATES = ["EMPTY", "LOW", "MEDIUM", "HIGH"]


def _ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _load_config(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _assign_state(bikes: float, docks: float, low_max: float, medium_max: float) -> str:
    # Special case
    if bikes == 0:
        return "EMPTY"

    denom = bikes + docks
    if denom <= 0:
        # If the feed is weird, put into LOW rather than failing
        return "LOW"

    ratio = bikes / denom
    if ratio <= low_max:
        return "LOW"
    elif ratio <= medium_max:
        return "MEDIUM"
    else:
        return "HIGH"


def _load_all_snapshots(snapshots_dir: str | Path) -> pd.DataFrame:
    snapshots_dir = Path(snapshots_dir)
    files = sorted(snapshots_dir.glob("divvy_station_status_*.csv"))
    if not files:
        raise FileNotFoundError("No snapshot CSVs found. Run src/collect_divvy.py first.")

    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)

    # Parse timestamps
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp_utc", "station_id"])
    return df


def build_station_capacity_table(cfg: Dict[str, Any]) -> pd.DataFrame:
    gbfs_url = cfg["divvy"]["gbfs_auto_discovery_url"]
    feeds = discover_divvy_feeds(gbfs_url)
    info = fetch_station_information(feeds.station_information_url)

    stations = info.get("data", {}).get("stations", [])
    rows = []
    for s in stations:
        rows.append({
            "station_id": s.get("station_id"),
            "name": s.get("name"),
            "lat": s.get("lat"),
            "lon": s.get("lon"),
            "capacity": s.get("capacity"),
        })

    df = pd.DataFrame(rows).dropna(subset=["station_id"])
    return df


def learn_transition_matrix(config_path: str = "config/config.yaml") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cfg = _load_config(config_path)

    low_max = float(cfg["state_binning"]["low_max"])
    medium_max = float(cfg["state_binning"]["medium_max"])

    snapshots_dir = cfg["collection"]["snapshots_dir"]
    derived_dir = _ensure_dir("data/derived")

    df = _load_all_snapshots(snapshots_dir)

    # Keep only active stations (optional but helps data quality)
    for col in ["is_installed", "is_renting", "is_returning"]:
        if col in df.columns:
            df = df[df[col] == 1]

    # Convert to numeric
    df["num_bikes_available"] = pd.to_numeric(df["num_bikes_available"], errors="coerce")
    df["num_docks_available"] = pd.to_numeric(df["num_docks_available"], errors="coerce")
    df = df.dropna(subset=["num_bikes_available", "num_docks_available"])

    # Assign state per snapshot
    df["state"] = df.apply(
        lambda r: _assign_state(r["num_bikes_available"], r["num_docks_available"], low_max, medium_max),
        axis=1
    )

    # Sort and create next_state per station
    df = df.sort_values(["station_id", "timestamp_utc"])
    df["next_state"] = df.groupby("station_id")["state"].shift(-1)

    # Only rows where we have a next state
    trans = df.dropna(subset=["next_state"]).copy()

    # Transition counts
    state_to_idx = {s: i for i, s in enumerate(STATES)}
    counts = np.zeros((len(STATES), len(STATES)), dtype=np.int64)

    for a, b in zip(trans["state"], trans["next_state"]):
        counts[state_to_idx[a], state_to_idx[b]] += 1

    counts_df = pd.DataFrame(counts, index=STATES, columns=STATES)
    counts_df.index.name = "from_state"

    # Transition probabilities (row-normalized)
    row_sums = counts.sum(axis=1, keepdims=True)
    probs = np.divide(counts, np.where(row_sums == 0, 1, row_sums), dtype=float)
    probs_df = pd.DataFrame(probs, index=STATES, columns=STATES)
    probs_df.index.name = "from_state"

    # Save derived datasets
    trans_out = derived_dir / "station_state_transitions.csv"
    trans[["timestamp_utc", "station_id", "state", "next_state"]].to_csv(trans_out, index=False)

    counts_df.to_csv(derived_dir / "transition_counts_real.csv")
    probs_df.to_csv(derived_dir / "transition_probs_real.csv")

    print("✅ Learned transition matrix from real Divvy snapshots.")
    print(f"- Saved: {trans_out}")
    print(f"- Saved: {derived_dir / 'transition_counts_real.csv'}")
    print(f"- Saved: {derived_dir / 'transition_probs_real.csv'}")

    return trans[["timestamp_utc", "station_id", "state", "next_state"]], counts_df, probs_df


if __name__ == "__main__":
    learn_transition_matrix()
