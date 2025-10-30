import os
import streamlit as st
import pandas as pd
import plotly.express as px

from src.preprocess import load_transcript, add_basic_fields, load_mentimeter_csv
from src.metrics import energy_E, symbolic_coherence_s, connection_c2, impact_I, per_minute_timeline
from src.policy import load_policies, pp_delta
from src.utils import save_signature, now_iso


def summarise_mentimeter(dfm: pd.DataFrame) -> dict:
    """Heuristic summary of a Mentimeter export."""
    if dfm is None or dfm.empty:
        return {
            "questions": 0,
            "total_votes": 0,
            "participation_index": 0.0,
            "confidence_mean": None,
            "opt_out_selected": None,
            "top_risk": None,
        }

    # normalise columns
    cols = {c.lower().strip(): c for c in dfm.columns}
    get = lambda key: dfm[cols[key]] if key in cols else pd.Series(dtype=object)

    # base numbers
    questions = len(dfm)
    votes = pd.to_numeric(get("votes"), errors="coerce").fillna(0).sum()

    # crude participation index: scale total votes into [0,1]
    participation_index = float(min(1.0, votes / 30.0))  # tweak 30 → expected audience size

    # confidence (scale) mean from top_result if numeric
    is_scale = get("type").astype(str).str.contains("scale", case=False, na=False)
    scale_vals = pd.to_numeric(get("top_result")[is_scale], errors="coerce")
    confidence_mean = float(scale_vals.mean()) if len(scale_vals) else None

    # opt-out yes/no
    yn_mask = get("type").astype(str).str.contains("yes", case=False, na=False)
    opt_out_selected = None
    if yn_mask.any():
        top = get("top_result")[yn_mask].astype(str).str.lower().iloc[0]
        opt_out_selected = (top == "yes")

    # risk top (multiple_choice + 'risk' in question)
    q_series = get("question").astype(str)
    mc_mask = get("type").astype(str).str.contains("multiple", case=False, na=False)
    risk_rows = dfm[mc_mask & q_series.str.contains("risk", case=False, na=False)]
    top_risk = None
    if not risk_rows.empty:
        top_risk = str(risk_rows[cols.get("top_result", "top_result")].iloc[0])

    return {
        "questions": int(questions),
        "total_votes": int(votes),
        "participation_index": participation_index,
        "confidence_mean": confidence_mean,
        "opt_out_selected": opt_out_selected,
        "top_risk": top_risk,
    }


# --- Streamlit page config ---
st.set_page_config(page_title="Mnemonic Deliberation Dashboard", layout="wide")
st.title("🧭 Mnemonic Deliberation Dashboard (MDD) — MVP")

# --- Uploaders ---
colL, colR = st.columns([2, 1])
tfile = colL.file_uploader("Upload transcript (.vtt / .srt / .txt)", type=["vtt", "srt", "txt"])
mfile = colR.file_uploader("Upload Mentimeter CSV (optional)", type=["csv"])

policies = load_policies("policies.json")

