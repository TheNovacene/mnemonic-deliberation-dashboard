from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pandas as pd
import srt
import webvtt


# ---------------------------
# Transcript loading utilities
# ---------------------------

def load_transcript(path: str) -> pd.DataFrame:
    """
    Load a transcript from .vtt, .srt, or plain .txt into a normalised DataFrame.

    Returns a DataFrame with columns:
      - ts_start: str | None  (HH:MM:SS.mmm for VTT/SRT; None for plain text)
      - ts_end:   str | None
      - speaker:  str         (inferred from "Speaker: text" if present; else "Unknown")
      - text:     str         (HTML tags stripped; whitespace normalised)
    """
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".vtt":
        rows = []
        for cue in webvtt.read(path):
            rows.append({
                "ts_start": cue.start,
                "ts_end": cue.end,
                "speaker": infer_speaker(cue.text),
                "text": clean_text(cue.text),
            })
        return pd.DataFrame(rows)

    if suffix == ".srt":
        with open(path, "r", encoding="utf-8") as f:
            subs = list(srt.parse(f.read()))
        rows = []
        for s_ in subs:
            rows.append({
                "ts_start": str(s_.start),
                "ts_end": str(s_.end),
                "speaker": infer_speaker(s_.content),
                "text": clean_text(s_.content),
            })
        return pd.DataFrame(rows)

    # --- robust plain-text fallback (one line per turn; engine-agnostic) ---
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        # splitlines() is safe across platforms and avoids pandas engine quirks
        lines = [ln.strip() for ln in f.read().splitlines() if ln.strip()]

    rows = []
    for line in lines:
        # naive split pattern: "Speaker: text"
        m = re.match(r"^([^:]{1,40}):\s*(.+)$", line)
        spk, txt = (m.group(1), m.group(2)) if m else ("Unknown", line)
        rows.append({
            "ts_start": None,
            "ts_end": None,
            "speaker": spk,
            "text": clean_text(txt),
        })
    return pd.DataFrame(rows)


def infer_speaker(txt: str) -> str:
    """Infer 'Speaker' from a leading 'Name: ...' pattern; else return 'Unknown'."""
    m = re.match(r"^\s*([A-Za-z][A-Za-z0-9_ -]{0,30}):", txt)
    return m.group(1) if m else "Unknown"


def clean_text(t: str) -> str:
    """Strip simple HTML tags and compress whitespace."""
    t = re.sub(r"<[^>]+>", " ", t)      # strip tags
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ---------------------------
# Feature enrichment
# ---------------------------

def duration_seconds(row) -> float:
    """
    Compute the duration in seconds for a row with ts_start/ts_end strings like HH:MM:SS.mmm.
    Returns 0.0 if timestamps are missing or unparsable.
    """
    def to_seconds(s: Optional[str]) -> Optional[float]:
        if s is None:
            return None
        try:
            h, m, rest = s.split(":")
            return int(h) * 3600 + int(m) * 60 + float(rest)
        except Exception:
            return None

    a = to_seconds(row.get("ts_start"))
    b = to_seconds(row.get("ts_end"))
    if a is None or b is None:
        return 0.0
    return max(0.0, b - a)


def add_basic_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived columns:
      - duration_s: float seconds (0.0 when not available)
      - tokens: int (simple whitespace token count)
    """
    df = df.copy()
    df["duration_s"] = df.apply(duration_seconds, axis=1)
    df["tokens"] = df["text"].astype(str).str.split().apply(len)
    return df


# ---------------------------
# Mentimeter helper
# ---------------------------

def load_mentimeter_csv(path: str) -> pd.DataFrame:
    """Load a Mentimeter CSV export safely; return empty DataFrame on failure."""
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
