import json, hashlib, time
from pathlib import Path

def save_signature(payload: dict, out_path: str) -> str:
    p = Path(out_path)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    return h

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")
