#### Crowdfund Compass — pre-launch readiness check for Kickstarter campaigns
#### HSG, Business Analytics & Data Science Applications, Group 11
#### Structure follows the course template (app_v5_final.py): page config -> cached loaders -> header -> sections.
#### This file and ui.py only decide how results are SHOWN. All numbers come from the model files in models/.
#########################################################

from html import escape
import datetime as dt
import os
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

import hashlib
import importlib
import features, modeling
import preprocess as P
import advice as A
import ui
# Streamlit Cloud can keep old copies of our modules in memory after an update: always load the current ones,
# and tie the cached model to the code version, so a code change always builds a fresh Advisor.
for _m in (features, modeling, P, A, ui):
    importlib.reload(_m)
CODE_VERSION = hashlib.md5(b"".join(open(m.__file__, "rb").read() for m in (features, modeling, P, A))).hexdigest()

st.set_page_config(page_title="Crowdfund Compass", page_icon=os.path.join(P.HERE, "assets", "favicon.png"), layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(ui.CSS, unsafe_allow_html=True)
ui.chart_theme()


#### Load functions (cached, as in the course template)
#########################################################

@st.cache_resource(show_spinner="Loading the model…")
def load_model(code_version):
    art, meta, text = P.load_artifacts()
    return A.Advisor(art), meta, text

advisor, META, TEXT = load_model(CODE_VERSION)

@st.cache_data
def category_table():
    t = pd.DataFrame([{"cat_id": int(k), **v} for k, v in META["categories"].items()])
    return t.sort_values(["parent", "name"])

@st.cache_data(show_spinner="Loading past campaigns…")
def similar_table():
    return pd.read_parquet(os.path.join(P.HERE, "models", "similar.parquet"))

CATS = category_table()

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
    "name_has_digit": "a number in the title", "name_has_symbol": "punctuation in the title", "blurb_flesch": "how easy the blurb is to read",
    "blurb_sentiment": "the tone of the blurb", "kw_exclaim": "an exclamation mark in the blurb", "kw_you": "addressing the reader ('you')",
    "kw_we": "speaking as 'we'", "kw_new_first": "words like 'new' or 'first'"}
LEVERS = {"Ambition": "goal and campaign length", "Timing": "preparation time and launch day",
          "Presentation": "pre-launch page and video", "Pitch": "length and form of title and blurb"}
AREA_OF = {"Goal": "Ambition", "Duration": "Ambition", "Launch day": "Timing", "Launch date": "Timing", "Preparation": "Timing",
           "Video": "Presentation", "Pre-launch page": "Presentation", "Title": "Pitch", "Blurb": "Pitch"}
COUNTRY_NAMES = {"US": "United States", "GB": "United Kingdom", "CA": "Canada", "AU": "Australia", "DE": "Germany", "FR": "France",
                 "IT": "Italy", "HK": "Hong Kong", "ES": "Spain", "MX": "Mexico", "NL": "Netherlands", "SE": "Sweden", "JP": "Japan",
                 "SG": "Singapore", "NZ": "New Zealand", "DK": "Denmark", "CH": "Switzerland", "PL": "Poland", "IE": "Ireland",
                 "BE": "Belgium", "AT": "Austria", "NO": "Norway", "GR": "Greece", "SI": "Slovenia", "LU": "Luxembourg"}
COUNTRY_CODES = {v.lower(): k for k, v in COUNTRY_NAMES.items()}
DEFAULT = {"parent": "Games", "cat_name": "Tabletop Games", "country": "CH",
           "name": "Alpine Trails: A Cooperative Hiking Board Game for 1–4 Players",
           "blurb": "Plan your route, share your supplies and reach the summit together before the weather turns.",
           "goal_usd": 15000.0, "min_budget_usd": 9000.0, "duration_days": 30, "launch_date": dt.date(2027, 1, 15),     # fixed, so the example gives the same result every day (slide 13)
           "prep_days": 30, "has_video": 1, "prelaunch": 0, "prior_n": 0, "prior_funded": 0, "days_since_last": 180}
RANGE_LABELS = ("The two ends are two estimates: one from our data, one adjusted to Kickstarter's official funding rate for the category "
                "(usually the lower one, because our data misses failed campaigns). Middle estimate: halfway between the two; checked against one public figure only.")
TIP_CHANCE = "The range is wide because our data shows only about 4 in 10 failed campaigns. " + RANGE_LABELS
COACH_TEST = ("In a test on 2025 campaigns, re-weighted to Kickstarter's official mix, a coach who sees the riskiest "
              "30% reached about half of all failures, and about 95% of the flagged campaigns failed. A new cohort may differ.")
FOUNDER_CONTROL = "Less than half of the model's explanation comes from things a founder can change"


#### Helpers (logic unchanged from version 1)
#########################################################

def middle(low, high):
    """Middle of the chance range (on the odds scale). Checked on one public figure: tabletop games 2024, official 80%, middle 78%."""
    lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
    return float(1 / (1 + np.exp(-(lg(low) + lg(high)) / 2)))

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
            steps.append("No strong track record yet" if go_left else "Strong track record: most earlier campaigns were funded")
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
    return steps, "lower" if share < 0.4 else "middle" if share < 0.75 else "higher"

def check(c):
    """Run the whole check for one campaign: features -> chance range -> areas -> fixes -> verdict."""
    X = P.campaign_features(c, META, TEXT)
    low, high = advisor.chances(X)
    ours, official = (float(v[0]) for v in advisor.estimates(X))
    areas = advisor.area_scores(X).iloc[0]
    every = advisor.fixes(X.iloc[0], min_budget_usd=c["min_budget_usd"], top=20, min_gain=-999)      # best option per lever, all levers
    fixes = [f for f in every if f["gain"] >= 2][:3]
    best = {}                                                                                        # best gain per area (points)
    for f in every:
        best[AREA_OF[f["lever"]]] = max(best.get(AREA_OF[f["lever"]], 0), f["gain"])
    return {"X": X, "area_best": best, "low": float(low[0]), "high": float(high[0]), "mid": middle(float(low[0]), float(high[0])), "areas": areas,
            "low_is_official": official <= ours,
            "fixes": fixes, "verdict": advisor.verdict(low[0], fixes), "shap": advisor.shap(X).iloc[0].sort_values()}

