#### Crowdfund Compass — pre-launch readiness check for Kickstarter campaigns
#### HSG, Business Analytics & Data Science Applications, Group 11
#### Built on the course's Streamlit template (app_v5_final.py): page config -> cached loaders -> header -> sections
#########################################################

import datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

import preprocess as P
import advice as A

st.set_page_config(page_title="Crowdfund Compass", page_icon="🧭", layout="wide")

NAVY, TEAL, GREEN, AMBER, RED, GREY = "#1B2A41", "#0F7C82", "#2E8B57", "#D98E04", "#C0392B", "#EEF0F3"

st.markdown(f"""<style>
.block-container {{padding-top: 2rem; max-width: 1150px;}}
h1, h2, h3 {{color: {NAVY};}}
.cc-card {{background: #FFFFFF; border: 1px solid #E3E6EB; border-radius: 12px; padding: 1.1rem 1.3rem; margin-bottom: 1rem;}}
.cc-note {{color: #5B6676; font-size: 0.88rem;}}
.cc-big {{font-size: 2.1rem; font-weight: 700; color: {NAVY}; line-height: 1.2;}}
.cc-pill {{display: inline-block; padding: .35rem .9rem; border-radius: 999px; color: white; font-weight: 600; font-size: 1.05rem;}}
.cc-bar {{background: {GREY}; border-radius: 6px; height: 14px; width: 100%;}}
.cc-fill {{height: 14px; border-radius: 6px;}}
</style>""", unsafe_allow_html=True)


#### Load functions (cached, as in the course template)
#########################################################

@st.cache_resource
def load_model():
    art, meta, text = P.load_artifacts()
    return A.Advisor(art), meta, text

advisor, META, TEXT = load_model()

@st.cache_data
def category_table():
    t = pd.DataFrame([{"cat_id": int(k), **v} for k, v in META["categories"].items()])
    return t.sort_values(["parent", "name"])

CATS = category_table()

@st.cache_data
def similar_table():
    return pd.read_parquet(P.os.path.join(P.HERE, 'models', 'similar.parquet'))

# Plain-language names for the model's inputs (used in "Why this result?")
LABELS = {
    "text_score": "the type of product (as described in title and blurb)", "cat_id": "the category", "parent_c": "the main category",
    "country_c": "the country", "log_goal_usd": "the size of the goal", "goal_ratio": "the goal compared with similar campaigns",
    "log_goal_per_day": "the goal per campaign day", "duration_days": "the campaign length", "goal_is_round": "a round-number goal",
    "launch_month": "the launch month", "launch_weekday": "the launch weekday", "holiday_window": "running over Christmas",
    "log_prep_days": "the preparation time", "creator_prior_rate": "the creator's share of earlier campaigns funded",
    "creator_prior_funded": "the number of earlier funded campaigns", "creator_prior_n": "the number of earlier campaigns",
    "first_timer": "being a first-time creator", "log_days_since_last": "the time since the last campaign",
    "has_video": "the campaign video", "prelaunch_activated": "the pre-launch page", "name_len": "the title length",
    "name_words": "the number of words in the title", "blurb_len": "the blurb length", "blurb_words": "the number of words in the blurb",
    "name_has_digit": "a number in the title", "name_has_symbol": "punctuation in the title", "name_caps_share": "capital letters in the title",
    "blurb_flesch": "how easy the blurb is to read", "blurb_sentiment": "the tone of the blurb", "kw_exclaim": "an exclamation mark in the blurb",
    "kw_you": "addressing the reader ('you')", "kw_we": "speaking as 'we'", "kw_new_first": "words like 'new' or 'first'"}
COUNTRY_NAMES = {"US": "United States", "GB": "United Kingdom", "CA": "Canada", "AU": "Australia", "DE": "Germany", "FR": "France",
                 "IT": "Italy", "HK": "Hong Kong", "ES": "Spain", "MX": "Mexico", "NL": "Netherlands", "SE": "Sweden", "JP": "Japan",
                 "SG": "Singapore", "NZ": "New Zealand", "DK": "Denmark", "CH": "Switzerland", "PL": "Poland", "IE": "Ireland",
                 "BE": "Belgium", "AT": "Austria", "NO": "Norway", "GR": "Greece", "SI": "Slovenia", "LU": "Luxembourg"}
COUNTRY_CODES = {v.lower(): k for k, v in COUNTRY_NAMES.items()}

def middle(low, high):
    """Middle of the chance range (on the odds scale). Checked on one public figure: tabletop games 2024, official 80%, middle 78%."""
    lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
    return float(1 / (1 + np.exp(-(lg(low) + lg(high)) / 2)))

