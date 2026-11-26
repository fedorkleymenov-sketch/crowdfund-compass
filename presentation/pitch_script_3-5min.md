# Live pitch, 3–5 minutes — Crowdfund Compass (draft 3, 26.11.2026)

About 570 words: roughly 4.4 minutes at 130 words per minute, plus about 30 seconds for the live demo. Every number matches the app, the deck and the docs as of 26.11 (the value section now compares with a one-page scorecard: 29, 27, 25). This is a draft: say it in your own words.

**What to have open:** the live app on the Coach view (https://azjftouvzzw5dbnqbqyrwl.streamlit.app/?page=Coach%20view), with the example cohort and the slider at 30%.

---

**[Problem, about 40 seconds]**
On Kickstarter, a campaign that misses its goal gets nothing. Not half: nothing. And the founder usually sets the goal, the launch date and the pitch by gut feeling.

Now imagine you coach startups at a university. Twenty teams want to launch a campaign this term, and you have time for six of them. Which six?

That is the decision Crowdfund Compass supports. Before launch, every plan gets a verdict: Launch, Adjust or Coach first. And the coach gets the riskiest teams ranked, so the coaching hours go where they are needed most.

**[Data and the key finding, about 60 seconds]**
We built it on 489,000 Kickstarter campaigns from 24 public snapshots, ten years of data. From these, we use 32 things a founder knows before launch: the goal and the timing, the title and short text, the founder's track record, the video and pre-launch page, and the type of product.

But the most important thing we found was a problem. Kickstarter hides most campaigns that failed. Our data holds about 85 percent of all funded campaigns, but only 42 percent of the failed ones. For tabletop games in 2024, our data says 94 percent were funded; Kickstarter says 80. If we had ignored this, our app would tell almost every founder that things look great.

So we did three things. We judge the model inside each category. We show every chance as a range, not one exact number. And we give coaching slots by rank, not by percentage.

**[Model, about 30 seconds]**
The model is XGBoost, a method from this course. We trained it on campaigns from 2023 and 2024 and tested it on 2025, which it had never seen. Inside a category, it ranks a funded campaign above a failed one 86 times out of 100. A plain logistic regression does almost as well, so the inputs matter more than the algorithm.

**[Live demo, about 60 seconds]**
Here is the coach's view. Six planned campaigns, and time for two. The app ranks them from riskiest to safest, and a line marks the coach's capacity. The two slots go to BudgetBuddy, a money app, and Voices of the Rhine, a documentary.

For BudgetBuddy, the conversation is whether Kickstarter is the right route at all: apps have rarely been funded there. For Voices of the Rhine, the app points to preparation: campaigns with a pre-launch page were funded more often, so the coach asks what audience the team has built.

If I move the slider, more teams get a slot, but no team's verdict changes.

**[Value, about 40 seconds]**
Does the ranking beat what a coach could do without us? We tested it on 2025 campaigns, re-weighted to Kickstarter's real mix. With 30 slots per 100 teams, our ranking reaches about 29 teams that will fail. Picking the subcategories with the lowest funding rates reaches 25. A one-page scorecard that also asks three questions about the team reaches 27. So our ranking finds about two more struggling teams than a coach's best rule of thumb, with the same hours. And we got the same result on the first half of 2026.

**[Limits and close, about 30 seconds]**
We are careful about what this means. We measured which teams get flagged, not how much coaching helps them; that would need a real study with coaches. "Launch" is not a promise, so the app always shows the range. And less than half of the model's explanation comes from things a founder can change.

Crowdfund Compass does not tell founders they will succeed. It tells a coach where to spend the next hour. Thank you.

---

**If you run short of time,** cut the model section to one sentence: "XGBoost, a class method, tested on campaigns it had never seen: 86 out of 100 pairs ranked correctly."

**Likely first question:** "How much does coaching actually help?" Answer: "We don't know yet, and we say so. Our test shows who gets flagged. The next step would be a study with Startup@HSG: coach half of the flagged teams and compare their outcomes."