def step(n, title):
    st.markdown(f"<div class='cc-step'><span class='cc-num'>{n}</span><b>{title}</b></div>", unsafe_allow_html=True)

def campaign_inputs():
    """The input form in four numbered steps. Values are remembered when the user moves between pages."""
    d = st.session_state.get("campaign", DEFAULT)
    with st.container(border=True):
        step(1, "What are you making?")
        parents = sorted(CATS.parent.unique())
        parent = st.selectbox("Main category", parents, index=parents.index(d["parent"]))
        names = CATS[CATS.parent == parent].name.tolist()
        cat_name = st.selectbox("Category", names, index=names.index(d["cat_name"]) if d["cat_name"] in names else 0)
        name = st.text_input("Campaign title", d["name"], max_chars=85)
        blurb = st.text_area("Blurb (the one or two sentences under the title)", d["blurb"], max_chars=135, height=80)
    with st.container(border=True):
        step(2, "Money and timing")
        a, b = st.columns(2)
        goal = a.number_input("Funding goal (USD)", min_value=100, max_value=5_000_000, value=int(d["goal_usd"]), step=500)
        min_budget = b.number_input("Minimum budget (USD)", min_value=0, max_value=5_000_000, value=int(d["min_budget_usd"]), step=500,
                                    help="The least you need to deliver. A lower goal is never suggested below this amount.")
        duration = st.slider("Campaign length (days)", 5, 60, int(d["duration_days"]))
        a, b = st.columns(2)
        launch = a.date_input("Planned launch date", d["launch_date"])
        country_names = sorted(COUNTRY_NAMES.values())
        country = COUNTRY_CODES[b.selectbox("Country", country_names, index=country_names.index(COUNTRY_NAMES[d["country"]])).lower()]
    with st.container(border=True):
        step(3, "Preparation and presentation")
        prep = st.number_input("Days of preparation before launch", min_value=0, max_value=1500, value=int(d["prep_days"]),
                               help="From the day you started the project page to the launch.")
        a, b = st.columns(2)
        video = a.toggle("Campaign video", bool(d["has_video"]))
        prelaunch = b.toggle("Pre-launch page", bool(d["prelaunch"]), help="A 'notify me on launch' page opened before the campaign starts.")
    with st.container(border=True):
        step(4, "Your track record")
        first = st.toggle("This is my first campaign", d["prior_n"] == 0)
        prior_n = prior_funded = 0; since = d["days_since_last"]
        if not first:
            a, b = st.columns(2)
            prior_n = a.number_input("Earlier campaigns (finished)", min_value=1, max_value=200, value=max(1, int(d["prior_n"])))
            prior_funded = b.number_input("Of which funded", min_value=0, max_value=int(prior_n), value=min(int(d["prior_funded"]) if d["prior_n"] else 1, int(prior_n)))
            since = st.number_input("Days since your last campaign ended", min_value=0, max_value=6000, value=int(d["days_since_last"]))
    c = {"parent": parent, "cat_name": cat_name, "cat_id": int(CATS[(CATS.parent == parent) & (CATS.name == cat_name)].cat_id.iloc[0]),
         "country": country, "name": name, "blurb": blurb, "goal_usd": float(goal), "min_budget_usd": float(min(min_budget, goal)),
         "duration_days": duration, "launch_date": launch, "prep_days": prep, "has_video": int(video), "prelaunch": int(prelaunch),
         "prior_n": int(prior_n), "prior_funded": int(prior_funded), "days_since_last": since}
    st.session_state["campaign"] = c
    return dict(c, launch_date=pd.Timestamp(launch))

def current_campaign():
    """On pages without the full form: the last campaign entered, with a compact summary and a way to edit it."""
    c = st.session_state.get("campaign", dict(DEFAULT, cat_id=int(CATS[(CATS.parent == "Games") & (CATS.name == "Tabletop Games")].cat_id.iloc[0])))
    st.markdown(f"<div class='cc-card'><span class='cc-eyebrow'>Your campaign</span><div class='cc-h' style='margin:.2rem 0'>{c['name']}</div>"
                f"<span class='cc-note'>{c['parent']} · {c['cat_name']} · {COUNTRY_NAMES[c['country']]} · goal ${c['goal_usd']:,.0f} · {c['duration_days']} days</span></div>",
                unsafe_allow_html=True)
    with st.expander("Edit the campaign"):
        c = campaign_inputs()
        return c
    return dict(c, launch_date=pd.Timestamp(c["launch_date"]))


#### Header and navigation
#########################################################

PAGES = ["Home", "Check-up", "Goal optimizer", "Coach view", "Similar campaigns", "Benchmarks", "How it works"]
page = st.query_params.get("page", "Home")
if page not in PAGES:
    page = "Home"

def go(target):
    st.query_params["page"] = target

st.markdown(ui.header(), unsafe_allow_html=True)
if page == "Home":
    coach, founder = st.columns(2)
    coach.button("Open Coach view", type="primary", on_click=go, args=("Coach view",), width="stretch")
    founder.button("Check a campaign", on_click=go, args=("Check-up",), width="stretch")
else:
    for col, target in zip(st.columns(3), ("Home", "Coach view", "Check-up")):
        col.button(target, on_click=go, args=(target,), disabled=page == target, width="stretch")

secondary = ("Goal optimizer", "Similar campaigns", "Benchmarks", "How it works")
with st.container(horizontal=True):
    for target in secondary:
        st.button(target, type="tertiary", on_click=go, args=(target,), disabled=page == target)


#### Home
#########################################################

