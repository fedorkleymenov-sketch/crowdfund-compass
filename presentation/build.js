const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.APPLY_THEME || "/root/.claude/skills/synced/b1664417-94ef-45c8-81d6-57ef8c5fdbe5_11d7e28c-5c53-44f8-9979-b7add7647ad5/pptx/scripts/apply_theme.js");
const THEME = { name: "Crowdfund Compass", headFontFace: "Arial", bodyFontFace: "Arial",
  colors: { dk1: "0B1F33", lt1: "FFFFFF", dk2: "5B6B7C", lt2: "F7F8FA", accent1: "0F6E56", accent2: "3FCFA4", accent3: "15803D", accent4: "B45309", accent5: "B91C1C", accent6: "CBD3DC", hlink: "0F6E56", folHlink: "5B6B7C" } };
const H = THEME.colors;
const VO = require("./voiceover.json"); let slideNo = 0;
(async () => {
const pres = new pptxgen(); pres.layout = "LAYOUT_16x9"; pres.theme = { headFontFace: "Arial", bodyFontFace: "Arial" };
pres.title = "Crowdfund Compass"; pres.author = "Group 11: Kleymenov, Arcauz, Braun";
const C = pres.SchemeColor;
pres.defineSlideMaster({ title: "TITLE_DARK", background: { color: H.dk1 }, objects: [
  { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.7, w: 8.6, h: 1.6, fontSize: 30, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
  { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.5, w: 7.6, h: 0.6, fontSize: 16, color: C.accent6, valign: "top", align: "left", margin: 0, bullet: false }, text: "" } } ] });
pres.defineSlideMaster({ title: "CONTENT", background: { color: H.lt2 }, objects: [
  { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.32, w: 9.0, h: 0.95, fontSize: 24, bold: true, color: C.text1, valign: "top", align: "left", margin: 0 }, text: "" } },
  { text: { text: "Crowdfund Compass · Group 11", options: { x: 0.5, y: 5.2, w: 5, h: 0.25, fontSize: 9, color: C.text2, margin: 0 } } } ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.25, fontSize: 9, color: H.dk2, align: "right" } });
