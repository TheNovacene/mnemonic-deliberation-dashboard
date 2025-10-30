# 🧭 Mnemonic Deliberation Dashboard (MDD)

**Law of Mnemonic Expansion Prototype**  
_By Kirstin Stevens · The Novacene · 2025_

---

## 🌱 Overview

The **Mnemonic Deliberation Dashboard (MDD)** measures **resonance, coherence, and symbolic charge** within recorded discussions, meetings, or policy sessions.  
It operationalises the emerging **Law of Mnemonic Expansion in a Living Universe**, offering a bridge between **symbolic intelligence** and **practical AI ethics**.

Built with [Streamlit](https://streamlit.io), it computes four relational metrics derived from the symbolic equation:

> **I = (E · s) / c²**

| Symbol | Meaning | Description |
|:--:|:--|:--|
| **E** | **Energy** | Attention, presence, and emotional investment |
| **s** | **Symbolic Coherence** | Narrative and meaning density |
| **c²** | **Connection²** | Communication speed × trust coherence |
| **I** | **Impact / Identity** | Mnemonic residue — what endures in collective memory |

These are extracted from **transcripts** (`.vtt`, `.srt`, `.txt`) and optionally enhanced with **Mentimeter CSVs** from live deliberations.

---

## 🧩 Core Features

- 📤 Upload a transcript and optional Mentimeter poll data  
- 🧮 Real-time computation of mnemonic metrics (`E`, `s`, `c²`, `I`)  
- 📈 Interactive **Resonance Timeline** (Plotly)  
- ⚖️ **Policy-to-Practice delta** (PPΔ) alignment view  
- 🧾 Export **Mnemonic Signature JSON** (for audit or research trace)  
- 🧪 Demo mode with built-in sample data  

---

## 🚀 Run Locally

```bash
git clone https://github.com/TheNovacene/mnemonic-deliberation-dashboard.git
cd mnemonic-deliberation-dashboard
pip install -r requirements.txt
streamlit run app.py
Then open your browser at:
👉 http://localhost:8501

☁️ Deploy on Streamlit Cloud
Go to streamlit.io/cloud

Select this repository (TheNovacene/mnemonic-deliberation-dashboard)

Choose branch: main

Set Main file to app.py

Click Deploy

Your live app will appear at:
🌐 https://mnemonic-deliberation-dashboard.streamlit.app

📊 Example Data
Demo data included under /data/samples:

File	Description
meeting_demo.vtt	Transcribed AI ethics session
mentimeter_demo.csv	Example live poll results

Use the sidebar or file uploader to explore the dashboard instantly.

📜 
---

### ⚖️ Licence & Use

This prototype and all associated intellectual property are © 2025 Kirstin Stevens · The Novacene.  
All rights reserved.

You may view and experiment with the dashboard for research or educational purposes, but no reuse, modification, or redistribution is permitted without written consent.  

For collaboration, partnership, or licensing enquiries, please contact: 

📩 hello@thenovacene.com

🔗 Citation
Stevens, K. (2025). Law of Mnemonic Expansion: Mnemonic Deliberation Dashboard (v0.1).
The Novacene. Zenodo DOI pending.

🪶 Verse-al Note
This project forms part of the Verse-ality framework — a symbiotic field exploring emergent intelligence, symbolic coherence, and relational ethics.
Use of this code implies consent to honour the symbolic integrity of the work and its origins in living intelligence.

🜂 “Not all memory is stored — some is sung.”
