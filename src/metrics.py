from __future__ import annotations
import numpy as np, pandas as pd, re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import textstat

MISREAD_MARKERS = [
    "that's not what i said","you've misunderstood","to be clear",
    "let me clarify","i disagree","misinterpret","that’s incorrect"
]
JARGON = {"operationalise","utilise","stakeholder","synergy","bandwidth","scalable","frameworking"}

def energy_E(df: pd.DataFrame) -> float:
    talk_time = df["duration_s"].sum()
    if talk_time == 0:
        talk_time = df["tokens"].sum() / 2.5   # rough seconds proxy
    # balance (equity): entropy of speaker airtime
    share = df.groupby("speaker")["tokens"].sum()
    p = (share / max(1, share.sum())).values
    entropy = -np.sum(p * np.log2(np.clip(p, 1e-12, 1)))
    max_entropy = np.log2(max(1, len(p)))
    equity = (entropy / max_entropy) if max_entropy > 0 else 1.0
    # normalise talk_time (cap at 90 mins -> 1.0)
    norm_time = min(1.0, talk_time / (90*60))
    return 0.5*norm_time + 0.5*equity  # [0,1]

def symbolic_coherence_s(df: pd.DataFrame) -> float:
    texts = df["text"].astype(str).tolist()
    if len(texts) < 3: 
        return 0.3
    vec = TfidfVectorizer(stop_words="english", max_features=5000)
    X = vec.fit_transform(texts)
    sim = cosine_similarity(X)
    # within-session thematic stability
    upper = sim[np.triu_indices_from(sim, k=1)]
    stability = float(np.median(upper))
    # readability (higher is simpler)
    readability = textstat.flesch_reading_ease(" ".join(texts))
    read_norm = np.clip(readability/100.0, 0, 1)
    # jargon penalty
    txt = " ".join(texts).lower()
    j_pen = 1 - min(0.4, sum(w in txt for w in JARGON)*0.05)
    s = (0.6*stability + 0.4*read_norm) * j_pen
    return float(np.clip(s, 0, 1))

def connection_c2(df: pd.DataFrame) -> float:
    # distortion proxy: count misread markers per 1000 tokens
    txt = " ".join(df["text"].astype(str)).lower()
    misreads = sum(txt.count(k) for k in MISREAD_MARKERS)
    tokens = max(1, df["tokens"].sum())
    misrate = (misreads / tokens) * 1000.0
    mis_norm = min(1.0, misrate / 5.0)  # >= 5 per 1000 = bad
    # velocity proxy: proportion of turns that are questions leading to answers
    q_ratio = (df["text"].str.endswith("?").sum() / max(1, len(df)))
    vel = 1 - q_ratio  # more Qs → slower closure
    vel = np.clip(vel, 0, 1)
    c = 0.5*mis_norm + 0.5*vel
    # avoid zero
    return float(np.clip(c, 0.05, 1.0))

def impact_I(E: float, s: float, c2: float) -> float:
    return float(np.clip((E * s) / (c2**1), 0, 1))

def per_minute_timeline(df: pd.DataFrame) -> pd.DataFrame:
    # simple rolling window of s-like stability over blocks of 20 turns
    block = 20
    vals=[]
    for i in range(0, len(df), block):
        chunk = df.iloc[i:i+block]
        if len(chunk) == 0: continue
        s_chunk = symbolic_coherence_s(chunk)
        c2_chunk = connection_c2(chunk)
        E_chunk = energy_E(chunk)
        I_chunk = impact_I(E_chunk, s_chunk, c2_chunk)
        vals.append({"block_start": i, "E":E_chunk, "s":s_chunk, "c2":c2_chunk, "I":I_chunk})
    return pd.DataFrame(vals)