if page == "Home":
    T = META["test"]
    st.markdown(f"""<div class='cc-hero cc-fade'><span class='cc-eyebrow' style='color:#7FE3C4'>Pre-launch readiness check for Kickstarter</span>
<h1>See which campaigns are ready to launch, and which need a coach first.</h1>
<p>On Kickstarter a campaign that misses its goal gets nothing. Crowdfund Compass compares a plan with past campaigns before it goes live and says: Launch, Adjust or Coach first.</p>
<div class='cc-kpis'>
<div class='cc-kpi'><div class='n'>~{T['n_train'] / 1000:.0f},000</div><div class='t'>recent campaigns the model learned from (from 489,000 collected)</div></div>
<div class='cc-kpi'><div class='n'>about half</div><div class='t'>of all failures reached at 30% coach capacity in a re-weighted test on 2025 campaigns. About 95% of flagged campaigns failed. A new cohort may differ.</div></div>
<div class='cc-kpi'><div class='n'>2025–2026</div><div class='t'>tested on 39,500 campaigns launched after the ones it learned from</div></div>
</div></div>""", unsafe_allow_html=True)
    cols = st.columns(3)
    for col, (h, t) in zip(cols, [("One verdict per plan", "Launch, Adjust or Coach first, with the one change that is linked to the biggest gain."),
                                  ("Honest about uncertainty", "Chances are shown as a range. Kickstarter hides most failed campaigns, so no tool can know the exact level."),
                                  ("Made for coaches", "Upload a whole cohort and get it ranked from riskiest to safest, matched to the hours you have.")]):
        col.markdown(f"<div class='cc-card cc-fade'><div class='cc-h'>{h}</div><span class='cc-note'>{t}</span></div>", unsafe_allow_html=True)
    st.markdown("<span class='cc-note'>Patterns in past campaigns, not promises. Funding is a market test, not proof that a company will survive. "
                "HSG · Business Analytics & Data Science Applications · Group 11 · Kleymenov, Arcauz, Braun</span>", unsafe_allow_html=True)


#### Check-up
#########################################################

if page == "Check-up":
    left, right = st.columns([5, 6], gap="large")
    with left:
        st.markdown("<a class='cc-jump' href='#result'>See my result ↓</a>", unsafe_allow_html=True)
        c = campaign_inputs()
        st.markdown("<a class='cc-jump' href='#result'>See my result ↓</a>", unsafe_allow_html=True)
    r = check(c)
    colour = ui.VERDICT[r["verdict"]]
    explain = {"Launch": "Ready as planned. No single change stands out.", "Adjust": "Worth changing one thing before launch.",
               "Coach first": "Among the riskiest plans. Talk it through with a coach before launching."}[r["verdict"]]
    with right:
        st.markdown(f"<div id='result' style='scroll-margin-top:1rem'></div><div class='cc-card cc-fade'><div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem'>"
                    f"<span class='cc-eyebrow'>{ui.tip('Chance of reaching the goal', TIP_CHANCE)}</span>{ui.badge(r['verdict'])}</div>"
                    f"{ui.range_bar(r['low'] * 100, r['mid'] * 100, r['high'] * 100, colour, r['low_is_official'])}"
                    f"<p style='text-align:center;margin:.5rem 0 0 0'>{explain}</p></div>", unsafe_allow_html=True)
        if r["fixes"]:
            f = r["fixes"][0]
            st.markdown(f"<div class='cc-next cc-fade'><span class='cc-eyebrow'>Best next step</span><div class='big'>{f['change']}</div>"
                        f"<div class='sub'>Campaigns that did this were funded more often: middle estimate {f['mid_before']:.0f}% → {f['mid']:.0f}% "
                        f"(about +{round(f['mid']) - round(f['mid_before'])} points).</div></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='cc-card cc-fade'><span class='cc-eyebrow'>Best next step</span><div class='cc-h'>No single change stands out</div>"
                        "<span class='cc-note'>Changing the goal, length, launch day, video, pre-launch page, preparation time, title or blurb is not linked to 2 more points.</span></div>",
                        unsafe_allow_html=True)
        def weak_note(area):
            """One line under a weak bar when no single change in that area helps much."""
            if float(r["areas"][area]) > 25: return ""
            g = r["area_best"].get(area, 0)
            if g < 2: return "Weak, but no single change here is linked to 2 more points. It is the overall set-up, not one setting."
            if g < 8: return f"Weak, yet the best single change here adds only about {g:.0f} points: within the limits you set, the plan stays far from what is typical."
            return ""
        bars = "".join(ui.bar(a, sub, float(r["areas"][a]), weak_note(a)) for a, sub in LEVERS.items())
        tip_levers = "Each bar compares one part of your plan with recent campaigns. 50 = typical. Green = strong, amber = to improve, red = weak."
        st.markdown(f"<div class='cc-card cc-fade'><span class='cc-eyebrow'>{ui.tip('What you can change', tip_levers)}</span>"
                    f"<div style='margin-top:.7rem'>{bars}</div></div>", unsafe_allow_html=True)
        st.caption(f"{TIP_CHANCE} {FOUNDER_CONTROL}.")
        if len(r["fixes"]) > 1:
            cards = "".join(f"<div class='cc-mini'><b>{f['change']}</b><br><span class='cc-note'>middle estimate</span> "
                            f"<span class='cc-arrow'>{f['mid_before']:.0f}% → {f['mid']:.0f}%</span></div>" for f in r["fixes"][1:])
            st.markdown(f"<span class='cc-eyebrow'>Other changes</span><div class='cc-grid' style='margin:.5rem 0 .9rem 0'>{cards}</div>", unsafe_allow_html=True)
        if any(f["lever"] in ("Pre-launch page", "Preparation") for f in r["fixes"]):
            st.markdown("<p class='cc-note'>A pre-launch page and more preparation time stand for groundwork: building an audience before launch. "
                        "Opening a page the day before launch will not add these points.</p>", unsafe_allow_html=True)
        founder = ("<b>First campaign.</b> No track record yet, so preparation matters more." if c["prior_n"] == 0 else
                   f"<b>Track record:</b> {c['prior_funded']} of {c['prior_n']} earlier campaigns funded "
                   f"({ui.band(float(r['areas']['Founder']))[1]} compared with other creators).")
        market = float(r["areas"]["Market"])
        product = f"<b>Product type:</b> campaigns for this kind of product have done {'well' if market > 60 else 'about average' if market > 25 else 'poorly'} on Kickstarter."
        st.markdown(f"<span class='cc-eyebrow'>{ui.tip('Context', 'Things you cannot change before launch. They explain more than half of the result.')}</span>"
                    f"<div style='margin-top:.5rem'><span class='cc-chip'>{founder}</span><span class='cc-chip'>{product}</span></div>", unsafe_allow_html=True)
        if market <= 15:
            st.warning("**Note for coaches:** this type of product has rarely been funded on Kickstarter (typical examples: apps, software, web platforms, "
                       "restaurants, drinks). Changing the campaign set-up will not fix that. Consider whether Kickstarter is the right route.")
        with st.expander("Why this result?"):
            up = r["shap"][r["shap"] > 0.03].sort_values(ascending=False).head(4); down = r["shap"][r["shap"] < -0.03].head(4)
            a, b = st.columns(2)
            a.markdown("**Helps your chances**\n\n" + ("\n".join(f"- {LABELS.get(k, k).capitalize()}" for k in up.index) or "- Nothing stands out"))
            b.markdown("**Holds your chances back**\n\n" + ("\n".join(f"- {LABELS.get(k, k).capitalize()}" for k in down.index) or "- Nothing stands out"))
            steps, level = tree_path(r["X"].iloc[0])
            st.markdown("**In three steps:** " + " → ".join(steps) + f" → campaigns on this path had a **{level}** funding rate.")
            st.caption(f"Patterns in past campaigns, not causes. One change is tried at a time, never a goal below your minimum budget. "
                       f"Model quality on 2025 campaigns it had never seen: AUC {META['test']['auc_within_category_2025']:.2f} within category (0.5 = guessing, 1 = perfect).")


