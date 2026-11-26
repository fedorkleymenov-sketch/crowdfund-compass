# Model results — Crowdfund Compass (final, 16.11.2026)

Code: `app/features.py`, `app/modeling.py`, notebook `notebooks/03_models.ipynb`.
All figures are computed on our sample, which over-represents funded campaigns. **Headline metric: AUC within category** (inside each category that has both funded and failed campaigns in the test year, averaged by size: in 2025, 163 categories with 26,508 of the 26,533 campaigns).

## 1. Design
- Splits by launch date: train 2023–2024 (43,904 campaigns; video and pre-launch page known for all), validation 2024 for selection and calibration (model trained on 2023), test 2025 (26,533; 70.8% funded) and January–June 2026 (12,990; 74.9%).
- 32 features: Ambition 5, Timing 4, Pitch 12, Founder 5, Presentation 2, labels 3 (category, main category, country), plus `text_score` (TF-IDF on title + blurb → logistic regression, scored out-of-fold in training).
- Dropped on the way: crowding (3) and city size (no signal inside a category), category norms (3; within-category AUC higher without them on two splits that do not touch the test years: 0.840 vs 0.823 and 0.828 vs 0.820), title capitalisation (made the Pitch score depend on Title Case).
- Tuning: `GridSearchCV` with `TimeSeriesSplit` (class). XGBoost best: depth 3, 400 trees, learning rate 0.03. Tree: depth 9, minimum leaf 100. Forest: 300 trees, minimum leaf 5.
- **Final model:** the tuned XGBoost plus one rule (beyond class): a higher goal may only lower the chance, never raise it. Without the rule the model said in 6% of campaigns that lowering the goal lowers the chance.

## 2. Results table (all models trained on 2023–24, evaluated on the two test periods)

| Model | Class? | AUC within category 2025 | within parent | overall | Accuracy | Precision | Recall | F1 | Brier | AUC within category Jan–Jun 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| Baseline: always "funded" | – | 0.500 | 0.500 | 0.500 | 0.708 | 0.708 | 1.000 | 0.829 | 0.207 | 0.500 |
| Baseline: category funding rate | – | 0.500 | 0.722 | 0.825 | 0.790 | 0.804 | 0.929 | 0.862 | 0.148 | 0.500 |
| XGBoost, 6 Kaggle-style features | class | 0.753 | 0.817 | 0.861 | 0.804 | 0.812 | 0.941 | 0.872 | 0.135 | 0.743 |
| Decision tree, depth 3 | class | 0.778 | 0.822 | 0.862 | 0.806 | 0.868 | 0.856 | 0.862 | 0.132 | 0.783 |
| Decision tree (grid search) | class | 0.823 | 0.863 | 0.895 | 0.835 | 0.851 | 0.929 | 0.888 | 0.116 | 0.829 |
| Logistic regression | class | 0.857 | 0.894 | 0.919 | 0.854 | 0.866 | 0.939 | 0.901 | 0.103 | 0.864 |
| Random forest (grid search) | class | 0.858 | 0.890 | 0.917 | 0.850 | 0.860 | 0.942 | 0.899 | 0.105 | 0.863 |
| XGBoost (grid search) | class | 0.859 | 0.891 | 0.917 | 0.850 | 0.860 | 0.941 | 0.899 | 0.105 | 0.867 |
| **XGBoost + goal rule — final model** | class + rule | **0.859** | 0.891 | 0.917 | 0.849 | 0.860 | 0.941 | 0.898 | 0.105 | **0.866** |
| LightGBM + Optuna | beyond class | 0.866 | 0.900 | 0.924 | 0.857 | 0.869 | 0.940 | 0.903 | 0.100 | 0.874 |

Confusion matrix, final model, 2025, threshold 0.5: failed and predicted failed 4,853 · failed but predicted funded 2,885 · funded but predicted failed 1,118 · funded and predicted funded 17,677. The model finds 63% of the failures (4,853 of 7,738); when it says "will fail" it is right 81% of the time.

## 3. Checks
**All years (A) vs recent years (M), AUC within category**

| Evaluated on | A, tuned as M | A, deeper trees | M without video/pre-launch | M with video/pre-launch |
|---|---|---|---|---|
| 2024 | 0.828 (359k rows) | 0.835 | 0.832 (18k) | 0.840 |
| 2025 | 0.841 (385k rows) | 0.852 | 0.850 (44k) | 0.859 |