AREA_TEXT = {
    "Ambition": ("Ambition", "Goal and campaign length"), "Timing": ("Timing", "Preparation time and launch day"),
    "Pitch": ("Pitch", "Length and form of title and blurb"), "Presentation": ("Presentation", "Pre-launch page and video"),
    "Founder": ("Founder (context)", "Track record of earlier campaigns"),
    "Market": ("Product type (context)", "How your type of product has done")}


#### Helpers
#########################################################

def band(score):
    return (RED, "weak") if score <= 25 else (AMBER, "to improve") if score <= 60 else (GREEN, "strong")

def tree_path(x):
    """Follow the campaign through the small decision tree and describe each step in plain words."""
    t = META["tree"]; node = 0; steps = []
    while t["left"][node] != -1:
        f = t["features"][t["feature"][node]]; thr = t["threshold"][node]
        val = x[f]; val = -1 if pd.isna(val) else val
        go_left = val <= thr
        if f == "creator_prior_rate" and thr > 0.9:
            steps.append("Most, but not all, earlier campaigns funded" if go_left else "All earlier campaigns funded")
        elif f == "creator_prior_rate":
            steps.append("No strong track record yet (first campaign, or fewer than about two thirds of earlier campaigns funded)" if go_left
                         else "Strong track record: most earlier campaigns were funded")
        elif f == "prelaunch_activated":
            steps.append("No pre-launch page" if go_left else "Has a pre-launch page")
        elif f == "log_goal_usd":
            steps.append(f"Goal up to about ${10 ** thr:,.0f}" if go_left else f"Goal above about ${10 ** thr:,.0f}")
        elif f == "creator_prior_funded":
            steps.append(f"Up to {int(thr)} earlier funded campaigns" if go_left else f"More than {int(thr)} earlier funded campaigns")
        else:
            steps.append(f"{LABELS.get(f, f)} {'low' if go_left else 'high'}")
        node = t["left"][node] if go_left else t["right"][node]
    share = t["funded_share"][node]
    level = "lower" if share < 0.4 else "middle" if share < 0.75 else "higher"
    return steps, level

def check(c):
    """Run the whole check for one campaign: features -> chance range -> areas -> fixes -> verdict."""
    X = P.campaign_features(c, META, TEXT)
    low, high = advisor.chances(X)
    areas = advisor.area_scores(X).iloc[0]
    fixes = advisor.fixes(X.iloc[0], min_budget_usd=c["min_budget_usd"])
    verdict = advisor.verdict(low[0], fixes)
    shap = advisor.shap(X).iloc[0].sort_values()
    return {"X": X, "low": float(low[0]), "high": float(high[0]), "areas": areas, "fixes": fixes, "verdict": verdict, "shap": shap}


#### Header and navigation
#########################################################

st.title("🧭 Crowdfund Compass")
st.markdown("A readiness check for Kickstarter campaigns **before** launch. Built from about 44,000 recent campaigns. "
            "It compares your plan with past campaigns. It does not promise an outcome.")

# Navigation in the main area (a sidebar is hidden on narrow screens)
page = st.radio("Page", ["Launch check-up", "Goal optimizer", "Coach cohort view", "Similar campaigns", "Category benchmarks", "How it works"],
                horizontal=True, label_visibility="collapsed")
st.caption("HSG · Business Analytics & Data Science Applications · Group 11 · Kleymenov, Arcauz, Braun")


#### Inputs (shared by the check-up and the goal optimizer)
#########################################################