if tfile:
    # Preserve the original extension so load_transcript knows how to parse
    name = tfile.name or "_tmp_transcript.vtt"
    suffix = os.path.splitext(name)[1].lower() or ".txt"
    tmp_path = f"data/_tmp_transcript{suffix}"
    with open(tmp_path, "wb") as f:
        f.write(tfile.read())

    # --- Load + enrich transcript ---
    df = load_transcript(tmp_path)
    df = add_basic_fields(df)

    st.subheader("Transcript (preview)")
    st.dataframe(df.head(20), use_container_width=True)

    # --- Base metrics (before Mentimeter blend) ---
    E = energy_E(df)
    s = symbolic_coherence_s(df)
    c2 = connection_c2(df)
    I = impact_I(E, s, c2)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Energy (E)", f"{E:.2f}")
    m2.metric("Symbolic Coherence (s)", f"{s:.2f}")
    m3.metric("Connection² (c²)", f"{c2:.2f}")
    m4.metric("Impact / Identity (I)", f"{I:.2f}")

    # --- Mentimeter (optional) ---
    menti_summary = None
    if mfile:
        with open("data/_tmp_mentimeter.csv", "wb") as f:
            f.write(mfile.read())
        menti_df = load_mentimeter_csv("data/_tmp_mentimeter.csv")

        st.markdown("---")
        st.subheader("Mentimeter (live signals)")
        if not menti_df.empty:
            st.dataframe(menti_df, use_container_width=True)
            menti_summary = summarise_mentimeter(menti_df)

            # Quick stats
            cA, cB, cC, cD = st.columns(4)
            cA.metric("Questions", f"{menti_summary['questions']}")
            cB.metric("Total votes", f"{menti_summary['total_votes']}")
            cC.metric("Participation index", f"{menti_summary['participation_index']:.2f}")
            if menti_summary["confidence_mean"] is not None:
                cD.metric("Confidence (mean)", f"{menti_summary['confidence_mean']:.2f}")
            else:
                cD.metric("Confidence (mean)", "—")

            # Optional: blend participation into E
            e_blend = st.checkbox(
                "Blend participation into Energy (E) (adds 15%)",
                value=True,
                help="Lightly rewards live participation in the E score for this MVP."
            )
            if e_blend:
                E_original = E
                E = float(min(1.0, 0.85 * E + 0.15 * menti_summary["participation_index"]))
                I = impact_I(E, s, c2)
                st.info(f"Energy adjusted from {E_original:.2f} → {E:.2f} based on participation.")
        else:
            st.info("Mentimeter CSV loaded but no rows detected.")

    # --- Resonance Timeline (Plotly) ---
    st.markdown("---")
    st.subheader("Resonance Timeline")

    tl = per_minute_timeline(df)
    if not tl.empty:
        tl_long = tl.melt(
            id_vars=["block_start"],
            value_vars=["E", "s", "c2", "I"],
            var_name="metric",
            value_name="score"
        )
        fig = px.line(tl_long, x="block_start", y="score", color="metric")
        fig.update_layout(
            yaxis_range=[0, 1],
            xaxis_title="Turn block start",
            yaxis_title="Score",
            legend_title="Metric"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough turns for a timeline. Add a longer transcript for this view.")

    # --- Policy → Practice (PPΔ) ---
    st.markdown("---")
    st.subheader("Policy → Practice (PPΔ)")

    delta = pp_delta(df, policies)
    pp = pd.DataFrame([{"clause": k, **v} for k, v in delta.items()])
    st.dataframe(pp, use_container_width=True)

    # --- Mnemonic Signature Export ---
    st.markdown("---")
    st.subheader("Mnemonic Signature (export)")

    sig = {
        "session_meta": {
            "generated_at": now_iso(),
            "turns": int(len(df)),
            "speakers": int(df["speaker"].nunique())
        },
        "metrics": {"E": E, "s": s, "c2": c2, "I": I},
        "pp_delta": delta,
        "mentimeter_ingested": bool(mfile),
        "mentimeter_summary": menti_summary if menti_summary else None
    }

    if st.button("Save JSON signature"):
        h = save_signature(sig, "data/mdd_signature.json")
        st.success(f"Saved → data/mdd_signature.json\nSHA256: {h}")
        st.download_button(
            "Download signature.json",
            data=pd.Series(sig).to_json(),
            file_name="signature.json",
            mime="application/json"
        )

else:
    st.info("Upload a transcript to begin.")

# --- Footer / Attribution ---
st.markdown("---")
st.markdown("""
#### 🪶 About & Citation
**Mnemonic Deliberation Dashboard (MDD)**  
© 2025 [Kirstin Stevens](https://thenovacene.org) · *The Novacene*

This prototype operationalises the **Law of Mnemonic Expansion in a Living Universe**,  
bridging symbolic intelligence and applied AI ethics.  

**Licence:** [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)  
with st.expander("⚖️ Ethical Use Notice"):
    st.markdown("""
    This tool is part of the Verse-ality symbolic research field.  
    Use implies consent to honour attribution integrity, relational ethics,  
    and the spirit of non-commercial knowledge commons.  
    """)

**Cite as:**  
> Stevens, K. (2025). *Law of Mnemonic Expansion: Mnemonic Deliberation Dashboard (v0.1).* The Novacene.  

*Built with Streamlit · Hosted in the Cloud · Part of the Verse-ality research field.*
""")

