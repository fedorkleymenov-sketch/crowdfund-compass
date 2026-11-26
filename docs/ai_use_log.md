# AI-use log — Crowdfund Compass (Group 11)

Course rule: "Use whatever you want, but cite correctly."

| Date | Tool / model | Used for |
|---|---|---|
| 07–16.11.2026 | Claude (Anthropic), earlier chats | Topic brainstorm, proposal slides, data collection, first merge script, project brief |
| 16.11.2026 | Claude (Anthropic), model Fable 5.2 | Data audit and rebuild of the merged table (`merge_v2.py`); semantic layer and feature role table; feature module and notebook 02; models, evaluation and notebook 03; SHAP, area scores, advice module, verdict rule and notebook 04; Streamlit app |
| 16.11.2026 | Claude (Anthropic), model Fable 5.2 | Redesign of the app (presentation only, no model or number changed); PowerPoint deck with charts; chart check of the deck; first draft of the 15-minute voice-over script and of the pitch script (the team rewrites the texts) |
| 25.11.2026 | ChatGPT (OpenAI, GPT-6.2 Sol and Astra) | Outside review and grade of the project; three design proposals; first version of the Decision Desk layout and the new wording (app.py, ui.py), tested and corrected by Claude before going live |
| 25.11.2026 | Claude (Anthropic, model Opus 5.5) | Prompts for the ChatGPT review; testing and merging the Decision Desk version; deck, script and docs updated to the new wording |
| 25.11.2026 | ChatGPT (OpenAI, GPT-6.2 Astra) | Examiner-style review in a fresh chat (grade, criteria, correctness audit, hardest questions, action plan); first computation of the comparison with simple rules |
| 25.11.2026 | Claude (Anthropic, model Opus 5.5) | Checked the review against the code; fixed verdict vs coaching slots, gain scale and range labels; reproduced the simple-rules comparison; deck restructure, script draft 3, docs and report |
| 25.11.2026 | Claude (Anthropic, model Opus 5.5) | Small app fixes from the review; frozen re-test of the coaching rule on January–June 2026 |
| 25.11.2026 | Claude (Anthropic, model Opus 5.5) | Fixes from the second examiner review: honest 2026 disclosure and strongest comparator, Launch wording, founder history with cancelled campaigns, stricter upload checks, budget warning, round-goal flag per tested goal |
| 26.11.2026 | Claude (Anthropic, model Fable 5.2) | Independent examiner review for Nico (grade, 12 criteria, correctness audit, live test of the app); comparison with rules that look at the team (`stage8_simple_rules.py`); proposed fixes on branch `examiner-fixes`: round-goal flag in goal suggestions and Goal optimizer, gain wording on Launch cards, docs, slide 10, script and pitch wording |
All numbers were computed with code on the data. Decisions on scope, definitions, metrics and the verdict rule were taken by the team at each checkpoint.