#### Goal optimizer
#########################################################

if page == "Goal optimizer":
    c = current_campaign()
    X = P.campaign_features(c, META, TEXT)
    goals = np.unique(np.round(np.geomspace(max(c["goal_usd"] * 0.2, 100), c["goal_usd"] * 3, 48), -1))
    V = pd.concat([X] * len(goals), ignore_index=True); d = np.log10(goals / c["goal_usd"])
    V["goal_usd"] = goals; V["log_goal_usd"] = np.log10(goals); V["goal_ratio"] = X.goal_ratio.iloc[0] + d; V["log_goal_per_day"] = X.log_goal_per_day.iloc[0] + d
    low, high = advisor.chances(V)
    curve = pd.DataFrame({"goal": goals, "low": low * 100, "high": high * 100, "mid": [middle(a, b) * 100 for a, b in zip(low, high)]})
    cut = META["verdict"]["reference_cut"] * 100
    ok = curve[(curve.goal >= c["min_budget_usd"]) & (curve.low >= cut)]
    here = curve.iloc[(curve.goal - c["goal_usd"]).abs().argmin()]
    rec = None if len(ok) == 0 else (here if ok.goal.max() >= c["goal_usd"] else ok.iloc[-1])
    x = alt.X("goal:Q", scale=alt.Scale(type="log", nice=False, domain=[float(goals.min()), float(goals.max())]), axis=alt.Axis(format="$~s", title="Funding goal (USD, log scale)"))
    tips = [alt.Tooltip("goal:Q", title="Goal", format="$,.0f"), alt.Tooltip("mid:Q", title="Middle estimate (%)", format=".0f"),
            alt.Tooltip("low:Q", title="Lower value (%)", format=".0f"), alt.Tooltip("high:Q", title="Upper value (%)", format=".0f")]
    base = alt.Chart(curve).encode(x=x)
    layers = [base.mark_area(color=ui.TEAL, opacity=0.16).encode(y=alt.Y("low:Q", title="Chance of reaching the goal (%)", scale=alt.Scale(domain=[0, 100])), y2="high:Q"),
              base.mark_line(color=ui.TEAL, strokeWidth=3).encode(y="mid:Q"),
              base.mark_circle(size=140, opacity=0).encode(y="mid:Q", tooltip=tips),
              alt.Chart(pd.DataFrame({"goal": [c["goal_usd"]], "t": ["your goal"]})).mark_rule(color=ui.NAVY, strokeWidth=1.5).encode(x="goal:Q"),
              alt.Chart(pd.DataFrame({"goal": [c["goal_usd"]], "y": [97], "t": ["your goal"]})).mark_text(align="left", dx=6, color=ui.NAVY, fontWeight=600).encode(x="goal:Q", y="y:Q", text="t:N")]
    if c["min_budget_usd"] > goals.min():
        layers += [alt.Chart(pd.DataFrame({"goal": [c["min_budget_usd"]]})).mark_rule(color=ui.AMBER, strokeDash=[4, 3]).encode(x="goal:Q"),
                   alt.Chart(pd.DataFrame({"goal": [c["min_budget_usd"]], "y": [90], "t": ["minimum budget"]})).mark_text(align="right", dx=-6, color=ui.AMBER, fontWeight=600).encode(x="goal:Q", y="y:Q", text="t:N")]
    if rec is not None:
        layers.append(alt.Chart(pd.DataFrame({"goal": [rec.goal], "mid": [rec.mid]})).mark_point(size=260, filled=True, color=ui.GREEN, stroke="#fff", strokeWidth=3, opacity=1).encode(x="goal:Q", y="mid:Q"))
    left, right = st.columns([7, 4], gap="large")
    with left:
        st.markdown("<div class='cc-h'>How the chance changes with the goal</div>", unsafe_allow_html=True)
        st.altair_chart(alt.layer(*layers).properties(height=380), width='stretch')
        st.markdown("<span class='cc-note'>Line = middle estimate. Shaded band = range. "
                    f"{RANGE_LABELS} Green dot = recommended goal. Pattern in past campaigns, not a cause.</span>", unsafe_allow_html=True)
    with right:
        if rec is None:
            st.markdown(f"<div class='cc-card'><span class='cc-eyebrow'>Recommended goal</span><div class='cc-h' style='color:{ui.RED}'>None covers your budget</div>"
                        "<span class='cc-note'>At any goal that covers your minimum budget, this plan stays in the riskiest group. The goal is not the main problem: look at the check-up.</span></div>", unsafe_allow_html=True)
        else:
            keep = rec.goal == here.goal
            atmin = curve.iloc[(curve.goal - c["min_budget_usd"]).abs().argmin()]
            why = (f" A lower goal would raise the chance a little ({atmin.mid:.0f}% at your minimum budget), but you would also ask for less money. "
                   f"The recommendation is the highest goal that stays out of the riskiest group, not the goal with the highest chance."
                   if keep and c["min_budget_usd"] < c["goal_usd"] * 0.98 else "")
            st.markdown(f"<div class='cc-next'><span class='cc-eyebrow'>Recommended goal</span><div class='big' style='font-size:1.7rem'>${(c['goal_usd'] if keep else rec.goal):,.0f}</div>"
                        f"<div class='sub'>{'Keep your goal: it is outside the riskiest group.' if keep else 'The highest goal that covers your minimum budget and stays out of the riskiest group.'} "
                        f"Middle estimate {rec.mid:.0f}% (between {rec.low:.0f}% and {rec.high:.0f}%).{why}</div></div>", unsafe_allow_html=True)
        rows = ""
        for label, g in [("Minimum budget", c["min_budget_usd"]), ("Your goal", c["goal_usd"]), ("Your goal + 50%", c["goal_usd"] * 1.5)]:
            row = curve.iloc[(curve.goal - g).abs().argmin()]
            rows += (f"<div style='display:flex;justify-content:space-between;padding:.55rem 0;border-bottom:1px solid {ui.LINE}'><span><b>{label}</b><br>"
                     f"<span class='cc-note'>${g:,.0f}</span></span><span style='text-align:right'><b>{row.mid:.0f}%</b><br><span class='cc-note'>{row.low:.0f}–{row.high:.0f}%</span></span></div>")
        st.markdown(f"<div class='cc-card'><span class='cc-eyebrow'>{ui.tip('Chance at three goals', TIP_CHANCE)}</span>{rows}</div>", unsafe_allow_html=True)


