from __future__ import annotations
import json, pandas as pd
from pathlib import Path

def load_policies(path="policies.json") -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def pp_delta(df: pd.DataFrame, policies: dict) -> dict:
    text = " ".join(df["text"].astype(str)).lower()
    out={}
    for corpus, clauses in policies.items():
        for cid, meta in clauses.items():
            score = 0.0
            if meta["duty"] in text:
                score += 0.35
            for syn in meta.get("synonyms",[]):
                if syn.lower() in text: score += 0.2
            status = "ignored"
            if score >= 0.7: status="addressed"
            elif score >= 0.4: status="ambiguous"
            out[cid] = {
                "duty": meta["duty"],
                "status": status,
                "score": round(min(0.99, score), 2)
            }
    return out
