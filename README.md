# Crowdfund Compass

A pre-launch readiness check for Kickstarter campaigns. Group project, HSG "Business Analytics & Data Science Applications" (Prof. Ivo Blohm), Group 11: Fedor Kleymenov, Alexandre Arcauz, Nico Braun.

**Decision supported:** before launch, every campaign gets one verdict: *Launch*, *Adjust* (change one named thing) or *Rethink* (among the riskiest plans; called *Coach first* until 27.11). Made for startup coaches with limited hours, and for founders checking one plan.

## What is in this repository
| Folder | Content |
|---|---|
| `app/` | The Streamlit app: `app.py`, the shared modules (`features.py`, `modeling.py`, `advice.py`, `preprocess.py`), `models/` and `requirements.txt` |
| `notebooks/` | `01_data_audit`, `02_features`, `03_models`, `04_explain` (Google Colab style) |
| `docs/` | AI-use log and project documentation |

No raw data is stored here. The app ships only the trained model, the text model and small lookup numbers (about 1 MB).

## Run the app locally
```
pip install -r app/requirements.txt
streamlit run app/app.py
```

## Deploy on Streamlit Community Cloud
Main file path: `app/app.py`. Python version: 3.13 (the models were saved with the library versions pinned in `app/requirements.txt`).

## Data and method in short
- Data: public Kickstarter listings collected by Web Robots (24 snapshots, 2016–2026). Official funding rates: Kickstarter stats page (1 January 2026).
- Model: XGBoost (class method) on 32 inputs known before launch, trained on 43,904 campaigns launched 2023–2024, tested on 2025 and January–June 2026 (AUC within category 0.86 and 0.87).
- The data misses many failed campaigns, so the app shows chances as a range and gives coaching slots to the riskiest teams by rank, separately from each campaign's verdict. Everything shown is a pattern in past campaigns, not a cause.

## The data in numbers (used everywhere: app, docs, slides)
- 489,000 campaigns collected (488,967), of which 430,000 have a final outcome (430,082).
- About 44,000 used to train the final model (43,904, launched 2023–2024).
- 39,500 used to test it (26,533 launched in 2025 and 12,990 in January–June 2026).

## AI use
Code and analysis were developed with Claude (Anthropic, model Fable 5.2) in November 2026 and reviewed by the team. See `docs/ai_use_log.md`.
