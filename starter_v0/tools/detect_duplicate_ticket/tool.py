"""Read-only, local duplicate candidates; never authorizes ticket creation."""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import unicodedata

TICKET_DIR = Path(__file__).resolve().parents[2] / "tickets"


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    return " ".join(re.findall(r"[a-z0-9]+", "".join(
        c for c in value if not unicodedata.combining(c)
    )))


def detect_duplicate_ticket(summary: str, asset_id: str = "", threshold: float = 0.7,
                            max_results: int = 5) -> dict:
    """Match normalized words within the same asset, returning IDs and scores only."""
    base = {"tool": "detect_duplicate_ticket"}
    if not isinstance(summary, str) or not summary.strip() or len(summary) > 1000:
        return {**base, "error": "invalid_summary"}
    if not isinstance(asset_id, str) or (asset_id.strip() and not re.fullmatch(
        r"(?:LT|DT|MB|PR|RM)-\d+", asset_id.strip(), re.I
    )):
        return {**base, "error": "invalid_asset_id"}
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 < threshold <= 1:
        return {**base, "error": "invalid_threshold"}
    if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= 20:
        return {**base, "error": "invalid_max_results"}
    normalized = _normalize(summary)
    if not normalized:
        return {**base, "error": "invalid_summary"}
    target_asset = asset_id.strip().upper()
    words = set(normalized.split())
    matches, scanned, skipped = [], 0, 0
    try:
        paths = sorted(TICKET_DIR.glob("*.json"))
        for path in paths:
            # Ignore links and malformed records; never follow a caller-supplied path.
            try:
                if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
                    skipped += 1
                    continue
                item = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(item, dict):
                    raise ValueError("record")
                ticket_id, text = item.get("ticket_id"), item.get("summary")
                stored_asset = item.get("asset_id") or ""
                if not isinstance(ticket_id, str) or not re.fullmatch(r"LAB-[A-Fa-f0-9]{8}", ticket_id):
                    raise ValueError("id")
                if not isinstance(text, str) or not text.strip() or not isinstance(stored_asset, str):
                    raise ValueError("fields")
                scanned += 1
                if stored_asset.strip().upper() != target_asset:
                    continue
                other = set(_normalize(text).split())
                score = len(words & other) / len(words | other)
                if score >= threshold:
                    matches.append({"ticket_id": ticket_id, "similarity": round(score, 4),
                                    "match_type": "exact" if normalized == _normalize(text) else "similar"})
            except (OSError, ValueError, UnicodeError):
                skipped += 1
    except OSError:
        return {**base, "error": "ticket_store_unavailable"}
    matches.sort(key=lambda m: (-m["similarity"], m["ticket_id"]))
    return {**base, "status": "candidates_found" if matches else "no_candidates",
            "matches": matches[:max_results], "total_matches": len(matches),
            "scanned_records": scanned, "skipped_records": skipped,
            "review_required": bool(matches),
            "notice": "Candidates only; no ticket was created or changed. No match does not authorize creation."}
