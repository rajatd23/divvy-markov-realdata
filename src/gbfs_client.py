from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, Any, Optional

import requests


@dataclass(frozen=True)
class DivvyFeeds:
    station_information_url: str
    station_status_url: str


def _get_json(url: str, timeout: int = 30) -> Dict[str, Any]:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def discover_divvy_feeds(gbfs_auto_discovery_url: str, prefer_lang: str = "en") -> DivvyFeeds:
    """
    GBFS auto-discovery returns language blocks containing a list of feed URLs.
    We find station_information + station_status.
    """
    gbfs = _get_json(gbfs_auto_discovery_url)

    # GBFS typically looks like: {"data": {"en": {"feeds": [{"name": "...", "url": "..."}]}}}
    data = gbfs.get("data", {})
    lang_block = data.get(prefer_lang) or next(iter(data.values()))
    feeds = lang_block.get("feeds", [])

    feed_map = {f["name"]: f["url"] for f in feeds if "name" in f and "url" in f}

    if "station_information" not in feed_map or "station_status" not in feed_map:
        raise ValueError("Could not find station_information and station_status in GBFS feeds.")

    return DivvyFeeds(
        station_information_url=feed_map["station_information"],
        station_status_url=feed_map["station_status"],
    )


def fetch_station_information(station_information_url: str) -> Dict[str, Any]:
    return _get_json(station_information_url)


def fetch_station_status(station_status_url: str) -> Dict[str, Any]:
    return _get_json(station_status_url)