#### Coach view
#########################################################

COHORT_COLUMNS = ["title", "blurb", "main_category", "category", "country", "goal_usd", "min_budget_usd", "duration_days", "launch_date",
                  "prep_days", "has_video", "prelaunch_page", "earlier_campaigns", "earlier_funded", "days_since_last"]
EXAMPLE_COHORT = pd.DataFrame([
    ["Alpine Trails: A Cooperative Hiking Board Game for 1–4 Players", "Plan your route, share your supplies and reach the summit together before the weather turns.", "Games", "Tabletop Games", "Switzerland", 15000, 9000, 30, "2027-01-15", 30, 1, 0, 0, 0, 180],   # same as the check-up example
    ["BudgetBuddy: the AI app that manages your money", "A mobile application platform empowering students to track spending.", "Technology", "Apps", "Switzerland", 60000, 40000, 45, "2027-02-10", 3, 0, 0, 0, 0, 0],
    ["Night Harbor #4: A 32-Page Noir Fantasy Comic", "Issue 4 of the indie graphic novel series. Variant covers and enamel pins.", "Comics", "Comic Books", "Germany", 3000, 2000, 21, "2027-02-16", 60, 1, 1, 4, 4, 200],
    ["Zürich Rooftop Honey", "Small batch honey from city bees, delivered to your door.", "Food", "Small Batch", "Switzerland", 8000, 5000, 30, "2027-03-01", 10, 1, 0, 0, 0, 0],
    ["The Lantern Keeper: An Illustrated Children's Book", "A hardcover picture book about a girl who lights the mountain paths.", "Publishing", "Children's Books", "Austria", 6000, 4000, 30, "2027-02-23", 45, 1, 1, 1, 1, 400],
    ["Docu: Voices of the Rhine", "A feature documentary about the people living along the river.", "Film & Video", "Documentary", "Switzerland", 25000, 15000, 40, "2027-03-09", 20, 1, 0, 1, 0, 700],
], columns=COHORT_COLUMNS)

@st.cache_data(show_spinner="Scoring the cohort…")
def score_cohort(df):
    """Match the uploaded columns to the expected ones and score every campaign (cached per file)."""
    df = df.rename(columns={col: col.strip().lower().replace(" ", "_") for col in df.columns})
    missing = [col for col in COHORT_COLUMNS if col not in df.columns]
    if missing:
        return None, f"These columns are missing: {', '.join(missing)}. Download the template to see the expected format."
    rows, problems = [], []
    lookup = {(r.parent.lower(), r["name"].lower()): r.cat_id for _, r in CATS.iterrows()}
    for i, x in df.iterrows():
        try:
            cat_id = lookup[(str(x.main_category).strip().lower(), str(x.category).strip().lower())]
            c = {"cat_id": cat_id, "country": COUNTRY_CODES.get(str(x.country).strip().lower(), str(x.country).strip().upper()), "name": str(x.title),
                 "blurb": "" if pd.isna(x.blurb) else str(x.blurb), "goal_usd": float(x.goal_usd), "min_budget_usd": float(min(x.min_budget_usd, x.goal_usd)),
                 "duration_days": float(x.duration_days), "launch_date": pd.Timestamp(x.launch_date), "prep_days": float(x.prep_days), "has_video": int(x.has_video),
                 "prelaunch": int(x.prelaunch_page), "prior_n": int(x.earlier_campaigns), "prior_funded": int(min(x.earlier_funded, x.earlier_campaigns)),
                 "days_since_last": float(x.days_since_last)}
            r = check(c)
            rows.append({"Campaign": c["name"], "Middle estimate (%)": round(r["mid"] * 100), "Chance (low)": round(r["low"] * 100),
                         "Chance (high)": round(r["high"] * 100), "Weakest area": min(LEVERS, key=lambda a: r["areas"][a]),
                         "Top fix": r["fixes"][0]["change"] if r["fixes"] else "No single change stands out",
                         "Gain (points)": round(r["fixes"][0]["gain"]) if r["fixes"] else 0, "Assessment": r["verdict"],
                         "Product type rarely funded": "yes" if r["areas"]["Market"] <= 15 else "", "_low": r["low"]})
        except KeyError:
            problems.append(f"Row {i + 1}: category '{x.main_category} / {x.category}' not found")
        except Exception as e:
            problems.append(f"Row {i + 1}: could not be read ({type(e).__name__})")
    if not rows:
        return None, "No row could be scored. " + "; ".join(problems[:5])
    return pd.DataFrame(rows).sort_values("_low").reset_index(drop=True), "; ".join(problems)