Two recent years do as well as all history; video and pre-launch page add about 0.009.

**Walk-forward (no text, no video/pre-launch), AUC within category: all earlier years / last 2 years only**
2019: 0.787 / 0.788 · 2020: 0.801 / 0.801 · 2021: 0.802 / 0.802 · 2022: 0.822 / 0.812 · 2023: 0.815 / 0.820 · 2024: 0.818 / 0.827 · 2025: 0.842 / 0.847 · Jan–Jun 2026: 0.855 / 0.861.

**Capped vs other categories (final model, AUC within category):** 2025: 0.866 (15,094 campaigns, 78.4% funded) vs 0.850 (11,439; 60.8%). Jan–Jun 2026: 0.879 vs 0.848.

**By main category, 2025 (AUC within category):** Comics 0.901, Fashion 0.887, Technology 0.884, Design 0.881, Games 0.877, Art 0.870, Publishing 0.863, Crafts 0.854, Photography 0.850, Music 0.810, Food 0.804, Journalism 0.788, Film & Video 0.757, Dance 0.756, Theater 0.752.

**Business metric:** if a coach takes the 30% of a cohort the model rates riskiest, the share of all later failures they include is 75.9% in 2025 and 81.0% in Jan–Jun 2026 in our observed sample, ranking by the raw score (74.7% in 2025 ranking by the lower value, as the app does) (random: 30%; category-rate baseline: 62.4% / 66.3%; 6 features: 67.4% / 69.6%). Inside every category: 52%. In a cohort with Kickstarter's official mix of outcomes the figure is 51% (see `explanation_and_verdict.md`).

## 4. Probabilities
- **Calibration (beyond class):** Platt scaling learned on 2024. Brier on 2025: 0.105 → 0.103. After calibration, predicted chances are within 5 points of observed rates in every tenth of the scale (before: up to 9.5).
- **Level correction (beyond class):** per main category, odds × [official odds ÷ sample odds], with Kickstarter's official all-time rates (stats page, 01.01.2026). 2025 test: mean chance 69% in our sample → 52% corrected. Median width of the range 14.5 points.
- **Check of the correction:** after re-weighting the 2025 sample to the official mix, the mean corrected chance per main category is on average 6 points from the official rate, mostly below it.
- **Middle of the range:** tabletop games launched in 2024, official 80% funded (5,314 of 6,646). Our lower value 66%, middle 78%, upper 86%. One benchmark only.
- **Down-weighting instead of shifting** gives the same within-category AUC (0.859) and probabilities that correlate 0.98 with the shifted ones (not an identical queue). The shift is kept: simpler to explain.

## 5. Support models
- **Money raised (class: linear regression on log10 USD):** funded campaigns only: R² 0.675, typical error factor ×1.8 (category-median baseline ×2.7). Not used in the app.
- **Similar campaigns (10 nearest neighbours in the same main category, beyond class):** the funded share of the neighbours alone predicts 2025 outcomes with AUC within category 0.791.
- Archetypes (k-means) were tested and cut: silhouette 0.13–0.17.

## 5b. Equal-capacity comparison with simple rules (added 25.11)
Coach capacity 30%, 2025 launches re-weighted to Kickstarter's official mix (56% fail). Share of all failures reached / share of selected teams that failed: random 30.0% / 56.0%; lowest official main-category rate 37.7% / 70.4%; highest goal for the category 37.3% / 69.7%; lowest 2023–24 subcategory rate in our data 44.5% / 83.0%; **our model (ranked by the lower value) 51.1% / 95.4%**; maximum possible 53.6% / 100%. Per 100 campaigns: about 29 failing teams found by the model against 25 with the best category rule and about 27 with a one-page scorecard (next paragraph). Ties at the cutoff are taken proportionally. Calendar check: using only 2023–24 outcomes resolved before 1 January 2025, the rule reaches 44.3% (instead of 44.5%). Script `stage6_rules.py`; first computed by an outside review (ChatGPT) and reproduced here with the same result. This measures who gets flagged, not how much coaching helps.