def campaign_inputs():
    st.subheader("Your campaign")
    c1, c2, c3 = st.columns(3)
    parent = c1.selectbox("Main category", sorted(CATS.parent.unique()), index=sorted(CATS.parent.unique()).index("Games"))
    sub = CATS[CATS.parent == parent]
    names = sub.name.tolist()
    cat_name = c2.selectbox("Category", names, index=names.index("Tabletop Games") if "Tabletop Games" in names else 0)
    country_names = sorted(COUNTRY_NAMES.values())
    country = COUNTRY_CODES[c3.selectbox("Country", country_names, index=country_names.index("Switzerland")).lower()]
    name = st.text_input("Campaign title", "Alpine Trails: A Cooperative Hiking Board Game for 1–4 Players", max_chars=85)
    blurb = st.text_area("Blurb (the one or two sentences under the title)",
                         "Plan your route, share your supplies and reach the summit together before the weather turns.", max_chars=135, height=70)
    c1, c2, c3, c4 = st.columns(4)
    goal = c1.number_input("Funding goal (USD)", min_value=100, max_value=5_000_000, value=15_000, step=500)
    min_budget = c2.number_input("Minimum budget you need (USD)", min_value=0, max_value=5_000_000, value=9_000, step=500,
                                 help="The goal is never suggested below this amount.")
    duration = c3.slider("Campaign length (days)", 5, 60, 30)
    launch = c4.date_input("Planned launch date", dt.date.today() + dt.timedelta(days=30))
    c1, c2, c3, c4 = st.columns(4)
    prep = c1.number_input("Days of preparation before launch", min_value=0, max_value=1500, value=30,
                           help="From the day you started the project page to the launch.")
    video = c2.checkbox("Campaign video", True)
    prelaunch = c3.checkbox("Pre-launch page", False, help="A 'notify me on launch' page opened before the campaign starts.")
    first = c4.checkbox("This is my first campaign", True)
    prior_n = prior_funded = 0; since = 0
    if not first:
        c1, c2, c3 = st.columns(3)
        prior_n = c1.number_input("Earlier campaigns (finished)", min_value=1, max_value=200, value=1)
        prior_funded = c2.number_input("Of which funded", min_value=0, max_value=int(prior_n), value=min(1, int(prior_n)))
        since = c3.number_input("Days since your last campaign ended", min_value=0, max_value=6000, value=180)
    return {"cat_id": int(sub[sub.name == cat_name].cat_id.iloc[0]), "country": country, "name": name, "blurb": blurb,
            "goal_usd": float(goal), "min_budget_usd": float(min(min_budget, goal)), "duration_days": duration,
            "launch_date": pd.Timestamp(launch), "prep_days": prep, "has_video": int(video), "prelaunch": int(prelaunch),
            "prior_n": int(prior_n), "prior_funded": int(prior_funded), "days_since_last": since}


#### Page 1: Launch check-up
#########################################################