let sec = "";
const S = (title, notes, master = "CONTENT") => { const s = pres.addSlide({ masterName: master, sectionTitle: sec }); s.addText(title, { placeholder: "title" }); slideNo += 1; const v = VO.find(o => o.slide === slideNo); s.addNotes("Speaker: " + v.speaker + " (about " + v.minutes + " min)\n\n" + v.text); return s; };
const card = (s, x, y, w, h, fill = H.lt1) => s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: "E4E8EE", width: 0.75 }, shadow: { type: "outer", color: "0B1F33", opacity: 0.06, blur: 6, offset: 2, angle: 90 } });
const T = (s, text, x, y, w, h, o = {}) => s.addText(text, Object.assign({ x, y, w, h, isTextBox: true, margin: 0, fontSize: 14, color: C.text1, valign: "top" }, o));
const stat = (s, x, y, w, num, label, color = C.accent1, h = 1.45, fs = 30) => { card(s, x, y, w, h); T(s, num, x + 0.2, y + 0.15, w - 0.4, 0.6, { fontSize: fs, bold: true, color, valign: "middle" }); T(s, label, x + 0.2, y + 0.78, w - 0.4, h - 0.85, { fontSize: 12, color: C.text2 }); };
const chartOpts = (extra) => Object.assign({ catAxisLabelColor: H.dk2, valAxisLabelColor: H.dk2, catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  dataLabelColor: H.dk1, dataLabelFontSize: 11, valGridLine: { color: "E4E8EE", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false, showValue: true }, extra);

// ---------------- Section 1: problem and decision (Fedor)
sec = "Problem and decision (Fedor)"; pres.addSection({ title: sec });
let s = S("Crowdfund Compass: which campaigns need a coach before they launch?", "Speaker: Fedor.\nOn Kickstarter a campaign that misses its goal gets nothing. We built a check that runs before launch. The app is live at the link on this slide.", "TITLE_DARK");
s.addImage({ path: "/home/claude/crowdfund-compass/app/assets/favicon.png", x: 0.6, y: 0.75, w: 0.7, h: 0.7 });
T(s, "Know before you launch.", 1.45, 0.9, 5, 0.4, { fontSize: 16, color: C.accent2, bold: true });
s.addText("A pre-launch readiness check for Kickstarter campaigns", { placeholder: "body" });
T(s, [{ text: "Group 11 · Fedor Kleymenov, Alexandre Arcauz, Nico Braun", options: { breakLine: true } }, { text: "Business Analytics & Data Science Applications · Prof. Ivo Blohm · HSG", options: { breakLine: true } }, { text: "azjftouvzzw5dbnqbqyrwl.streamlit.app", options: { color: C.accent2, hyperlink: { url: "https://azjftouvzzw5dbnqbqyrwl.streamlit.app/" } } }], 0.6, 4.35, 8.5, 0.9, { fontSize: 12, color: C.accent6 });

s = S("A coach has hours for a third of the cohort, and no way to see who is at risk", "Speaker: Fedor.\nState the managerial problem and who has it: a startup coach, for example at Startup@HSG. Say once: funding is a market test, not proof that the company survives.");
stat(s, 0.5, 1.45, 2.9, "All or nothing", "A campaign that misses its goal receives no money at all.", C.accent5, 1.45, 22);
stat(s, 3.55, 1.45, 2.9, "43%", "of all campaigns ever launched on Kickstarter reached their goal (official figure).", C.text1);
stat(s, 6.6, 1.45, 2.9, "Gut feeling", "Founders set goal, timing and pitch without data.", C.accent4, 1.45, 22);
card(s, 0.5, 3.15, 9.0, 1.75); T(s, "The managerial problem", 0.75, 3.3, 8.5, 0.35, { bold: true, fontSize: 15 });
T(s, [{ text: "Startup coaches have limited hours and many teams that want to launch.", options: { bullet: true, breakLine: true } }, { text: "They cannot see in advance which plans are at risk, so hours go to the wrong teams.", options: { bullet: true, breakLine: true } }, { text: "A failed campaign costs the team months of work and its first public impression.", options: { bullet: true } }], 0.75, 3.7, 8.5, 1.1, { fontSize: 14, paraSpaceAfter: 4 });

s = S("One decision per campaign: Launch, Adjust or Coach first", "Speaker: Fedor.\nThe decision-driven question: which campaigns are ready, and for the others, which change is linked to better odds? Primary user: the coach who triages a cohort. Secondary user: the founder who checks one plan.");
[["Launch", "Not among the riskiest, and no single change adds 5 points. Not a promise.", H.accent3, "E8F5EC"], ["Adjust", "One named change adds at least 5 points to the middle estimate.", H.accent4, "FDF1DC"], ["Coach first", "Among the riskiest plans (lower value below 11.5%): talk to a coach first.", H.accent5, "FCE9E7"]].forEach(([v, t, col, soft], i) => {
  const x = 0.5 + i * 3.05; card(s, x, 1.45, 2.9, 1.9);
  s.addShape(pres.ShapeType.roundRect, { x: x + 0.2, y: 1.65, w: 1.6, h: 0.42, rectRadius: 0.2, fill: { color: soft }, line: { color: soft } });
  T(s, v, x + 0.2, 1.65, 1.6, 0.42, { bold: true, color: col, fontSize: 14, align: "center", valign: "middle" }); T(s, t, x + 0.2, 2.25, 2.5, 1.0, { fontSize: 13, color: C.text2 }); });
card(s, 0.5, 3.6, 9.0, 1.3); T(s, "The question we answer", 0.75, 3.75, 8.5, 0.3, { bold: true, fontSize: 13, color: C.accent1 });
T(s, "Which campaigns should a coach see first, and for each campaign, which change is linked to the biggest rise in its odds of being funded?", 0.75, 4.08, 8.5, 0.75, { fontSize: 15, italic: true });

s = S("The coach's view: six teams, time for two", "");
s.addImage({ path: "s_coach_big.png", x: 0.8, y: 1.25, w: 8.4, h: 3.65, altText: "Coach view: six example campaigns ranked from riskiest to safest, with a line where the coach's capacity ends" });
T(s, [{ text: "Above the line: a coaching slot. The slider never changes a verdict.  Live: " }, { text: "azjftouvzzw5dbnqbqyrwl.streamlit.app", options: { color: C.accent1, bold: true, hyperlink: { url: "https://azjftouvzzw5dbnqbqyrwl.streamlit.app/?page=Coach%20view" } } }], 0.8, 4.92, 8.4, 0.22, { fontSize: 10, color: C.text2 });

// ---------------- Section 2: data and model (Alex)
sec = "Data and model (Alex)"; pres.addSection({ title: sec });
s = S("489,000 campaigns from 24 snapshots, instead of a 6-field public file", "Speaker: Alex.\nThe TA told us on 10 November: find more data, use many more inputs. This is our answer. Source: public Kickstarter listings collected by Web Robots, 2016 to 2026.");
stat(s, 0.5, 1.45, 2.15, "489,000", "campaigns collected (24 snapshots, 2016–2026)", C.text1); stat(s, 2.78, 1.45, 2.15, "430,000", "with a final outcome: funded or failed", C.text1);
stat(s, 5.06, 1.45, 2.15, "~44,000", "launched 2023–2024, used to train the final model"); stat(s, 7.34, 1.45, 2.16, "39,500", "launched 2025 and Jan–Jun 2026, used to test it");
card(s, 0.5, 3.15, 4.4, 1.75); T(s, "Typical public file: 6 fields before launch", 0.7, 3.3, 4.0, 0.3, { bold: true, fontSize: 13 }); T(s, "Category, country, goal, length, launch month, title length", 0.7, 3.65, 4.0, 1.0, { fontSize: 13, color: C.text2 });
card(s, 5.1, 3.15, 4.4, 1.75); T(s, "Our data adds", 5.3, 3.3, 4.0, 0.3, { bold: true, fontSize: 13, color: C.accent1 }); T(s, "Title and blurb text, the creator's earlier campaigns, video, pre-launch page, preparation time, 174 categories", 5.3, 3.65, 4.0, 1.0, { fontSize: 13, color: C.text2 });

s = S("Our data shows 85% of funded campaigns but only 42% of failed ones", "Speaker: Alex.\nKickstarter's listings hide most failed campaigns. We found this in the audit, measured it against Kickstarter's official counts, and it shaped every later choice. Example: tabletop games 2024, 94% funded in our data against 80% officially.");
s.addChart(pres.charts.BAR, [{ name: "Share of all campaigns we hold", labels: ["Funded campaigns", "Failed campaigns"], values: [85, 42] }], chartOpts({ x: 0.5, y: 1.4, w: 5.0, h: 3.5, barDir: "col", chartColors: [H.accent6, H.accent1], barGapWidthPct: 80, valAxisMaxVal: 100, valAxisMinVal: 0, dataLabelFormatCode: '0"%"', valAxisLabelFormatCode: '0"%"', showTitle: true, title: "Share of all Kickstarter campaigns that are in our data (campaigns ended before 1 Jan 2026; totals: Kickstarter stats page)", titleFontSize: 10, titleColor: H.dk2, titleFontFace: "+mn-lt" }));
stat(s, 5.8, 1.45, 3.7, "94% vs 80%", "Tabletop games 2024: funded in our data against Kickstarter's own figure", C.accent5, 1.5);
card(s, 5.8, 3.1, 3.7, 1.8); T(s, "What we did about it", 6.0, 3.22, 3.3, 0.3, { bold: true, fontSize: 13 });
T(s, [{ text: "Judge the model inside each category", options: { bullet: true, breakLine: true } }, { text: "Show chances as a range", options: { bullet: true, breakLine: true } }, { text: "Give coaching slots by rank", options: { bullet: true } }], 6.0, 3.58, 3.3, 1.2, { fontSize: 13, paraSpaceAfter: 3 });

s = S("We caught a leak before it reached the model", "Speaker: Alex.\nWhether a video is recorded depends on when Kickstarter last listed the project, and that depends on the outcome. A model can learn that instead of the campaign. With the leak the score looks better on old data and gets worse on new data. So video and pre-launch page are only used where they are known for every campaign.");
card(s, 0.5, 1.45, 4.4, 2.2); T(s, "On 2022 launches (field often unknown)", 0.7, 1.58, 4.0, 0.3, { bold: true, fontSize: 13 });
T(s, "0.901 → 0.920", 0.7, 1.95, 4.0, 0.7, { fontSize: 32, bold: true, color: C.accent5 }); T(s, "AUC without and with the leaking fields: it looks like an improvement", 0.7, 2.75, 4.0, 0.7, { fontSize: 12, color: C.text2 });
card(s, 5.1, 1.45, 4.4, 2.2); T(s, "On 2024 launches (field always known)", 5.3, 1.58, 4.0, 0.3, { bold: true, fontSize: 13 });
T(s, "0.841 → 0.828", 5.3, 1.95, 4.0, 0.7, { fontSize: 32, bold: true, color: C.text1 }); T(s, "The same two models on new data: the \"gain\" was the scraper, and it hurts", 5.3, 2.75, 4.0, 0.7, { fontSize: 12, color: C.text2 });
T(s, [{ text: "No results of the campaign as inputs: pledges, backers, \"Projects We Love\"", options: { bullet: true, breakLine: true } }, { text: "History inputs rechecked on 695 campaigns with separate code: 0 mismatches", options: { bullet: true, breakLine: true } }, { text: "Video and pre-launch page only in a model trained on launches from 2023 on", options: { bullet: true } }], 0.5, 3.9, 9.0, 1.1, { fontSize: 13, paraSpaceAfter: 3 });

s = S("Tested on the future: 0.86 inside a category. More inputs helped; fancier models did not", "");
s.addChart(pres.charts.BAR, [{ name: "AUC within category, 2025", labels: ["Baselines", "XGBoost, 6 usual inputs", "Logistic regression, 32 inputs", "XGBoost, 32 inputs (final)"].reverse(), values: [0.5, 0.753, 0.857, 0.859].reverse() }],
  chartOpts({ x: 0.5, y: 1.35, w: 5.7, h: 3.65, barDir: "bar", chartColors: [H.accent1, H.accent6, H.accent6, H.accent6], barGapWidthPct: 45, valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.25, dataLabelFormatCode: "0.000", valAxisLabelFormatCode: "0.00", showTitle: true, title: "AUC within category, campaigns launched in 2025 (n = 26,508 in the 163 categories with both outcomes); 0.5 = guessing, 1 = perfect", titleFontSize: 10, titleColor: H.dk2, titleFontFace: "+mn-lt" }));
stat(s, 6.4, 1.3, 3.1, "0.86", "on 2025 launches (Jan–Jun 2026: 0.87)", C.accent1, 1.1, 26);
stat(s, 6.4, 2.5, 3.1, "85% vs 71%", "accuracy against always saying \"funded\"", C.text1, 1.2, 22);
stat(s, 6.4, 3.8, 3.1, "0.852 vs 0.850", "all years vs 2023–24 only: more history did not help", C.text1, 1.25, 18);

s = S("The ranking is solid, the percentage is rough: so we show a range", "Speaker: Alex.\nAfter calibration, predictions are within 5 points of what happened in 2025 in our data. But our data is too optimistic, so the app shows a range: the upper value from our data, the lower value adjusted to Kickstarter's official rates, and the middle as most likely. We could check the middle on one public figure: tabletop games 2024, official 80%, ours 78%.");
const CALA = [4.5, 14.7, 26.3, 37.7, 46.7, 57.0, 69.8, 77.3, 88.3, 97.8], CALB = [2.6, 10.4, 18.9, 27.3, 38.1, 45.6, 56.1, 70.6, 80.8, 96.5];
s.addChart(pres.charts.LINE, [{ name: "After calibration", labels: ["5", "15", "25", "35", "45", "55", "65", "75", "85", "96"], values: CALA }, { name: "Before calibration", labels: ["5", "15", "25", "35", "45", "55", "65", "75", "85", "96"], values: CALB }, { name: "Perfect", labels: ["5", "15", "25", "35", "45", "55", "65", "75", "85", "96"], values: [5, 15, 25, 35, 45, 55, 65, 75, 85, 96] }],
  chartOpts({ x: 0.5, y: 1.35, w: 5.2, h: 3.65, chartColors: [H.accent1, H.accent6, "9AA6B2"], lineSize: 2, lineDataSymbolSize: 6, showValue: false, showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: H.dk2, legendFontFace: "+mn-lt", showTitle: true, title: "Final model, campaigns launched in 2025 (n = 26,533), grouped by predicted chance, in our data", titleFontSize: 10, titleColor: H.dk2, titleFontFace: "+mn-lt", valAxisMaxVal: 100, valAxisMinVal: 0, showCatAxisTitle: true, catAxisTitle: "Predicted chance (%)", catAxisTitleColor: H.dk2, catAxisTitleFontSize: 10, showValAxisTitle: true, valAxisTitle: "Actually funded (%)", valAxisTitleColor: H.dk2, valAxisTitleFontSize: 10 }));
card(s, 6.0, 1.45, 3.5, 1.65); T(s, "The range", 6.2, 1.57, 3.1, 0.3, { bold: true, fontSize: 13 });
T(s, [{ text: "One estimate from our data", options: { bullet: true, breakLine: true } }, { text: "One adjusted to the official rate of the category (almost always the lower one)", options: { bullet: true, breakLine: true } }, { text: "Middle estimate: halfway between", options: { bullet: true } }], 6.2, 1.92, 3.1, 1.1, { fontSize: 12, paraSpaceAfter: 2 });
stat(s, 6.0, 3.3, 3.5, "78% vs 80%", "our middle estimate against Kickstarter's figure for tabletop games 2024 (one benchmark)", C.accent1, 1.6);

// ---------------- Section 3: impact (Fedor)
sec = "Impact (Fedor)"; pres.addSection({ title: sec });
s = S("With 30 slots per 100 teams, our ranking finds 29 failing teams; a one-page scorecard finds 27", "");
s.addChart(pres.charts.BAR, [{ name: "Share of all failures reached", labels: ["Random", "Lowest official category rate", "Highest goal for the category", "Lowest sub-category rate", "Scorecard with 3 questions", "Our model", "Maximum possible"], values: [30, 37.7, 37.3, 44.5, 47.6, 51.1, 53.6] }], chartOpts({ x: 0.5, y: 1.35, w: 5.3, h: 3.65, barDir: "col", chartColors: [H.accent6, H.accent6, H.accent6, H.accent6, H.accent6, H.accent1, "9AA6B2"], barGapWidthPct: 50, valAxisMaxVal: 60, valAxisMinVal: 0, dataLabelFormatCode: '0"%"', valAxisLabelFormatCode: '0"%"', catAxisLabelFontSize: 9, catAxisLabelRotate: 0.01, showTitle: true, title: "Share of all failures reached with coaching slots for 30% of teams (2025 launches, re-weighted to Kickstarter's official mix: 56% fail)", titleFontSize: 10, titleColor: H.dk2, titleFontFace: "+mn-lt" }));
stat(s, 6.05, 1.35, 3.45, "29 vs 27", "failing teams found per 100 campaigns with 30 coaching slots: our ranking vs a one-page scorecard (51% vs 48% of all failures). Best category rule: 25.", C.accent1, 1.75, 26);
stat(s, 6.05, 3.25, 3.45, "95%", "of the teams given a slot failed. Re-test on Jan–Jun 2026, settings fixed: 51% vs 48% vs 45%. It shows who gets flagged, not how much coaching helps.", C.text1, 1.75, 26);

// ---------------- Section 4: app and limits (Nico)
sec = "App and limits (Nico)"; pres.addSection({ title: sec });
s = S("Less than half of the model's explanation comes from things a founder can change", "Speaker: Nico.\nThe app says this openly. Goal, timing, presentation and pitch explain 43% of the model's result; what is being made and the creator's track record explain 57%. The biggest levers, a pre-launch page and more preparation, stand for groundwork, not for a button to press. For 44% of campaigns no single change is worth 2 points.");
s.addChart(pres.charts.BAR, [{ name: "Share of the model's explanation", labels: ["Product type", "Founder", "Ambition", "Presentation", "Timing", "Pitch"].reverse(), values: [34, 23, 19, 12, 9, 4].reverse() }], chartOpts({ x: 0.5, y: 1.35, w: 4.9, h: 3.65, barDir: "bar", chartColors: [H.accent1, H.accent1, H.accent1, H.accent1, H.accent6, H.accent6], barGapWidthPct: 45, valAxisMinVal: 0, valAxisMaxVal: 40, dataLabelFormatCode: '0"%"', valAxisLabelFormatCode: '0"%"', showTitle: true, title: "Share of the model's explanation (SHAP), 2025 launches (n = 26,533). Green = a founder can change it. Rounded shares add to 101%", titleFontSize: 10, titleColor: H.dk2, titleFontFace: "+mn-lt" }));
stat(s, 5.7, 1.45, 1.8, "43%", "of the explanation: things a founder can change", C.accent1, 1.4); stat(s, 7.7, 1.45, 1.8, "57%", "product type and track record", C.text1, 1.4);
card(s, 5.7, 3.05, 3.8, 1.9); T(s, "Biggest gains (model, 4,000 campaigns)", 5.9, 3.17, 3.4, 0.3, { bold: true, fontSize: 12 });
T(s, [{ text: "Pre-launch page: about +11 points", options: { bullet: true, breakLine: true } }, { text: "More preparation time: about +7", options: { bullet: true, breakLine: true } }, { text: "Lower goal or add a video: about +4 to +5", options: { bullet: true, breakLine: true } }, { text: "35% of campaigns: no single change worth 2 points", options: { bullet: true } }], 5.9, 3.52, 3.4, 1.35, { fontSize: 12, paraSpaceAfter: 2 });

s = S("The founder's view: one plan, one verdict, one next step", "");
s.addImage({ path: "s_check.png", x: 0.5, y: 1.3, w: 4.05, h: 3.74, altText: "Check-up page: the example board game, verdict Adjust, range 23 to 60 percent, best next step a pre-launch page" });
card(s, 4.85, 1.3, 4.65, 3.2); T(s, "The example: a board game, first campaign, $15,000", 5.05, 1.42, 4.3, 0.3, { bold: true, fontSize: 12, color: C.accent1 });
T(s, [{ text: "Verdict: Adjust", options: { bullet: true, breakLine: true } }, { text: "Chance: 23% to 60%, middle estimate 40%; each end says where it comes from", options: { bullet: true, breakLine: true } }, { text: "Best next step: a pre-launch page, middle estimate 40% → 63%", options: { bullet: true, breakLine: true } }, { text: "Four bars: where the plan is strong or weak", options: { bullet: true, breakLine: true } }, { text: "More pages: goal optimizer, similar campaigns, official benchmarks, how it works", options: { bullet: true } }], 5.05, 1.8, 4.3, 2.6, { fontSize: 12, paraSpaceAfter: 4 });
T(s, [{ text: "Live: " }, { text: "azjftouvzzw5dbnqbqyrwl.streamlit.app", options: { color: C.accent1, bold: true, hyperlink: { url: "https://azjftouvzzw5dbnqbqyrwl.streamlit.app/?page=Check-up" } } }], 4.85, 4.7, 4.65, 0.3, { fontSize: 11 });

s = S("Limits and next steps", "Speaker: Nico.\nWe know where this is weak and what would fix it. The remaining bias cannot be measured, because the failed campaigns we see are the visible ones. Next: follow live campaigns daily so that hidden failures get an outcome, test the advice with a real cohort, and add other platforms.");
card(s, 0.5, 1.45, 4.4, 2.5); T(s, "Limits", 0.7, 1.57, 4.0, 0.3, { bold: true, fontSize: 14, color: C.accent5 });
T(s, [{ text: "The remaining bias cannot be measured", options: { bullet: true, breakLine: true } }, { text: "Official rates are all-time averages", options: { bullet: true, breakLine: true } }, { text: "Patterns in past campaigns, not causes", options: { bullet: true, breakLine: true } }, { text: "We measured who gets flagged, not how much coaching helps", options: { bullet: true, breakLine: true } }, { text: "Funding is a market test, not proof a company survives", options: { bullet: true, breakLine: true } }, { text: "Data up to November 2026", options: { bullet: true } }], 0.7, 1.95, 4.0, 1.9, { fontSize: 13, paraSpaceAfter: 3 });
card(s, 5.1, 1.45, 4.4, 2.5); T(s, "Next steps", 5.3, 1.57, 4.0, 0.3, { bold: true, fontSize: 14, color: C.accent1 });
T(s, [{ text: "Follow live campaigns daily to see the hidden failures", options: { bullet: true, breakLine: true } }, { text: "Test the advice with a real cohort at Startup@HSG", options: { bullet: true, breakLine: true } }, { text: "Add other platforms: some products do not fit Kickstarter", options: { bullet: true } }], 5.3, 1.95, 4.0, 1.9, { fontSize: 13, paraSpaceAfter: 3 });
card(s, 0.5, 4.1, 9.0, 0.9); T(s, [{ text: "From class: ", options: { bold: true } }, { text: "XGBoost, logistic regression, trees, random forest, grid search, text mining (TF-IDF), course metrics.  " }, { text: "Beyond class: ", options: { bold: true } }, { text: "goal rule, calibration, official-rate range, SHAP, one-change advice, nearest neighbours. AI use: built with Claude (Anthropic), reviewed with ChatGPT (OpenAI); cited in the repository." }], 0.7, 4.2, 8.6, 0.72, { fontSize: 11, color: C.text2 });

// ---------------- Backup
sec = "Backup"; pres.addSection({ title: sec });
s = S("Backup: 32 inputs a founder knows before launch, in six areas", "Speaker: Alex.\nWe only use what is known before launch. We also threw inputs away when they measured the scraper and not the campaign: crowding, city size, category averages and title capitalisation.");
[["Ambition · 5", "Goal, goal against the category's usual goal, campaign length"], ["Timing · 4", "Preparation time, launch month and weekday, running over Christmas"], ["Pitch · 12", "Length and form of title and blurb, readability, tone"],
 ["Founder · 5", "Earlier campaigns and how many were funded"], ["Presentation · 2", "Campaign video, pre-launch page"], ["Product type · 4", "Category, country, and a text score for what is being made"]].forEach(([h, t], i) => {
  const x = 0.5 + (i % 3) * 3.05, y = 1.45 + Math.floor(i / 3) * 1.4; card(s, x, y, 2.9, 1.25); T(s, h, x + 0.2, y + 0.14, 2.5, 0.3, { bold: true, fontSize: 14, color: C.accent1 }); T(s, t, x + 0.2, y + 0.5, 2.5, 0.7, { fontSize: 12, color: C.text2 }); });
T(s, "Built and dropped: crowding (3), city size, category averages (3), title capitalisation. They had no signal inside a category or measured which categories our data covers well.", 0.5, 4.35, 9.0, 0.6, { fontSize: 12, color: C.text2, italic: true });

s = S("Backup: all models compared", "Speaker: Alex.\nAUC in one sentence: take one funded and one failed campaign from the same category; how often does the model give the funded one the higher score? We train on 2023–2024 and test once on 2025. Tuning: grid search with time-ordered cross-validation. Accuracy 85% against 71% for always saying funded.");
s.addChart(pres.charts.BAR, [{ name: "AUC within category, 2025", labels: ["Baselines", "XGBoost, 6 inputs", "Decision tree", "Logistic regression", "Random forest", "XGBoost (final)", "LightGBM + Optuna"].reverse(), values: [0.5, 0.753, 0.823, 0.857, 0.858, 0.859, 0.866].reverse() }],
  chartOpts({ x: 0.5, y: 1.35, w: 5.9, h: 3.65, barDir: "bar", chartColors: [H.accent6, H.accent1, H.accent6, H.accent6, H.accent6, H.accent6, H.accent6], barGapWidthPct: 45, valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.25, dataLabelFormatCode: "0.000", valAxisLabelFormatCode: "0.00", showTitle: true, title: "AUC within category, campaigns launched in 2025 (n = 26,508 in the 163 categories with both outcomes); 0.5 = guessing, 1 = perfect", titleFontSize: 10, titleColor: H.dk2, titleFontFace: "+mn-lt" }));
stat(s, 6.7, 1.45, 2.8, "0.86", "AUC within category on 2025 launches (Jan–Jun 2026: 0.87). 0.5 = guessing, 1 = perfect.", C.accent1, 1.65);
stat(s, 6.7, 3.25, 2.8, "85% vs 71%", "accuracy against always saying \"funded\"", C.text1, 1.65);


await pres.writeFile({ fileName: "Crowdfund_Compass_Group11.pptx" });
// Slide 10 has seven bars: keep its category labels horizontal (wrapped). pptxgenjs cannot write rot="0", so the
// chart is written with a tiny rotation and fixed here.
const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] })), fs = require("fs"); const zip = await JSZip.loadAsync(fs.readFileSync("Crowdfund_Compass_Group11.pptx"));
for (const f of Object.keys(zip.files).filter(f => /^ppt\/charts\/chart\d+\.xml$/.test(f))) {
  const x = await zip.file(f).async("string"); if (x.includes('<a:bodyPr rot="600"/>')) zip.file(f, x.split('<a:bodyPr rot="600"/>').join('<a:bodyPr rot="0" vert="horz"/>')); }
fs.writeFileSync("Crowdfund_Compass_Group11.pptx", await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
await applyTheme("Crowdfund_Compass_Group11.pptx", THEME); console.log("written");
})();
