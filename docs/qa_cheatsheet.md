# Q&A cheat sheet — Crowdfund Compass (Group 11)

Fifteen questions a professor could ask, each with a short answer in plain words. Numbers are from `results.md` and `explanation_and_verdict.md`.

**1. What decision does this support, and for whom?**
A startup coach with limited hours must decide which planned Kickstarter campaigns to see first. Each campaign gets one verdict: Launch, Adjust or Coach first. A founder can check a single plan.

**2. Why this data and not the Kaggle Kickstarter file?**
The Kaggle file has about six fields known before launch. The Web Robots scrapes add title and blurb, creator history, video and pre-launch page. With six fields our model reaches an AUC of 0.75 inside a category, with 32 it reaches 0.86.

**3. How did you avoid leakage?**
Three rules. Only inputs a founder knows before launch: nothing about pledges, backers or "Projects We Love". History inputs use only campaigns that ended before the launch; we rechecked 695 campaigns by hand-written code with zero mismatches. And we found one hidden leak ourselves: whether a video is recorded depends on when Kickstarter last listed the project, which depends on the outcome, so those fields are used only where they are known for every campaign.

**4. Why a time split instead of a random split?**
The tool is used on future campaigns, so we test on the future. We train on 2023–2024 and test once on 2025 and on January–June 2026. A walk-forward check from 2019 gives the same picture every year.

**5. What does AUC mean, and why "within category"?**
Take one funded and one failed campaign at random: AUC is how often the model gives the funded one the higher score. 0.5 is guessing, 1 is perfect. We compute it inside each of 174 categories, because our data covers failed campaigns differently in each category. Across categories a model can look good just by learning which categories we cover well.

**6. Your data is biased. How bad is it, and what did you do?**
Kickstarter's listings hide most failed campaigns. We hold about 85% of all funded campaigns but about 42% of the failed ones, so 71% of our 2025 campaigns are funded against an official all-time 43%. We do three things: we judge the model inside categories, we decide "Coach first" by rank and not by a percentage, and we show the chance as a range whose lower value is adjusted to Kickstarter's official rates.

**7. Why XGBoost?**
It is a class method and handles missing values and mixed inputs well. Honestly, the choice matters little: logistic regression scores 0.857 and the random forest 0.858 against 0.859. The inputs carry the result, not the algorithm.

**8. What is "beyond class", and why did you use it?**
Six things, each labelled in the app: the text score fed into the main model, the rule that a higher goal can only lower the chance, calibration, the adjustment to official rates, SHAP for the explanations, and the one-change-at-a-time advice. Each exists because the decision needs it: a coach needs reasons and a believable percentage, not only a score.

**9. Can a founder really raise the chance by following the advice?**
We do not claim that. The app says "campaigns that did this were funded more often". The two biggest patterns, a pre-launch page and more preparation time, stand for groundwork such as building an audience. Opening a page the day before launch will not help.

**10. How accurate is the percentage?**
The ranking is solid, the level is rough. That is why we show a range, about 15 points wide on average, and a "most likely" value in the middle. On the one public figure we could check, tabletop games in 2024, Kickstarter reports 80% funded and our middle value is 78%.

**11. What is the business value?**
In a cohort with Kickstarter's real mix, 56% of campaigns fail. A coach who can see 30% of the cohort and picks by our ranking reaches 51% of all failures, where the maximum possible is 54%, and 95% of the campaigns the coach sees would indeed have failed. Almost no coaching hours go to campaigns that did not need them.

**12. What can a founder actually change?**
Less than half. Goal, timing, presentation and pitch explain 43% of the model's result. What is being made and the creator's track record explain 57%. The app says so, and tells the coach when a type of product, such as apps or software, has rarely been funded on Kickstarter at all.

**13. Does more data help?**
More features help a lot, more history does not. 44,000 campaigns from 2023–2024 do as well as 385,000 from all years (0.850 against 0.852). Video and pre-launch page add about 0.009.

**14. What are the main limits?**
The remaining bias cannot be measured: the failed campaigns we see are the visible ones. Official rates are all-time averages per main category. Patterns are not causes. Funding is a market test, not proof that a company survives. And the data ends in November 2026.

**15. What would you do next?**
Get outcomes for the campaigns Kickstarter hides, for example by following live campaigns daily until they end. Test the advice with real cohorts at Startup@HSG. Add other platforms, since the product-type note already tells some founders that Kickstarter is the wrong route.

## Short definitions to have ready
- **Precision / recall at 50%:** when the model says "will fail" it is right 81% of the time, and it finds 63% of the failures.
- **Calibration:** a small correction so that "70%" means about 70 in 100; after it, predictions are within 5 points of what happened in 2025.
- **SHAP:** splits a score into one piece per input; the pieces add up exactly to the score.
- **Grid search with time-ordered cross-validation:** try a fixed set of settings, always training on earlier campaigns and checking on later ones.