**Rules that look at the team (added 26.11 after an independent examiner review).** The rules above only use the category or the goal, so inside a category they cannot tell two teams apart. A coach's own rule of thumb can. Same capacity, weighting and tie rule; rules fitted on 2023–24 launches only. Share of all failures reached, 2025 / January–June 2026: highest goal in USD first 42.6% / 40.9%; three yes/no questions (first campaign, no pre-launch page, goal above $10,000) 45.2% / 45.0%; **scorecard = subcategory rate + the three questions 47.6% / 47.9%** (88.8% / 89.6% of the selected teams failed); our model 51.1% / 51.1%; maximum 53.6% / 53.5%. Per 100 campaigns: about 29 failing teams with the model, 27 with the scorecard, 25 with the best category rule. The scorecard beats the best category rule by 3.1 points in 2025 (95% paired bootstrap 2.8 to 3.5) and 2.9 points in 2026 (2.4 to 3.5); the model is 3.5 and 3.2 points above the scorecard (no interval: the scorecard runs on the slim table in the repository, the model's per-campaign predictions need the raw data). Honest reading: against a rule a coach could keep on one page, the model adds about two failing teams per 100, not four. Script `notebooks/stage8_simple_rules.py`, which runs without the raw data; its output is in `docs/simple_rules_output.txt`.

**Retrospective re-test on January–June 2026 (added 25.11, corrected after the second review).** The model, its calibration, the ranking score, the 30% capacity and the 11.5% cut were all fixed on 16.11, on 2025 data; all model inputs were known before 2026 (official rates of 1 January 2026). Disclosure: this is a retrospective re-test, not an untouched one. 2026 H1 had already been inspected before 16.11 in notebook 03 (AUC 0.866, model comparisons, and a 30%-capacity figure of 81.0% failures reached in the observed sample). No rule or setting was chosen on 2026, but the files cannot prove that nothing was influenced by it. 12,990 launches, re-weighted to the official mix (56.1% fail). Failures reached / selected that failed: random 30.0% / 56.1%; official main-category rate 37.9% / 70.8%; highest goal for the category 35.8% / 67.0%; subcategory rate 2023–24 **45.0% / 84.2% (the strongest category rule)**; subcategory rate 2023–25 44.6% / 83.4%; the same with only outcomes resolved before 1 January 2026 44.9%; **frozen model 51.1% / 95.7%**; maximum 53.5%. Model minus the strongest category rule: **+6.1 points** (difference on the full sample; 95% paired bootstrap interval 5.5 to 7.0). Against the 2023–25 rule: +6.6 (5.9 to 7.2); against the calendar-purged 2023–25 rule: +6.3 (5.7 to 7.0). The interval resamples campaigns with the fitted model and the re-weighting held fixed; it does not cover repeated creators, unseen failures, uncertainty in the official rates, retraining or the effect of coaching. The fixed single check-up cut flags 27.1% of the re-weighted cohort (target 30%), and 96.3% of those failed. Script `stage7_frozen2026.py`.

## 6. Honest reading
1. The model clearly beats both baselines and the 6-feature version (0.753 → 0.859).
2. **The model family hardly matters.** Logistic regression equals XGBoost and the forest; LightGBM + Optuna adds 0.007. The features carry the result.
3. **More history does not help** inside a category: 44,000 recent campaigns do as well as 385,000 from all years.
4. **The text score is the strongest feature, and it captures what is being made**, not how well it is written (tarot, 5e, comic, enamel pins vs app, platform, software, podcast).
5. **Scores are still inflated.** Within-category AUC rises over the walk-forward years (0.79 in 2019 to 0.86 in 2026, with a dip in 2023) and is higher in capped categories. The failed campaigns we hold are the visible ones. We cannot measure the remaining bias.
6. Titles and blurbs come from the last scrape; 3.2% of funded and 1.5% of failed campaigns changed their title between a live sighting and the end.
7. The level correction is rough: official rates are all-time averages per main category.
8. **The 2025 test year was not used only once.** The models were evaluated on it on 16.11, the final model was then retrained without title capitalisation (33 → 32 inputs; AUC within category 0.8584 → 0.8587), and the 11.5% cut and the rule comparisons were computed on it. No model setting was chosen on 2025, but it is not an untouched test set.
9. **Against a one-page scorecard the model's lead is about 3 points of failures reached, not 6** (section 5b).
