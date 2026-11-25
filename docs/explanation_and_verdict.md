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
- **Upper value:** calibrated chance in our sample. **Lower value:** after the shift to Kickstarter's official per-category rates. **Middle estimate:** halfway between the two on the odds scale (called "most likely" before 25.11).
- Why the range is wide: our data holds about 85% of all funded campaigns but about 42% of the failed ones, so the true level is uncertain.
- One public benchmark for the middle: tabletop games launched in 2024, official 80% funded; lower 66%, middle 78%, upper 86%.

## 4. Verdict rule (approved 16.11)
1. **Coach first** = the riskiest share of the cohort, ranked by the lower value of the range. The share is the coach's capacity, default 30%, adjustable.
2. **Adjust** = not in that group, and one single change is associated with at least 5 points more.
3. **Launch** = everything else.
4. Single check-up without a cohort: Coach first if the lower value is below 11.5%. That is where the riskiest 30% begin in a cohort with Kickstarter's official mix of outcomes.

Why rank by the lower value: inside a category the order is identical (AUC within category 0.859 both ways), but across categories it uses official levels instead of our biased sample levels.

| Coach capacity | Our sample: failures reached | Our sample: share of the group that fails | Official mix: failures reached | Official mix: share of the group that fails |
|---|---|---|---|---|
| 20% | 57% | 84% | 35% | 98% |
| **30%** | **75%** | **73%** | **51%** | **95%** |
| 40% | 87% | 63% | 66% | 92% |
| 50% | 93% | 54% | 79% | 88% |

- In the official mix 56% of campaigns fail (our sample: 29%). A coach with capacity for 30% can therefore reach at most 54% of the failures; the model reaches 51%.
- Simulated cohorts of 40 drawn from 2025, coach takes the 12 riskiest: on average 74% of the cohort's failures are among them (in 9 of 10 cohorts between about 55% and over 90%).
- Verdict mix on 2025 with the single check-up rule: Coach first 17% (12% funded in sample), Adjust 28% (63%), Launch 56% (95%).
- Adjust threshold sensitivity (share of non-coach campaigns labelled Adjust): 3 points 41%, 5 points 33%, 8 points 25%, 10 points 21%.

## 5. What to change
One change at a time on: goal (−10% to −50%, never below the minimum budget), campaign length (15 / 21 / 30 / 45 days), launch day (next six days), moving off Christmas, video, pre-launch page, 14 or 30 more days of preparation, title of about 7 words, full blurb. Best option per lever, top 3, only if at least 2 points.

On 4,000 campaigns of 2025 (minimum budget assumed at half the goal):
- No change of 2 points or more: 44%. Median best gain 2.9 points; 41% have a change of 5 points or more, 26% of 10 or more.
- Top fix: pre-launch page 17%, preparation 14%, length 9%, goal 8%, video 3%, launch day 2%, blurb 1%, title under 1%.
- Median gain when offered: pre-launch page 10.8, preparation 7.7, goal 5.0, video 4.8, length 4.2, blurb 3.9, launch day 3.8, title 3.1.

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