if page == "Coach view":
    st.markdown("<div class='cc-h' style='font-size:1.3rem'>Triage a whole cohort</div><span class='cc-note'>Upload one row per planned campaign. "
                "The cohort is ranked from riskiest to safest. The ranking is the reliable part; the chances are a rough range.</span>", unsafe_allow_html=True)
    a, b = st.columns([3, 2], gap="large")
    uploaded = a.file_uploader("Cohort file (CSV)", type="csv")
    capacity = b.slider("Share of the cohort you can coach (%)", 10, 60, int(META["verdict"]["default_capacity"] * 100), step=5,
                        help="Sets how many campaigns are marked 'Coach first'.") / 100
    b.download_button("Download the CSV template", EXAMPLE_COHORT.to_csv(index=False).encode("utf-8"), file_name="cohort_template.csv")
    data = pd.read_csv(uploaded) if uploaded is not None else EXAMPLE_COHORT
    if uploaded is None:
        st.caption("No file yet: showing the example cohort of 6 campaigns.")
    scored, message = score_cohort(data)
    if scored is None:
        st.error(message)
    else:
        if message: st.warning(message)
        out = scored.copy()
        n_coach = int(round(len(out) * capacity))      # coaching slots: the riskiest teams by rank, up to the coach's capacity
        out.insert(0, "Risk rank", out.index + 1); out = out.drop(columns="_low")
        out["Coaching slot"] = np.where(out.index < n_coach, "yes", "")      # the assessment of each campaign does not depend on the slider
        out["Verdict"] = out.pop("Assessment")
        counts = out["Verdict"].value_counts()
        summary = " ".join(f"<span>{ui.badge(v)} {counts.get(v, 0)}</span>" for v in ("Coach first", "Adjust", "Launch"))
        st.markdown(f"<div class='cc-counts'>{summary}<span class='cc-note'>· coaching slots: {n_coach} of {len(out)}</span></div>", unsafe_allow_html=True)
        st.caption("The verdict of each campaign is the same as in its check-up and does not change with the slider. The slider only decides "
                   "how many of the riskiest teams get a coaching slot (above the line). " + RANGE_LABELS)
        cutoff = f"<div class='cc-cutoff'>Coach capacity: {n_coach} {'team' if n_coach == 1 else 'teams'} · the teams above this line get a coaching slot</div>"
        if n_coach == 0:
            st.markdown(cutoff, unsafe_allow_html=True)
        for _, row in out.iterrows():
            rank = row["Risk rank"]
            st.markdown(
                f"<div class='cc-queue-row'><b>#{rank}</b><strong>{escape(row['Campaign'])}</strong>"
                f"{ui.badge(row['Verdict'])}<span>{row['Chance (low)']}–{row['Chance (high)']}%</span>"
                f"<span class='cc-queue-fix'>{escape(row['Top fix'])}</span></div>",
                unsafe_allow_html=True,
            )
            with st.expander(f"#{rank} · Full details"):
                st.table(row.to_frame(name="Campaign").rename_axis(" ").astype(str))
            if rank == n_coach:
                st.markdown(cutoff, unsafe_allow_html=True)
        with st.expander("Full table and download", expanded=False):
            tint = {v: ui.SOFT[c] for v, c in ui.VERDICT.items()}
            st.dataframe(out.style.apply(lambda row: [f"background-color: {tint[row.Verdict]}" if col == "Verdict" else "" for col in out.columns], axis=1),
                         hide_index=True, width='stretch')
            st.download_button("Download the result as CSV", out.to_csv(index=False).encode("utf-8"), file_name="cohort_result.csv")
        st.caption(COACH_TEST)


#### Similar campaigns (nearest neighbours)
#########################################################

if page == "Similar campaigns":
    c = current_campaign()
    same_country = st.toggle("Only campaigns from the same country", False)
    X = P.campaign_features(c, META, TEXT).iloc[0]
    S = similar_table(); sm = META["similar"]
    pool = S[S.parent_category == X.parent_category]
    if same_country:
        if (pool.country == c["country"]).sum() >= 20:
            pool = pool[pool.country == c["country"]]
        else:
            st.info(f"Fewer than 20 past {X.parent_category} campaigns from {COUNTRY_NAMES[c['country']]} in our data, so all countries are shown.")
    mine = {"log_goal_usd": X.log_goal_usd, "duration_days": X.duration_days, "log_prep_days": X.log_prep_days, "log_prior": np.log10(X.creator_prior_n + 1),
            "prelaunch_activated": X.prelaunch_activated, "has_video": X.has_video, "text_score": X.text_score, "first_timer": X.first_timer}
    dist = sum(((pool[f].values - mine[f]) / sm["std"][f]) ** 2 for f in sm["features"])      # distance on standardised values
    near = pool.iloc[np.argsort(dist)[:10]]
    funded = int(near.success.sum()); names = CATS.set_index("cat_id").name
    tip_sim = "Similar = same main category and closest on goal, length, preparation time, creator experience, video, pre-launch page and type of product."
    st.markdown(f"<div class='cc-card cc-fade'><span class='cc-eyebrow'>{ui.tip('Most similar past campaigns', tip_sim)}</span>"
                f"<div style='font-size:2rem;font-weight:800;color:{ui.INK};margin:.2rem 0'>{funded} of 10 were funded</div>"
                f"<span class='cc-note'>Our data misses many failed campaigns, so this count is on the optimistic side.</span></div>", unsafe_allow_html=True)
    cards = ""
    for _, r in near.iterrows():
        colr = ui.GREEN if r.success == 1 else ui.RED
        cards += (f"<div class='cc-mini cc-fade'><span class='cc-badge' style='background:{ui.SOFT[colr]};color:{colr};font-size:.75rem;padding:.15rem .6rem'>"
                  f"{'Funded' if r.success == 1 else 'Not funded'}</span><div style='font-weight:600;margin:.45rem 0 .25rem 0;line-height:1.3'>{r['name']}</div>"
                  f"<span class='cc-note'>{names.get(r.cat_id, '')} · {COUNTRY_NAMES.get(str(r.country), '')} · {int(r.launch_year)}<br>Goal ${r.goal_usd:,.0f}</span><br>"
                  f"<a href='https://www.kickstarter.com/discover/advanced?term={P.quote(r['name'])}' target='_blank'>Search on Kickstarter ↗</a></div>")
    st.markdown(f"<div class='cc-grid'>{cards}</div>", unsafe_allow_html=True)
    st.markdown(f"<p class='cc-note' style='margin-top:.9rem'>Drawn from {sm['n']:,} campaigns launched from 2023 to June 2026. Source: public Kickstarter listings "
                f"collected by Web Robots (webrobots.io/kickstarter-datasets). No creator names are stored.</p>", unsafe_allow_html=True)


