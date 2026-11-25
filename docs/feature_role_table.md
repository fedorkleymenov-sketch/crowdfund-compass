# Feature role table — Crowdfund Compass (final, 16.11.2026)

First step before any training (as in the professor's VibeCodingML). Rule: a feature must be known to the founder **before launch**.

## 1. Columns of the merged table

| Column | Role | Reason |
|---|---|---|
| `state` | **Target** (successful = 1, failed = 0) | The outcome. Other states are dropped |
| `id`, `slug` | Excluded (keys) | Identifiers only |
| `name` | Feature (text) | Title is written before launch |
| `blurb` | Feature (text) | Short pitch, written before launch |
| `goal` + `static_usd_rate` | Feature → goal in USD | Founder's choice. The rate is fixed at launch |
| `currency` | Excluded | Duplicates `country` |
| `country` | Feature | Known before launch |
| `city`, `loc_type`, `loc_state` | Not a model feature | City size had no signal; city is not used in the app |
| `cat_id` / `cat_slug`, `parent_category` | Feature (category labels) | Founder's choice |
| `subcategory` | Display only | Name is ambiguous for 7 names |
| `creator_id` | Excluded as a column; **source** of founder history | History only from campaigns ended before this launch. Never shown in the app |
| `created_at` | Feature → preparation time | Known at launch |
| `launched_at` | Feature → month, weekday, Christmas window; **split key** | Founder's choice |
| `deadline` | Feature → campaign length | Set at launch |
| `has_video`, `prelaunch_activated` | Feature, only in the model trained on launches from 2023 on | Known only for projects last listed from 2023-12 on |
| "known / missing" flag for the two fields | **Excluded: leakage** | Equals "last listed in 2023-12 or later", which depends on the outcome |
| `staff_pick` | **Excluded** | "Projects We Love" is usually awarded after launch |
| `spotlight` | **Excluded: leakage** | Only available to funded projects |
| `pledged`, `usd_pledged`, `backers_count` | **Excluded: leakage** | Results of the campaign |
| `state_changed_at` | **Excluded: leakage** | Set when the campaign ends |
| `scrape`, `first_scrape`, `n_scrapes` | **Excluded: leakage** | When and how often a project is listed depends on its outcome |

## 2. Final features (32)

| Area | Features |
|---|---|
| Ambition (5) | `log_goal_usd`, `goal_ratio`, `log_goal_per_day`, `duration_days`, `goal_is_round` |
| Timing (4) | `launch_month`, `launch_weekday`, `holiday_window`, `log_prep_days` |
| Pitch (12) | `name_len`, `name_words`, `blurb_len`, `blurb_words`, `name_has_digit`, `name_has_symbol`, `blurb_flesch`, `blurb_sentiment`, `kw_exclaim`, `kw_you`, `kw_we`, `kw_new_first` |
| Founder (5) | `creator_prior_n`, `creator_prior_funded`, `creator_prior_rate`, `first_timer`, `log_days_since_last` |
| Presentation (2) | `has_video`, `prelaunch_activated` |
| Product type and market (4) | `cat_id`, `parent_c`, `country_c`, `text_score` |

Built and dropped: crowding (`crowd_prev7`, `crowd_ratio`, `live_same_cat`), `city_size`, category norms (`cat_rate_12m`, `cat_trend`, `log_cat_n_12m`), `name_caps_share`. Reasons in `semantic_layer.md`.

## 3. The no-leak test (video and pre-launch page)
Run on 16.11 with 10 simple features and XGBoost.
1. **Structural:** the all-years model's feature list contains none of the excluded columns (asserted in code).
2. **The leak is real:** train ≤ 2021, evaluate on 2022 launches (80% known; funded 67.8% if known, 97.3% if unknown). AUC 0.901 without the fields, 0.915 with a known-flag, 0.920 with the two fields left empty where unknown. On 2024, where everything is known, the same three models score 0.841, 0.803 and 0.828: the "gain" was the scraper, and it hurts on new data.
3. **Invariance:** scrambling `has_video`, `prelaunch_activated` and the known-flag changes the all-years model's predictions by exactly 0.
4. **Final model:** trained only on launches from 2023 on, where both fields are known for every row (1 row dropped). The known-flag has a single value, so it cannot carry information.

What the test does **not** prove: that the sample itself is unbiased. Missing failed campaigns still inflate rates and AUC.

## 4. Other leak checks
- History features recomputed with independent slow code on 695 sampled rows: 0 mismatches.
- Text: titles and blurbs are from the last scrape; edits during the campaign are rare (3.2% of funded, 1.5% of failed) and none were seen after the end.
- Text score: training rows are scored out-of-fold.
