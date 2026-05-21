from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .normalization import norm_key


@dataclass(frozen=True)
class RegionMatch:
    region_code: str | None
    region_name: str | None
    source: str
    confidence: str


def load_regions(path: str | Path) -> dict[str, dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("regions", data)


def detect_region(address: str | None, regions: dict[str, dict]) -> RegionMatch:
    if not address:
        return RegionMatch(None, None, "no_address", "low")
    text = norm_key(address)
    best: tuple[int, str, dict] | None = None
    for code, cfg in regions.items():
        keywords = cfg.get("keywords") or []
        for kw in keywords:
            key = norm_key(kw)
            if key and key in text:
                score = len(key)
                if best is None or score > best[0]:
                    best = (score, code, cfg)
    if best:
        _, code, cfg = best
        return RegionMatch(code, cfg.get("name", code), "address", "medium")
    return RegionMatch(None, None, "not_detected", "low")