#### Benchmarks
#########################################################

if page == "Benchmarks":
    parents = sorted(META["official_rate"])
    default_parent = st.session_state.get("campaign", DEFAULT)["parent"]
    parent = st.selectbox("Main category", parents, index=parents.index(default_parent))
    rate = META["official_rate"][parent]
    a, b = st.columns([2, 5], gap="large")
    a.markdown(f"<div class='cc-card cc-fade'><span class='cc-eyebrow'>{ui.tip('Official funding rate', 'Share of all campaigns ever launched in this category that reached their goal. Source: Kickstarter.')}</span>"
               f"<div style='font-size:2.6rem;font-weight:800;color:{ui.INK}'>{rate * 100:.0f}%</div><span class='cc-note'>of all {META['official_launched'][parent]:,} {parent} "
               f"campaigns ever launched on Kickstarter. All categories: 43%. All-time average; recent rates are higher.</span></div>", unsafe_allow_html=True)
    off = pd.DataFrame({"Category": parents, "rate": [META["official_rate"][p] * 100 for p in parents]}); off["picked"] = off.Category == parent
    chart = alt.Chart(off).mark_bar(cornerRadiusEnd=5, height=16).encode(
        x=alt.X("rate:Q", title="Official funding rate, all time (%)", scale=alt.Scale(domain=[0, 80])), y=alt.Y("Category:N", sort="-x", title=None),
        color=alt.condition(alt.datum.picked, alt.value(ui.TEAL), alt.value("#CBD3DC")), tooltip=["Category", alt.Tooltip("rate:Q", title="Funded (%)", format=".0f")])
    b.altair_chart(chart.properties(height=360), width='stretch')
    st.markdown(f"<div class='cc-h'>What funded {parent} campaigns look like</div><span class='cc-note'>From funded campaigns in our data, launched from 2023 to June 2026. "
                "We hold about 85% of all funded campaigns, so these figures describe funded campaigns fairly well, though coverage differs by year and category. Funding rates from our data are not shown: it misses too many failed campaigns.</span>",
                unsafe_allow_html=True)
    B = META["benchmarks"]; rows = [("All " + parent, B["parent"][parent])]
    for _, r in CATS[CATS.parent == parent].iterrows():
        if str(r.cat_id) in B["category"]: rows.append((r["name"], B["category"][str(r.cat_id)]))
    table = pd.DataFrame([{"Category": n, "Funded campaigns": p["n"], "Typical goal (USD)": round(p["median_goal"]), "Typical amount raised (USD)": round(p["median_raised"]),
                           "Typical length (days)": round(p["median_days"]), "With pre-launch page (%)": round(p["prelaunch"] * 100),
                           "With video (%)": round(p["video"] * 100), "First-time creators (%)": round(p["first_timer"] * 100)} for n, p in rows])
    st.dataframe(table, hide_index=True, width='stretch',
                 column_config={"Typical goal (USD)": st.column_config.NumberColumn(format="$%d"), "Typical amount raised (USD)": st.column_config.NumberColumn(format="$%d"),
                                "With pre-launch page (%)": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100),
                                "With video (%)": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)})
    st.markdown("<span class='cc-note'>'Typical' = median. Many funded campaigns set a low goal on purpose and raise several times that amount. "
                "Sources: Kickstarter stats page (last updated 1 January 2026); public Kickstarter listings collected by Web Robots.</span>", unsafe_allow_html=True)


#### How it works
#########################################################

