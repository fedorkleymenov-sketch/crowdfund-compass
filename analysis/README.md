# Analysis, presentation and report sources

Everything needed to re-run the analysis and rebuild the deck and the report. The app itself lives in `app/`.

## Data (not in the repository)
The raw Web Robots scrapes and the merged tables are too large for GitHub. They are on Fedor's Mac:
- `~/Downloads/ks_scrapes/` — the 24 raw scrape files (plus the zip of 16.11.2026)
- `~/Downloads/ks_scrapes/merged_v2/` — `kickstarter_merged_v2_part1–8.parquet`, presence tables, `models/`

To rebuild the analysis tables in a new session: stage the merged parts from the Mac, then run
`pipeline/merge_v2.py` (only if starting from raw scrapes) → `pipeline/run_feat.py` (builds `features.parquet`, about 100 MB) →
`pipeline/stage3.py` (models) → `pipeline/stage4.py` / `stage4b.py` (explanation, verdict) → `pipeline/export_app.py` (writes `app/models/`).
Paths inside the scripts point to the original work folder (`/home/claude/work/v2/`); adjust them.

`models_M.joblib` (this folder) is the saved model bundle the later scripts load: XGBoost model, calibration, sample rates, text-model settings.

## Scripts in `pipeline/`
| Script | What it does |
|---|---|
| `merge_v2.py` | Merges the 24 scrapes into one row per project + presence table |
| `audit1–3.py`, `founder.py`, `leak.py`, `textleak.py` | Phase 1–2 audits: coverage vs official stats, founder-history recheck (695 rows), missingness leak test, title edits |
| `run_feat.py` | Builds the 32 features (uses `app/features.py`) |
| `stage1–3.py` | Feature tests, model comparison, tuning, final model |
| `stage4.py`, `stage4b.py` | Calibration, official-rate shift, SHAP, area scores, fixes, verdict, capacity tables |
| `stage5_gain.py` | 25.11: "what to change" figures with gains on the middle estimate (4,000 campaigns of 2025) |
| `stage6_rules.py` | 25.11: model vs simple rules at 30% capacity, 2025 re-weighted to the official mix |
| `stage7_frozen2026.py` | 25.11: retrospective re-test on Jan–Jun 2026 with paired bootstrap |
| `stage8_simple_rules.py` | 26.11: rules that look at the team (three questions, one-page scorecard) at 30% capacity, 2025 and Jan–Jun 2026; runs without the raw data (`app/models/similar.parquet`); output in `docs/simple_rules_output.txt` |
| `export_app.py` | Writes the model files the app uses |
| `mknb02–04.py`, `run_nb.py` | Generate and execute notebooks 02–04 |

## Tests in `tests/`
- `test_pages.py` — runs all 7 app pages with Streamlit's AppTest (`python test_pages.py new`), prints exceptions per page.
- `test_numbers.py` — prints the key numbers shown on Check-up, Coach view, Goal optimizer, Similar campaigns (compare before/after a change).
- `shot_inter.py` — full-page screenshots of a local app (`streamlit run app/app.py` on port 8501, then `python shot_inter.py 1360 1100 "Check-up" "Coach view"`), with the Inter font injected.

## Presentation (`../presentation/`)
- `build.js` — generates `Crowdfund_Compass_Group11.pptx` with pptxgenjs (`node build.js`). It needs the pptx skill's `apply_theme.js` (path on line 2; adjust in a new session). Slide notes come from `voiceover.json`.
- `voiceover.json` / `voiceover_script.md` — the 15-minute script (13 recorded slides + 2 backup).
- `pitch_script_3-5min.md` — the live pitch.
- `s_check.png`, `s_coach.png`, `s_coach_big.png` — app pictures on slides 4 and 12.

## Report (`../report_source/`)
- `build_report.py` — generates `Crowdfund_Compass_Full_Report.pdf` with reportlab (`python build_report.py`).
