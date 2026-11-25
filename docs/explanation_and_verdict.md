# Explanation, advice and verdict — Crowdfund Compass (final, 16.11.2026)

Code: `app/advice.py` (class `Advisor`), notebook `notebooks/04_explain.ipynb`. Model: final XGBoost with the goal rule (see `results.md`). Checks on the 2025 test year (26,533 campaigns). Everything describes associations in past campaigns, in our sample.

## 1. SHAP (beyond class)
*Why:* a coach needs reasons, not only a number. *To say out loud:* "SHAP splits each campaign's score into one piece per input: how much that input pushed the score up or down compared with an average campaign. The pieces add up exactly to the model's score."
- Additivity checked: largest gap between the sum of the pieces and the model's score is 0.00003.
- Share of the explanation by area (mean absolute SHAP): Product type and market 34%, Founder 23%, Ambition 19%, Presentation 12%, Timing 9%, Pitch 4%.
- **The four areas a founder can change before launch carry 43%; what is being made and who launches it carry 57%.**

## 2. Area scores (0–100)
Definition: add up the SHAP pieces of the area's features; the score is the share of reference campaigns (launches 2023–24, n = 43,904) with a lower sum. 50 = typical. Bands: 0–25 weak (red), 26–60 to improve (amber), 61–100 strong (green).
- "Market" is shown as "Product type: how your type of product has done". Product type and Founder are context, not levers.
- A first campaign is shown as "First campaign: no track record yet", without a score.
- No funded percentages by founder record or by category from our sample are shown.

Check on 2025, funded in sample by band (weak / to improve / strong): Ambition 38% / 75% / 86% · Timing 46% / 77% / 80% · Pitch 65% / 66% / 76% · Founder 41% / 62% / 94% · Presentation 55% / 68% / 82% · Product type 29% / 69% / 92%.

## 3. Chance range and "middle estimate"
- **Two estimates, named by source:** the calibrated chance in our sample, and the same shifted to Kickstarter's official per-category rates. The lower and upper value are simply the smaller and the larger of the two. The official one is lower for 99.8% of 2025 campaigns; only in Dance, where the official rate is higher than in our data, it is the upper value. **Middle estimate:** halfway between the two on the log-odds scale (called "most likely" before 25.11). There is no measured guarantee that the true chance lies between the two.
- Why the range is wide: our data holds about 85% of all funded campaigns but about 42% of the failed ones, so the true level is uncertain.
- One public benchmark for the middle: tabletop games launched in 2024, official 80% funded; lower 66%, middle 78%, upper 86%.

## 4. Verdict rule (approved 16.11, revised 25.11)
Since 25.11 the assessment of a campaign and the coach's slots are two separate things (an outside review showed that a hopeless campaign outside the coach's capacity could be labelled "Launch").
1. **Verdict, the same on every screen:** **Coach first** if the lower value is below 11.5% (where the riskiest 30% begin in a cohort with Kickstarter's official mix: computed as 11.6% on re-weighted 2025 data, fixed at 11.5% by decision on 16.11; so the verdict mix below is not a fully untouched test); **Adjust** if not, and one single change adds at least 5 points to the middle estimate (tested before rounding); **Launch** otherwise.
2. **Coaching slots (Coach view only):** the riskiest teams, ranked by the lower value, up to the coach's capacity (default 30%, adjustable). The slider changes who gets a slot, never a verdict.
3. Before 25.11 the cohort view labelled the slot holders "Coach first" and gave the rest Adjust or Launch, and the Adjust test used the gain at the upper value. The figures below for slots (failures reached) are unchanged; the verdict mix was recomputed.

Why rank by the lower value: inside a category the order is identical (AUC within category 0.859 both ways), but across categories it uses official levels instead of our biased sample levels.

| Coach capacity | Our sample: failures reached | Our sample: share of the group that fails | Official mix: failures reached | Official mix: share of the group that fails |
|---|---|---|---|---|
| 20% | 57% | 84% | 35% | 98% |
| **30%** | **75%** | **73%** | **51%** | **95%** |
| 40% | 87% | 63% | 66% | 92% |
| 50% | 93% | 54% | 79% | 88% |

- In the official mix 56% of campaigns fail (our sample: 29%). A coach with capacity for 30% can therefore reach at most 54% of the failures; the model reaches 51%.
- Simulated cohorts of 40 drawn from 2025, coach takes the 12 riskiest: on average 74% of the cohort's failures are among them (in 9 of 10 cohorts between about 55% and over 90%).
- Verdict mix (4,000 campaigns of 2025, gains on the middle estimate): Coach first 17% (12% funded in sample), Adjust 32% (66%), Launch 51% (95%).
- Adjust threshold sensitivity (share of non-Coach-first campaigns labelled Adjust): 3 points 50%, 5 points 38%, 8 points 29%, 10 points 24%.

## 5. What to change
One change at a time on: goal (−10% to −50%, never below the minimum budget), campaign length (15 / 21 / 30 / 45 days), launch day (next six days), moving off Christmas, video, pre-launch page, 14 or 30 more days of preparation, title of about 7 words, full blurb. Best option per lever, top 3, only if it adds at least 2 points to the middle estimate (since 25.11; before, gains were measured at the upper value).

On 4,000 campaigns of 2025 (minimum budget assumed at half the goal):
- No change of 2 points or more: 35%. Median best gain 3.7 points; 43% have a change of 5 points or more, 24% of 10 or more.
- Top fix: pre-launch page 18%, preparation 15%, length 11%, goal 10%, video 5%, launch day 3%, blurb 2%, title 1%.
- Median gain when offered (points of the middle estimate; a model difference, not a measured effect): pre-launch page 10.8, preparation 6.7, goal 4.6, video 4.2, blurb 3.8, length 3.7, launch day 3.5, title 3.2.
- These figures use a sample of 4,000 of the 26,533 test campaigns (SHAP figures use all 26,533). Script: `stage5_gain.py`, 25.11.2026.

Caveat: **pre-launch page and preparation time stand for groundwork** (an audience built before launch). Opening a page the day before will not add these points. Wording in the app: "campaigns that did this were funded more often".

## 6. Product types that do badly (note for coaches)
Rule: Product-type score ≤ 15 → note that this type of product has rarely been funded on Kickstarter and that changing the set-up will not fix that. On 2025: 3,447 campaigns (13%), funded 21% in sample against 78% for the rest. Mostly apps, web, restaurants, software, drinks.

## 7. Explanation tree (class: decision tree, depth 3)
Built on readable inputs only (no text score, no category codes). Path: track record → pre-launch page → goal above about $10,000–13,000, or number of earlier funded campaigns. The app shows the path and a band (lower / middle / higher), not a percentage.

## 8. Reading
1. Ranking-based triage is defensible; absolute chances are not, so they stay a range.
2. Most of the score is not under the founder's control. The app says so.
3. Advice is association. The strongest "levers" are proxies for preparation work.
4. In a realistic cohort a coach with 30% capacity reaches about half of the failures, close to the maximum possible, and almost none of the hours go to campaigns that would have been funded anyway.