if page == "How it works":
    T = META["test"]
    st.markdown("<div class='cc-h' style='font-size:1.3rem'>From public listings to one verdict</div>", unsafe_allow_html=True)
    st.markdown(f"""<div class='cc-pipe cc-fade'>
<div class='box'><span class='cc-eyebrow'>1 · Data</span><b>489,000 campaigns collected</b><span class='cc-note'>Public Kickstarter listings, 24 snapshots from 2016 to 2026 (Web Robots). 430,000 have a final outcome.</span></div>
<div class='box'><span class='cc-eyebrow'>2 · Inputs</span><b>32 things known before launch</b><span class='cc-note'>Goal, timing, title and blurb, track record, video and pre-launch page, type of product.</span></div>
<div class='box'><span class='cc-eyebrow'>3 · Model</span><b>XGBoost, tested on the future</b><span class='cc-note'>Learned from about 44,000 campaigns of 2023–2024, tested on 39,500 launched in 2025 and January–June 2026.</span></div>
<div class='box'><span class='cc-eyebrow'>4 · Advice</span><b>Verdict, range, next step</b><span class='cc-note'>A verdict per plan, the chance as a range, one change at a time, coaching slots by rank.</span></div></div>""", unsafe_allow_html=True)
    a, b = st.columns(2, gap="large")
    with a:
        tip_auc = "Take one funded and one failed campaign from the same category: how often does the model give the funded one the higher score? 0.5 = guessing, 1 = perfect."
        def acc(label, value, colour):
            return (f"<div style='margin:.7rem 0'><div style='display:flex;justify-content:space-between'><b>{label}</b><b>{value:.2f}</b></div>"
                    f"<div class='cc-bar'><div class='cc-fill' style='width:{(value - 0.5) / 0.5 * 100:.0f}%;background:{colour}'></div></div></div>")
        st.markdown(f"<div class='cc-card'><span class='cc-eyebrow'>{ui.tip('More inputs, better ranking', tip_auc)}</span>"
                    f"{acc('6 inputs of a typical public dataset', 0.75, '#CBD3DC')}{acc('Our 32 inputs', T['auc_within_category_2025'], ui.TEAL)}"
                    f"<span class='cc-note'>Bars run from 0.5 (guessing) to 1 (perfect). Campaigns launched in 2025, which the model had never seen. "
                    f"January–June 2026: {T['auc_within_category_2026h1']:.2f}. Accuracy {T['accuracy_2025'] * 100:.0f}% against 71% for always saying \"funded\".</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='cc-card'><span class='cc-eyebrow'>The verdict rule</span><p style='margin:.5rem 0'>{ui.badge('Coach first')} lower value below {META['verdict']['reference_cut'] * 100:.1f}%: "
                    f"among the riskiest plans</p><p style='margin:.5rem 0'>{ui.badge('Adjust')} one change is linked to at least "
                    f"{META['verdict']['adjust_gain']:.0f} more points</p><p style='margin:.5rem 0'>{ui.badge('Launch')} everything else</p><span class='cc-note'>In Coach view, coaching slots go to the riskiest teams by rank, up to the coach's capacity "
                    f"(default {META['verdict']['default_capacity'] * 100:.0f}%, adjustable). The slots do not change any verdict.</span></div>", unsafe_allow_html=True)
    with b:
        cal = pd.concat([pd.DataFrame(META["calibration"]["before"], columns=["x", "y"]).assign(s="before correction"),
                         pd.DataFrame(META["calibration"]["after"], columns=["x", "y"]).assign(s="after correction")])
        diag = alt.Chart(pd.DataFrame({"x": [0, 100], "y": [0, 100]})).mark_line(color="#B6C0CC", strokeDash=[4, 3]).encode(x="x:Q", y="y:Q")
        lines = alt.Chart(cal).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("x:Q", title="Predicted chance (%)", scale=alt.Scale(domain=[0, 100])), y=alt.Y("y:Q", title="Actually funded (%)", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("s:N", scale=alt.Scale(domain=["after correction", "before correction"], range=[ui.TEAL, "#B6C0CC"]), legend=alt.Legend(title=None, orient="top-left")),
            tooltip=[alt.Tooltip("s:N", title=" "), alt.Tooltip("x:Q", title="Predicted (%)", format=".0f"), alt.Tooltip("y:Q", title="Funded (%)", format=".0f")])
        st.markdown("<span class='cc-eyebrow'>When we say 70%, is it 70%?</span>", unsafe_allow_html=True)
        st.altair_chart((diag + lines).properties(height=300), width='stretch')
        st.markdown("<span class='cc-note'>In our data, after correction, predictions are within 5 points of what happened in 2025 (dashed line = perfect). "
                    "Real Kickstarter rates are lower than in our data, which is why the app shows a range.</span>", unsafe_allow_html=True)
    st.markdown("<div class='cc-h' style='margin-top:.6rem'>Limits you should know</div>", unsafe_allow_html=True)
    limits = [("Our data misses many failed campaigns", "We hold about 85% of all funded campaigns but about 42% of the failed ones, because Kickstarter's listings hide most campaigns that failed. That is why chances are a range."),
              ("Ranking beats level", "The model is good at telling stronger plans from weaker ones. The exact percentage is rough. 'Middle estimate' was checked on one public figure: 80% official for tabletop games in 2024, 78% here."),
              ("Patterns, not causes", "'Campaigns with a pre-launch page were funded more often' does not mean a page causes funding."),
              (FOUNDER_CONTROL, "In the model's explanation, what is being made and the creator's track record explain 57% of the result; goal, timing, presentation and pitch explain 43%."),
              ("A market test, not a verdict on the company", "Funding shows that backers want the product now. It does not prove the company will survive."),
              ("Data up to November 2026", "Kickstarter changes. The model should be retrained with new listings.")]
    st.markdown("<div class='cc-grid'>" + "".join(f"<div class='cc-mini'><b>{h}</b><br><span class='cc-note'>{t}</span></div>" for h, t in limits) + "</div><div style='height:.9rem'></div>", unsafe_allow_html=True)
    with st.expander("Methods: from class and beyond"):
        st.markdown("""
| Step | Method | From class? |
|---|---|---|
| Prediction | XGBoost, compared with logistic regression, decision tree, random forest | Class |
| Tuning and testing | Grid search, time-ordered cross-validation, confusion matrix, precision, recall, F1, ROC-AUC | Class |
| Title and blurb | TF-IDF text mining | Class |
| Explanation path | Decision tree, depth 3 | Class |
| Product-type score | Text model fed into the main model (stacking) | Beyond class |
| Goal rule | The model may only learn that a higher goal lowers the chance | Beyond class |
| Chance range | Calibration (Platt scaling) and adjustment to official rates | Beyond class |
| Area bars and "why" | SHAP values | Beyond class |
| What to change | One-change-at-a-time comparison | Beyond class |
| Similar campaigns | Nearest neighbours | Beyond class |
""")
    st.markdown("<p class='cc-note'>AI use: code and analysis were developed with Claude (Anthropic, model Fable 5.2) in November 2026 and reviewed by the team. "
                "Official rates: Kickstarter stats page, last updated 1 January 2026. Data: Web Robots (webrobots.io/kickstarter-datasets).</p>", unsafe_allow_html=True)