if page == "Launch check-up":
    c = campaign_inputs()
    r = check(c)
    st.markdown("---")
    st.subheader("Result")
    left, right = st.columns([1, 1])

    colour = {"Launch": GREEN, "Adjust": AMBER, "Coach first": RED}[r["verdict"]]
    explain = {"Launch": "Ready as planned. No single change stands out.",
               "Adjust": "Worth changing one thing before launch (see 'What to change').",
               "Coach first": "Among the riskiest plans. Talk it through with a coach before launching."}[r["verdict"]]
    left.markdown(f"<div class='cc-card'><span class='cc-note'>Verdict</span><br><span class='cc-pill' style='background:{colour}'>{r['verdict']}</span>"
                  f"<p style='margin:.6rem 0 0 0'>{explain}</p></div>", unsafe_allow_html=True)
    right.markdown(f"<div class='cc-card'><span class='cc-note'>Chance of reaching the goal</span><br>"
                   f"<span class='cc-big'>most likely about {middle(r['low'], r['high']) * 100:.0f}%</span><br>"
                   f"<b>between {r['low'] * 100:.0f}% and {r['high'] * 100:.0f}%</b>"
                   f"<p class='cc-note' style='margin:.4rem 0 0 0'>Why the range is wide: our data shows only about 4 in 10 failed campaigns, so the true level is uncertain. "
                   f"Upper value = campaigns like yours in our data. Lower value = adjusted to Kickstarter's official all-time rates. "
                   f"'Most likely' is the middle of the two. How plans rank against each other is much more certain than the percentage.</p></div>", unsafe_allow_html=True)

    # Six area bars
    st.subheader("Where the plan is strong and weak")
    st.markdown("<span class='cc-note'>Each bar compares one area of your plan with recent campaigns. 50 = typical. "
                "Green = strong, amber = to improve, red = weak. The last two are context: you cannot change them before launch.</span>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, a in enumerate(["Ambition", "Timing", "Pitch", "Presentation", "Founder", "Market"]):
        s = float(r["areas"][a]); col, word = band(s); title, sub = AREA_TEXT[a]
        if a == "Founder" and c["prior_n"] == 0:           # a first campaign is not a weakness: show it neutrally, without a score
            cols[i % 3].markdown(f"<div class='cc-card'><b>{title}</b><div class='cc-bar'></div>"
                                 f"<span class='cc-note'><b>First campaign: no track record yet.</b> Creators with funded campaigns behind them do better, "
                                 f"so preparation matters more for you.</span></div>", unsafe_allow_html=True)
            continue
        cols[i % 3].markdown(f"<div class='cc-card'><b>{title}</b> · <span style='color:{col}'>{word}</span> <span style='float:right'><b>{s:.0f}</b>/100</span>"
                             f"<div class='cc-bar'><div class='cc-fill' style='width:{max(s, 3):.0f}%;background:{col}'></div></div>"
                             f"<span class='cc-note'>{sub}</span></div>", unsafe_allow_html=True)
    if r["areas"]["Market"] <= 15:
        st.warning("**Note for coaches:** this type of product has rarely been funded on Kickstarter (typical examples: apps, software, web platforms, "
                   "restaurants, drinks). Changing the campaign set-up will not fix that. Consider whether Kickstarter is the right route.")

    # What to change
    st.subheader("What to change")
    if r["fixes"]:
        for f in r["fixes"]:
            st.markdown(f"<div class='cc-card'><b style='color:{TEAL}'>+{f['gain']:.0f} points</b> &nbsp; {f['change']}"
                        f"<br><span class='cc-note'>Campaigns that did this were funded more often. Chance would then be between {f['low']:.0f}% and {f['high']:.0f}%.</span></div>",
                        unsafe_allow_html=True)
        if any(f["lever"] in ("Pre-launch page", "Preparation") for f in r["fixes"]):
            st.markdown("<span class='cc-note'>A pre-launch page and more preparation time stand for groundwork: building an audience before launch. "
                        "Opening a page the day before launch will not add these points.</span>", unsafe_allow_html=True)
    else:
        st.info("No single change to goal, length, launch day, video, pre-launch page, preparation time, title or blurb is linked to at least 2 more points.")
    st.markdown("<span class='cc-note'>These are patterns in past campaigns, not causes. We tried one change at a time and never a goal below your minimum budget.</span>",
                unsafe_allow_html=True)

    # Why
    st.subheader("Why this result?")
    w1, w2 = st.columns(2)
    up = r["shap"][r["shap"] > 0.03].sort_values(ascending=False).head(4); down = r["shap"][r["shap"] < -0.03].head(4)
    w1.markdown("**Helps your chances**\n\n" + ("\n".join(f"- {LABELS.get(k, k).capitalize()}" for k in up.index) or "- Nothing stands out"))
    w2.markdown("**Holds your chances back**\n\n" + ("\n".join(f"- {LABELS.get(k, k).capitalize()}" for k in down.index) or "- Nothing stands out"))
    steps, level = tree_path(r["X"].iloc[0])
    st.markdown("**In three steps** (a simple decision tree): " + " → ".join(steps) + f" → campaigns on this path had a **{level}** funding rate.")
    st.markdown(f"<span class='cc-note'>Model quality on campaigns launched in 2025, which it had never seen: AUC {META['test']['auc_within_category_2025']:.2f} within category "
                f"(0.5 = guessing, 1 = perfect). See 'How it works' for limits.</span>", unsafe_allow_html=True)


#### Page 2: Goal optimizer
#########################################################

if page == "Goal optimizer":
    c = campaign_inputs()
    st.markdown("---")
    st.subheader("How the chance changes with the goal")
    X = P.campaign_features(c, META, TEXT)
    goals = np.unique(np.round(np.geomspace(max(c["goal_usd"] * 0.2, 100), c["goal_usd"] * 3, 40), -1))
    V = pd.concat([X] * len(goals), ignore_index=True)
    d = np.log10(goals / c["goal_usd"])
    V["goal_usd"] = goals; V["log_goal_usd"] = np.log10(goals); V["goal_ratio"] = X.goal_ratio.iloc[0] + d; V["log_goal_per_day"] = X.log_goal_per_day.iloc[0] + d
    low, high = advisor.chances(V)
    curve = pd.DataFrame({"Goal (USD)": goals, "low": low * 100, "high": high * 100})
    base = alt.Chart(curve).encode(x=alt.X("Goal (USD):Q", scale=alt.Scale(type="log"), axis=alt.Axis(format="~s")))
    chart = (base.mark_area(opacity=0.25, color=TEAL).encode(y=alt.Y("low:Q", title="Chance of reaching the goal (%)", scale=alt.Scale(domain=[0, 100])), y2="high:Q")
             + base.mark_line(color=TEAL).encode(y="high:Q") + base.mark_line(color=NAVY, strokeDash=[4, 3]).encode(y="low:Q")
             + alt.Chart(pd.DataFrame({"x": [c["goal_usd"]]})).mark_rule(color=NAVY).encode(x="x:Q")
             + alt.Chart(pd.DataFrame({"x": [max(c["min_budget_usd"], goals.min())]})).mark_rule(color=RED, strokeDash=[2, 2]).encode(x="x:Q"))
    st.altair_chart(chart.properties(height=360), width='stretch')
    st.markdown("<span class='cc-note'>Shaded band = chance range (upper line: our data; dashed lower line: adjusted to Kickstarter's official rates). "
                "Solid vertical line = your goal. Red dashed line = your minimum budget.</span>", unsafe_allow_html=True)
    cut = META["verdict"]["reference_cut"] * 100
    def at(goal):                                      # chance range at one goal, read off the curve
        row = curve.iloc[(curve["Goal (USD)"] - goal).abs().argmin()]
        return f"about {middle(row.low / 100, row.high / 100) * 100:.0f}% (between {row.low:.0f}% and {row.high:.0f}%)"
    options = [("Minimum budget", c["min_budget_usd"]), ("Your goal", c["goal_usd"]), ("Your goal + 50%", c["goal_usd"] * 1.5)]
    st.table(pd.DataFrame({"Goal": [f"${g:,.0f}" for _, g in options], "Chance of reaching it": [at(g) for _, g in options]},
                          index=[n for n, _ in options]))
    ok = curve[(curve["Goal (USD)"] >= c["min_budget_usd"]) & (curve.low >= cut)]
    if len(ok) == 0:
        st.warning("At any goal that covers your minimum budget, this plan stays in the riskiest group. The goal is not the main problem: look at the check-up.")
    elif ok["Goal (USD)"].max() >= goals.max():
        st.success("Even at three times your goal the plan stays outside the riskiest group. The goal is not what holds this campaign back.")
    else:
        g = ok["Goal (USD)"].max()
        st.info(f"Above a goal of about **${g:,.0f}** this plan falls into the riskiest group ('Coach first'). "
                f"That is the highest goal that still covers your minimum budget and stays out of it.")
    st.markdown("<span class='cc-note'>Pattern in past campaigns, not a cause: campaigns with lower goals were funded more often, everything else equal.</span>", unsafe_allow_html=True)


#### Page 3: Coach cohort view
#########################################################

COHORT_COLUMNS = ["title", "blurb", "main_category", "category", "country", "goal_usd", "min_budget_usd", "duration_days", "launch_date",
                  "prep_days", "has_video", "prelaunch_page", "earlier_campaigns", "earlier_funded", "days_since_last"]
EXAMPLE_COHORT = pd.DataFrame([
    ["Alpine Trails: A Cooperative Hiking Board Game", "Plan your route, share supplies and reach the summit together.", "Games", "Tabletop Games", "Switzerland", 15000, 9000, 30, "2027-02-02", 30, 1, 0, 0, 0, 0],
    ["BudgetBuddy: the AI app that manages your money", "A mobile application platform empowering students to track spending.", "Technology", "Apps", "CH", 60000, 40000, 45, "2027-02-10", 3, 0, 0, 0, 0, 0],
    ["Night Harbor #4: A 32-Page Noir Fantasy Comic", "Issue 4 of the indie graphic novel series. Variant covers and enamel pins.", "Comics", "Comic Books", "DE", 3000, 2000, 21, "2027-02-16", 60, 1, 1, 4, 4, 200],
    ["Zürich Rooftop Honey", "Small batch honey from city bees, delivered to your door.", "Food", "Small Batch", "CH", 8000, 5000, 30, "2027-03-01", 10, 1, 0, 0, 0, 0],
    ["The Lantern Keeper: An Illustrated Children's Book", "A hardcover picture book about a girl who lights the mountain paths.", "Publishing", "Children's Books", "AT", 6000, 4000, 30, "2027-02-23", 45, 1, 1, 1, 1, 400],
    ["Docu: Voices of the Rhine", "A feature documentary about the people living along the river.", "Film & Video", "Documentary", "CH", 25000, 15000, 40, "2027-03-09", 20, 1, 0, 1, 0, 700],
], columns=COHORT_COLUMNS)

def score_cohort(df, capacity):
    """Match the uploaded columns to the expected ones, score every campaign, rank by risk and assign the verdicts."""
    df = df.rename(columns={c: c.strip().lower().replace(" ", "_") for c in df.columns})
    missing = [c for c in COHORT_COLUMNS if c not in df.columns]
    if missing:
        return None, f"These columns are missing: {', '.join(missing)}. Download the template to see the expected format."
    rows, problems = [], []
    lookup = {(r.parent.lower(), r["name"].lower()): r.cat_id for _, r in CATS.iterrows()}
    for i, x in df.iterrows():
        try:
            cat_id = lookup[(str(x.main_category).strip().lower(), str(x.category).strip().lower())]
            c = {"cat_id": cat_id, "country": COUNTRY_CODES.get(str(x.country).strip().lower(), str(x.country).strip().upper()), "name": str(x.title), "blurb": "" if pd.isna(x.blurb) else str(x.blurb),
                 "goal_usd": float(x.goal_usd), "min_budget_usd": float(min(x.min_budget_usd, x.goal_usd)), "duration_days": float(x.duration_days),
                 "launch_date": pd.Timestamp(x.launch_date), "prep_days": float(x.prep_days), "has_video": int(x.has_video), "prelaunch": int(x.prelaunch_page),
                 "prior_n": int(x.earlier_campaigns), "prior_funded": int(min(x.earlier_funded, x.earlier_campaigns)), "days_since_last": float(x.days_since_last)}
            r = check(c)
            levers = ["Ambition", "Timing", "Pitch", "Presentation"]
            rows.append({"Campaign": c["name"], "Most likely chance (%)": round(middle(r["low"], r["high"]) * 100),
                         "Chance (low)": round(r["low"] * 100), "Chance (high)": round(r["high"] * 100),
                         "Weakest area": min(levers, key=lambda a: r["areas"][a]), "Top fix": r["fixes"][0]["change"] if r["fixes"] else "No single change stands out",
                         "Gain (points)": round(r["fixes"][0]["gain"]) if r["fixes"] else 0,
                         "Product type rarely funded": "yes" if r["areas"]["Market"] <= 15 else "", "_low": r["low"]})
        except KeyError:
            problems.append(f"Row {i + 1}: category '{x.main_category} / {x.category}' not found")
        except Exception as e:
            problems.append(f"Row {i + 1}: could not be read ({type(e).__name__})")
    if not rows:
        return None, "No row could be scored. " + "; ".join(problems[:5])
    out = pd.DataFrame(rows).sort_values("_low").reset_index(drop=True)
    n_coach = int(round(len(out) * capacity))                                # the coach's capacity decides who is 'Coach first'
    out["Verdict"] = np.where(out.index < n_coach, "Coach first", np.where(out["Gain (points)"] >= META["verdict"]["adjust_gain"], "Adjust", "Launch"))
    out.insert(0, "Risk rank", out.index + 1)
    return out.drop(columns="_low"), "; ".join(problems)

if page == "Coach cohort view":
    st.subheader("Triage a whole cohort")
    st.markdown("Upload one row per planned campaign. The app ranks the cohort from riskiest to safest and marks the campaigns to see first. "
                "The ranking is the reliable part; the chances are a rough range.")
    c1, c2 = st.columns([1, 1])
    c1.download_button("Download the CSV template", EXAMPLE_COHORT.to_csv(index=False).encode("utf-8"), file_name="cohort_template.csv")
    capacity = c2.slider("Share of the cohort you can coach (%)", 10, 60, int(META["verdict"]["default_capacity"] * 100), step=5) / 100
    uploaded = st.file_uploader("Choose a CSV file with your cohort", type="csv")
    use_example = st.checkbox("Use the example cohort (6 campaigns)", value=uploaded is None)
    data = pd.read_csv(uploaded) if uploaded is not None else (EXAMPLE_COHORT if use_example else None)
    if data is not None:
        result, message = score_cohort(data, capacity)
        if result is None:
            st.error(message)
        else:
            if message: st.warning(message)
            n = (result.Verdict == "Coach first").sum()
            st.success(f"Scored {len(result)} campaigns. Coach first: {n} · Adjust: {(result.Verdict == 'Adjust').sum()} · Launch: {(result.Verdict == 'Launch').sum()}")
            colours = {"Coach first": "#F6D5D1", "Adjust": "#FBE8C4", "Launch": "#D5EDDF"}
            st.dataframe(result.style.apply(lambda row: [f"background-color: {colours[row.Verdict]}" if col == "Verdict" else "" for col in result.columns], axis=1),
                         hide_index=True, width="stretch")
            st.download_button("Download the result as CSV", result.to_csv(index=False).encode("utf-8"), file_name="cohort_result.csv")
            st.markdown("<span class='cc-note'>In past data, the riskiest 30% of a cohort contained about half of all campaigns that later failed, "
                        "and nearly all campaigns in that group failed. Patterns, not causes.</span>", unsafe_allow_html=True)


#### Page 4: Similar campaigns (nearest neighbours)
#########################################################

if page == "Similar campaigns":
    c = campaign_inputs()
    st.markdown("---")
    st.subheader("Past campaigns most like yours")
    same_country = st.checkbox("Only campaigns from the same country", False)
    X = P.campaign_features(c, META, TEXT).iloc[0]
    S = similar_table(); sm = META["similar"]
    pool = S[S.parent_category == X.parent_category]
    if same_country:
        if (pool.country == c["country"]).sum() >= 20:
            pool = pool[pool.country == c["country"]]
        else:
            st.info(f"Fewer than 20 past {X.parent_category} campaigns from {COUNTRY_NAMES[c['country']]} in our data, so all countries are shown.")
    mine = {"log_goal_usd": X.log_goal_usd, "duration_days": X.duration_days, "log_prep_days": X.log_prep_days,
            "log_prior": np.log10(X.creator_prior_n + 1), "prelaunch_activated": X.prelaunch_activated, "has_video": X.has_video,
            "text_score": X.text_score, "first_timer": X.first_timer}
    # distance on standardised values: every input counts the same
    dist = sum(((pool[f].values - mine[f]) / sm["std"][f]) ** 2 for f in sm["features"])
    near = pool.iloc[np.argsort(dist)[:10]].copy()
    funded = int(near.success.sum())
    st.markdown(f"<div class='cc-card'><span class='cc-big'>{funded} of 10</span> most similar past campaigns were funded."
                f"<p class='cc-note' style='margin:.4rem 0 0 0'>Similar = same main category and closest on goal, length, preparation time, creator experience, "
                f"video, pre-launch page and type of product. Our data misses many failed campaigns, so this count is on the optimistic side.</p></div>", unsafe_allow_html=True)
    names = CATS.set_index("cat_id").name
    show = pd.DataFrame({"Campaign": near.name.values, "Category": near.cat_id.map(names).fillna("").values, "Country": near.country.astype(str).map(COUNTRY_NAMES).values,
                         "City": near.city.fillna("").values, "Launched": near.launch_year.values, "Goal (USD)": near.goal_usd.values,
                         "Outcome": np.where(near.success == 1, "Funded", "Not funded"),
                         "Find it": ["https://www.kickstarter.com/discover/advanced?term=" + P.quote(n) for n in near.name.values]})
    st.dataframe(show, hide_index=True, width="stretch",
                 column_config={"Find it": st.column_config.LinkColumn("Find it", display_text="Search on Kickstarter"),
                                "Goal (USD)": st.column_config.NumberColumn(format="$%d")})
    st.markdown(f"<span class='cc-note'>Drawn from {sm['n']:,} campaigns launched from 2023 to June 2026. Source: public Kickstarter listings collected by Web Robots "
                f"(webrobots.io/kickstarter-datasets). No creator names are stored.</span>", unsafe_allow_html=True)


#### Page 5: Category benchmarks
#########################################################

if page == "Category benchmarks":
    st.subheader("Category benchmarks")
    parents = sorted(META["official_rate"])
    parent = st.selectbox("Main category", parents, index=parents.index("Games"))
    rate = META["official_rate"][parent]; overall = 0.4273
    c1, c2 = st.columns([1, 2])
    c1.markdown(f"<div class='cc-card'><span class='cc-note'>Official funding rate, {parent}</span><br><span class='cc-big'>{rate * 100:.0f}%</span>"
                f"<p class='cc-note' style='margin:.4rem 0 0 0'>Share of all {META['official_launched'][parent]:,} {parent} campaigns ever launched on Kickstarter that reached "
                f"their goal. All categories: {overall * 100:.0f}%. This is an all-time average; recent rates are higher.</p></div>", unsafe_allow_html=True)
    off = pd.DataFrame({"Category": parents, "rate": [META["official_rate"][p] * 100 for p in parents]})
    off["picked"] = off.Category == parent
    bars = alt.Chart(off).mark_bar().encode(
        x=alt.X("rate:Q", title="Official funding rate, all time (%)", scale=alt.Scale(domain=[0, 80])), y=alt.Y("Category:N", sort="-x", title=None),
        color=alt.condition(alt.datum.picked, alt.value(TEAL), alt.value("#C5CAD3")), tooltip=["Category", alt.Tooltip("rate:Q", format=".0f")])
    c2.altair_chart(bars.properties(height=330), width="stretch")
    st.markdown("<span class='cc-note'>Source: Kickstarter stats page, last updated 1 January 2026.</span>", unsafe_allow_html=True)

    st.subheader(f"What funded {parent} campaigns look like")
    st.markdown("<span class='cc-note'>From campaigns in our data that were funded, launched from 2023 to June 2026. We hold about 85% of all funded campaigns, "
                "so these figures are reliable. We do not show funding rates from our data: it misses too many failed campaigns.</span>", unsafe_allow_html=True)
    B = META["benchmarks"]; rows = [("All " + parent, B["parent"][parent])]
    for _, r in CATS[CATS.parent == parent].iterrows():
        if str(r.cat_id) in B["category"]: rows.append((r["name"], B["category"][str(r.cat_id)]))
    table = pd.DataFrame([{"Category": n, "Funded campaigns": p["n"], "Typical goal (USD)": round(p["median_goal"]), "Typical amount raised (USD)": round(p["median_raised"]),
                           "Typical length (days)": round(p["median_days"]), "With pre-launch page (%)": round(p["prelaunch"] * 100),
                           "With video (%)": round(p["video"] * 100), "First-time creators (%)": round(p["first_timer"] * 100)} for n, p in rows])
    st.dataframe(table, hide_index=True, width="stretch",
                 column_config={"Typical goal (USD)": st.column_config.NumberColumn(format="$%d"), "Typical amount raised (USD)": st.column_config.NumberColumn(format="$%d")})
    st.markdown("<span class='cc-note'>'Typical' = median. Many funded campaigns set a low goal on purpose and raise several times that amount. "
                "Data: public Kickstarter listings collected by Web Robots (webrobots.io/kickstarter-datasets).</span>", unsafe_allow_html=True)


#### Page 6: How it works
#########################################################

if page == "How it works":
    T = META["test"]
    st.subheader("How it works")
    st.markdown(f"""
**The decision.** Before launch, every campaign gets one verdict: *Launch*, *Adjust* (change one named thing) or *Coach first*. It is made for startup coaches who have limited hours, and for founders checking one plan.

**The data.** Public Kickstarter listings collected by Web Robots, 24 snapshots from 2016 to 2026 (about 489,000 campaigns). The model is trained on {T['n_train']:,} campaigns launched in 2023–2024 and tested on {T['n_test_2025']:,} campaigns launched in 2025, which it had never seen.

**The method.** 32 inputs known before launch, in six areas (ambition, timing, pitch, founder, presentation, product type). The model is XGBoost, a method from class, tuned with grid search and time-ordered cross-validation.

**Test results (2025).** AUC within category {T['auc_within_category_2025']:.2f} (January–June 2026: {T['auc_within_category_2026h1']:.2f}); accuracy {T['accuracy_2025'] * 100:.0f}% against 71% for always saying "funded". With only the six inputs of a typical public dataset the AUC is 0.75.

**The verdict rule.** *Coach first* = among the riskiest 30% of a cohort (for a single check: lower chance below {META['verdict']['reference_cut'] * 100:.1f}%). *Adjust* = one change is linked to at least {META['verdict']['adjust_gain']:.0f} more points. *Launch* = otherwise.
""")
    st.subheader("Limits you should know")
    st.markdown("""
- **Our data misses many failed campaigns.** We hold about 85% of all funded campaigns but about 42% of the failed ones, because Kickstarter's listings hide most campaigns that failed. Chances from our data alone are too high. That is why the app shows a range, with the lower value adjusted to Kickstarter's official funding rates.
- **Why the range is wide, and what "most likely" means.** The lower and upper value differ by about 15 points on average. "Most likely" is the middle of the two. We could check it on one public figure: Kickstarter reported that 80% of tabletop game campaigns launched in 2024 were funded; our middle value for those campaigns is 78% (lower 66%, upper 86%).
- **The ranking is more reliable than the level.** The model is good at telling stronger plans from weaker ones. The exact percentage is rough.
- **Patterns, not causes.** "Campaigns with a pre-launch page were funded more often" does not mean a page causes funding.
- **Most of the result is not in the founder's hands.** What is being made and the creator's track record explain 57% of the model's result; goal, timing, presentation and pitch explain 43%.
- **Funding is a market test,** not proof that a company will survive.
- Data up to November 2026.
""")
    st.subheader("Methods: from class and beyond")
    st.markdown("""
| Step | Method | From class? |
|---|---|---|
| Prediction | XGBoost, compared with logistic regression, decision tree, random forest | Class |
| Similar campaigns | Nearest neighbours | Beyond class |
| Tuning and testing | Grid search, time-ordered cross-validation, confusion matrix, precision, recall, F1, ROC-AUC | Class |
| Title and blurb | TF-IDF text mining | Class |
| Explanation path | Decision tree, depth 3 | Class |
| Product-type score | Text model fed into the main model (stacking) | Beyond class |
| Goal rule | The model may only learn that a higher goal lowers the chance | Beyond class |
| Chance range | Calibration (Platt scaling) and adjustment to official rates | Beyond class |
| Area bars and "why" | SHAP values | Beyond class |
| What to change | One-change-at-a-time comparison | Beyond class |
""")
    st.markdown("<span class='cc-note'>AI use: code and analysis were developed with Claude (Anthropic, model Fable 5.2) in November 2026 and reviewed by the team. "
                "Official rates: Kickstarter stats page, last updated 1 January 2026.</span>", unsafe_allow_html=True)
