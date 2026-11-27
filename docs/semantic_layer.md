# Semantic Layer: Crowdfund Compass (Kickstarter) — v1.7 (proposed), 27.11.2026

Says what we mean by our data. Never change a definition silently; if a metric is not defined here, propose it and ask first.
v1.0–v1.2 approved by Fedor on 16.11. Changes in v1.3: title capitalisation dropped (32 features), goal rule, "most likely" value, verdict rule, neutral first-campaign display. Change in v1.4 (approved by Fedor on 25.11): "most likely" renamed "middle estimate"; the coach claim is always stated as the result of a re-weighted test on 2025 campaigns. Change in v1.5 (approved by Fedor on 25.11): verdict and coaching slots separated; gains measured on the middle estimate; range ends named by source. Change in v1.6 (approved by Fedor on 26.11, after Nico's examiner review): the round-goal flag keeps the plan's own value when the app tests other goals; the recommended goal and the Goal optimizer table stay scored exactly, as in Check-up.
Data: 24 Web Robots scrapes of public Kickstarter listings (2016-03 to 2026-11), merged by `merge_v2.py` into one row per project. Official benchmark: Kickstarter stats page, last updated 01.01.2026.

## 1. Terms: file vs. business

| In the file | What we mean |
|---|---|
| One row | One **Kickstarter project**, in the latest state any scrape saw it in (deduplicated on `id`) |
| `state` | `successful` = reached its goal by the deadline; `failed` = did not. Other states have no usable outcome |
| `goal` | Funding goal in the project's own currency. Always convert: `goal × static_usd_rate` |
| `launched_at`, `deadline`, `created_at` | Unix seconds, UTC. `created_at` = when the creator started the draft |
| `name`, `blurb` | Title and short pitch **as of the last scrape**. 3.2% of funded and 1.5% of failed campaigns changed the title between a live sighting and the end |
| `cat_id`, `cat_slug` | The category key. `cat_slug` = `"parent/subcategory"`, e.g. `art/painting` |
| `parent_category` | First part of `cat_slug`, mapped to the 15 official names ("main category" in the app) |
| `subcategory` | Display name only. 7 names exist under several parents: use `cat_id` |
| `has_video`, `prelaunch_activated` | 1 / 0 when known. **Missing** when the project was last listed before the 2023-12-14 scrape. Missing is never "no" |
| `scrape`, `first_scrape`, `n_scrapes` | Data-quality fields, **never features** |
| Capped category | One of the 29 categories with ≥ 2,150 projects listed in the 2025-12-18 scrape (`features.CAPPED_CAT_IDS`). For reporting, **never a feature** |

## 2. Entities

| Entity | Columns | Notes |
|---|---|---|
| Project (campaign) | `id`, `name`, `blurb`, `slug` | 488,967 rows; 430,082 finished |
| Creator | `creator_id` | 323,236 creators with a finished project; 43,923 with more than one. Never shown or stored in the app |
| Category | `parent_category` → `cat_id` | 15 main categories, 174 category ids (164 names); 163 have both funded and failed campaigns in 2025 and count in the within-category AUC |
| Place | `country`, `city` | 25 countries. City is not used (no signal); similar campaigns show category, country, year and goal |
| Time | `launched_at` | Every "by year/month" statement uses the **launch date** |

## 3. General rules

1. **Finished projects only.** Every outcome metric uses `state ∈ {successful, failed}`.
2. **Before-launch rule.** A feature may only use what the founder knows at launch. Creator history uses only campaigns whose deadline is before this campaign's launch. The category median goal uses campaigns that ended in the 12 months before the first day of the launch month.
3. **Sample rates are not Kickstarter rates.** Of campaigns ended before 01.01.2026 we hold 246,842 funded and 162,910 failed; the official stats count 292,062 funded and 391,396 unsuccessful. Kickstarter's "unsuccessful" is everything launched that is neither funded nor live (685,397 launched = 292,062 + 391,396 + 1,939 live), so it includes cancelled and suspended projects; counted the same way we hold 185,448. So we hold about 85% of all funded projects but about 47% of the unsuccessful ones (v1.7, proposed on 27.11; until then stated as 42%, which counts only our failed projects). The model's outcome stays funded vs failed: cancelled and suspended projects are in neither training nor test. Any rate from this file is labelled "in our sample" and is never shown in the app as a fact about Kickstarter. This includes funded rates by category and by creator track record.
4. **Video / pre-launch rule.** `has_video` and `prelaunch_activated`, and any "known/missing" flag for them, are used only in a model trained on launches from 2023-01-01 on.
5. **Outliers are flagged, not deleted.**
6. **Test window.** Test years are launches of 2025 and of January–June 2026. Launches from July 2026 on are excluded everywhere: they ended after the last full crawl (12.08.2026).
7. **Crawls.** Full: about 185,000–211,000 projects. Partial: 2021–2023 scrapes, 2026-10-12, 2026-11-16.
8. **Headline metric: AUC within category** (inside each `cat_id` with both funded and failed campaigns in the test year, averaged by size; 163 categories in 2025), with AUC within main category and overall AUC next to it.
9. **Results are also reported separately** for the 29 capped categories and the rest.
10. **Chances are shown as a range with a middle.** Two estimates: the calibrated probability in our sample, and the same after shifting the odds, per main category, by official odds ÷ sample odds. The lower value and the upper value are simply the smaller and the larger of the two (the official one is lower except in Dance; see 13a). "Middle estimate": halfway between the two on the log-odds scale, checked against one public figure only. Never called "most likely". The two ends are scenarios, with no measured guarantee that the true chance lies between them.
11. **Founder history stays in the model**, but its raw funded percentages are not shown. A first campaign is shown neutrally, without a score.
12. **Goal rule.** The model may only learn that a higher goal lowers the chance.
13. **Verdict and coaching slots (v1.5, 25.11).** Verdict, the same on every screen: Rethink = lower value below 11.5% (v1.7, proposed by Nico on 27.11, to be confirmed by Fedor when merging: the verdict "Coach first" is renamed, because it was mistaken for the coaching slots; rule and numbers unchanged); Adjust = otherwise, if one change adds at least 5 points to the middle estimate (before rounding); Launch = otherwise. Launch therefore means "not among the riskiest, and no single change adds 5 points": it is not a promise, and a Launch plan can still have a low range. Coaching slots (Coach view): the riskiest teams ranked by the lower value, up to the coach's capacity (default 30%); slots never change a verdict.
13a. **Range ends are named by source** ("from our data", "adjusted to official rates"), not by position: in Dance the adjusted estimate is the higher one.
14. **Advice is association.** A suggested change is worded "campaigns that did this were funded more often", never as a promise.

## 4. Metrics

| Metric | Formula | Rule |
|---|---|---|
| Success (target) | 1 if `state == successful`, else 0 | Finished only |
| Success rate (in sample) | successful ÷ finished, by launch date | Rule 3 label |
| Goal (USD) | `goal × static_usd_rate` | Modelled as log10. The round-goal flag is computed in the project's own currency in training, but on the USD amount in the app (the app only asks for USD); when the app tests other goals (goal suggestions, Goal optimizer curve) the flag keeps the plan's own value, so the goal rule holds; the recommended goal and the three-goal table on the Goal optimizer are scored as Check-up scores that exact figure, and a goal is recommended only if it stays out of the riskiest group both ways, so Check-up never flags a recommended goal (v1.6; on 25.11 it was recomputed for every tested goal, which let a suggested goal win only because it landed on a round number, for example $9,000: +5.3 points against +1.8 at $8,999). Limit: a round goal figure by itself is worth about 3 points in the model's estimate for the example plan ($15,000: 40.4%, $14,999: 37.0%); this is a pattern in past campaigns, not advice |
| Campaign length | (`deadline − launched_at`) ÷ 86,400, days | |
| Preparation time | (`launched_at − created_at`) ÷ 86,400, days | |
| Goal ratio | log10 of Goal (USD) ÷ median Goal (USD) of the same `cat_id`, campaigns ended in the 12 months before the first day of the launch month | Main category if fewer than 20 prior campaigns |
| Creator prior campaigns / prior success rate | Count of the same `creator_id`'s campaigns that ended before launch, cancelled and suspended included; success rate = funded ÷ (funded + failed). The app asks for all ended campaigns, of which funded, of which cancelled or suspended (since 25.11) | Earlier failed campaigns are under-recorded |
| Text score | Output of a logistic regression on TF-IDF of title + blurb, fitted on training data only | Reflects what is being made (product type), not writing quality. Not a lever |
| Area score | Share of reference campaigns (launches 2023–24) with a lower SHAP sum in that area, 0–100 | 0–25 weak, 26–60 to improve, 61–100 strong |
| Official funding rate | Kickstarter's all-time success rate per main category | The only category rate shown as fact |

Dropped from the model: crowding (three features), city size, category norms (`cat_rate_12m`, `cat_trend`, `log_cat_n_12m`), title capitalisation (`name_caps_share`). Final feature set: 32 (30 without video / pre-launch page).
