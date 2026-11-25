"""ui.py — Crowdfund Compass: the visual layer (styles and small HTML components).
Nothing here computes a number. It only decides how numbers from the model are shown."""
from html import escape
import altair as alt

NAVY, TEAL, TEAL_SOFT, INK, MUTED, LINE, BG = "#0B1F33", "#0F6E56", "#E7F4EF", "#0B1F33", "#5B6B7C", "#E4E8EE", "#F7F8FA"
GREEN, AMBER, RED = "#15803D", "#B45309", "#B91C1C"                  # strong / to improve / weak (colour only with meaning)
SOFT = {GREEN: "#E8F5EC", AMBER: "#FDF1DC", RED: "#FCE9E7"}
VERDICT = {"Launch": GREEN, "Adjust": AMBER, "Coach first": RED}

LOGO = ("<svg width='{s}' height='{s}' viewBox='0 0 64 64' aria-hidden='true'><circle cx='32' cy='32' r='30' fill='#0B1F33'/>"
        "<circle cx='32' cy='32' r='23' fill='none' stroke='#fff' stroke-opacity='.3' stroke-width='2'/>"
        "<polygon points='48,16 27,27 37,37' fill='#3FCFA4'/><polygon points='16,48 27,27 37,37' fill='#fff'/></svg>")

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, .stApp, .stApp p, .stApp div, .stApp label, .stApp li, .stApp a, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp td, .stApp th,
.stApp span:not([data-testid="stIconMaterial"]):not([class*="material"]), button, input, textarea, select {{font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif !important;}}
.stApp {{background: {BG};}}
.block-container {{padding-top: 1.4rem; padding-bottom: 4rem; max-width: 1180px;}}
#MainMenu, footer, header[data-testid="stHeader"] {{visibility: hidden; height: 0;}}
h1, h2, h3, h4 {{color: {INK}; letter-spacing: -0.02em;}}
.cc-top {{display: flex; align-items: center; gap: .7rem; margin-bottom: .6rem;}}
.cc-brand {{font-weight: 800; font-size: 1.15rem; color: {INK}; letter-spacing: -0.02em;}}
.cc-tag {{color: {MUTED}; font-size: .9rem; margin-left: .2rem;}}
.cc-card {{background: #fff; border: 1px solid {LINE}; border-radius: 16px; padding: 1.15rem 1.3rem; margin-bottom: .9rem;
          box-shadow: 0 1px 2px rgba(11,31,51,.04); transition: box-shadow .2s ease, transform .2s ease;}}
.cc-card:hover {{box-shadow: 0 6px 20px rgba(11,31,51,.07);}}
.cc-fade {{animation: ccfade .45s ease both;}}
@keyframes ccfade {{from {{opacity: 0; transform: translateY(6px);}} to {{opacity: 1; transform: none;}}}}
.cc-eyebrow {{font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: {MUTED};}}
.cc-note {{color: {MUTED}; font-size: .86rem; line-height: 1.45;}}
.cc-h {{font-size: 1.05rem; font-weight: 700; color: {INK}; margin: .2rem 0 .5rem 0;}}
.cc-badge {{display: inline-flex; align-items: center; gap: .4rem; padding: .32rem .85rem; border-radius: 999px; font-weight: 700; font-size: .95rem;}}
.cc-dot {{width: .55rem; height: .55rem; border-radius: 50%; display: inline-block;}}
.cc-chip {{display: inline-block; background: #F1F4F8; color: {INK}; border-radius: 10px; padding: .55rem .8rem; font-size: .88rem; margin: 0 .5rem .5rem 0; line-height: 1.4;}}
.cc-step {{display: flex; align-items: center; gap: .6rem; margin: .1rem 0 .5rem 0;}}
.cc-num {{width: 1.6rem; height: 1.6rem; border-radius: 50%; background: {TEAL}; color: #fff; font-weight: 700; font-size: .85rem; display: inline-flex; align-items: center; justify-content: center;}}
.cc-step b {{font-size: 1rem; color: {INK};}}
.cc-bar {{background: #EEF1F5; border-radius: 99px; height: 10px; width: 100%; overflow: hidden; margin: .45rem 0 .3rem 0;}}
.cc-fill {{height: 10px; border-radius: 99px; animation: ccgrow .8s cubic-bezier(.2,.8,.2,1) both; transform-origin: left;}}
@keyframes ccdraw {{to {{stroke-dashoffset: 0;}}}}
@keyframes ccpop {{to {{opacity: 1;}}}}
@keyframes ccgrow {{from {{transform: scaleX(0);}} to {{transform: scaleX(1);}}}}
.cc-next {{background: linear-gradient(135deg, {TEAL} 0%, #0B5745 100%); color: #fff; border-radius: 16px; padding: 1.1rem 1.3rem; margin-bottom: .9rem;}}
.cc-next .cc-eyebrow {{color: rgba(255,255,255,.75);}}
.cc-next .big {{font-size: 1.12rem; font-weight: 700; margin: .25rem 0;}}
.cc-next .sub {{font-size: .88rem; color: rgba(255,255,255,.85);}}
.cc-arrow {{font-weight: 700; color: {INK};}}
.cc-hero {{background: radial-gradient(1200px 400px at 85% -10%, #14806A 0%, rgba(20,128,106,0) 60%), linear-gradient(135deg, #0B1F33 0%, #102C47 100%);
          border-radius: 22px; padding: 2.6rem 2.4rem 2.2rem 2.4rem; color: #fff; margin-bottom: 1.1rem;}}
.cc-hero h1 {{color: #fff; font-size: 2.35rem; line-height: 1.12; font-weight: 800; margin: .5rem 0 .7rem 0; max-width: 760px;}}
.cc-hero p {{color: rgba(255,255,255,.82); font-size: 1.05rem; max-width: 680px; margin: 0;}}
.cc-kpis {{display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1.7rem;}}
.cc-kpi {{background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14); border-radius: 14px; padding: 1rem 1.1rem;}}
.cc-kpi .n {{font-size: 1.7rem; font-weight: 800; letter-spacing: -0.02em;}}
.cc-kpi .t {{font-size: .86rem; color: rgba(255,255,255,.8); line-height: 1.4;}}
.cc-grid {{display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: .8rem;}}
.cc-mini {{background: #fff; border: 1px solid {LINE}; border-radius: 14px; padding: .9rem 1rem; transition: box-shadow .2s ease;}}
.cc-mini:hover {{box-shadow: 0 6px 20px rgba(11,31,51,.07);}}
.cc-mini a {{color: {TEAL}; text-decoration: none; font-weight: 600; font-size: .84rem;}}
.cc-pipe {{display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin: .4rem 0 1rem 0;}}
.cc-pipe .box {{background: #fff; border: 1px solid {LINE}; border-radius: 14px; padding: 1rem; position: relative;}}
.cc-pipe .box b {{display: block; color: {INK}; margin-bottom: .25rem;}}
.cc-pipe .box:not(:last-child)::after {{content: '→'; position: absolute; right: -.75rem; top: 42%; color: {TEAL}; font-weight: 800; z-index: 2;}}
.cc-range {{margin: .8rem .15rem;}}
.cc-scale, .cc-estimates, .cc-counts {{display:flex; justify-content:space-between; gap:.6rem; flex-wrap:wrap;}}
.cc-scale, .cc-estimates {{font-size:.83rem; color:{MUTED};}}
.cc-estimates b {{display:block; color:{INK}; font-size:1.1rem;}}
.cc-estimates small {{display:block; font-size:.74rem; color:{MUTED};}}
.cc-track {{position:relative; height:.65rem; margin-top:.35rem; border-radius:1rem; background:#E4E8EE;}}
.cc-track i {{position:absolute; inset-block:0; opacity:.48; border-radius:1rem;}}
.cc-track b {{position:absolute; top:-.25rem; bottom:-.25rem; width:3px; background:{NAVY}; transform:translateX(-50%);}}
.cc-counts {{justify-content:flex-start; gap:1rem;}}
.cc-cutoff {{border-top:2px solid {TEAL}; padding-top:.3rem; color:{TEAL}; font-weight:700;}}
.cc-queue-row {{display:grid; grid-template-columns:auto minmax(0,2fr) auto auto minmax(0,1.4fr); gap:.75rem;
 align-items:center; border:1px solid {LINE}; border-radius:12px; background:white; padding:.8rem 1rem; color:{INK}; overflow-wrap:anywhere;}}
.cc-queue-row .cc-badge {{justify-self:start; white-space:nowrap;}}
.cc-queue-fix {{font-size:.9rem;}}
[data-tip] {{position: relative; cursor: help; border-bottom: 1px dotted {MUTED};}}
[data-tip]:hover::after {{content: attr(data-tip); position: absolute; left: 0; bottom: 130%; background: {NAVY}; color: #fff; padding: .5rem .7rem; border-radius: 8px;
   font-size: .78rem; font-weight: 400; line-height: 1.4; width: 240px; z-index: 50; box-shadow: 0 8px 24px rgba(11,31,51,.25); white-space: normal; text-transform: none; letter-spacing: 0;}}
div[data-testid="stVerticalBlockBorderWrapper"] {{border-radius: 16px !important; background: #fff; border-color: {LINE} !important;}}
.stButton > button, .stDownloadButton > button {{border-radius: 10px; font-weight: 600; border: 1px solid {LINE}; transition: all .15s ease;}}
.stButton > button[kind="primary"] {{background: #3FCFA4; color: {NAVY}; border: none; padding: .6rem 1.3rem; font-size: 1rem;}}
.stButton > button[kind="primary"]:hover {{background: #5ADBB4; transform: translateY(-1px);}}
.cc-jump {{display: none;}}
@media (max-width: 760px) {{
  .cc-queue-row {{grid-template-columns:auto minmax(0,1fr) auto; gap:.45rem;}}
  .cc-queue-row > :nth-child(4) {{grid-column:2;}}
  .cc-queue-fix {{grid-column:2 / -1;}}
  .cc-jump {{display: block; text-align: center; background: {TEAL}; color: #fff !important; font-weight: 700; border-radius: 10px; padding: .7rem; margin: .2rem 0 .8rem 0; text-decoration: none;}}
  .cc-hero {{padding: 1.6rem 1.2rem;}} .cc-hero h1 {{font-size: 1.6rem;}} .cc-kpis, .cc-pipe {{grid-template-columns: 1fr;}}
  .cc-pipe .box:not(:last-child)::after {{content: '';}} .cc-tag {{display: none;}} [data-tip]:hover::after {{width: 180px;}}
}}
</style>
"""

def tip(text, explanation):
    """A word or number with a plain-language explanation on hover."""
    return f"<span data-tip=\"{escape(explanation, quote=True)}\">{text}</span>"

def header():
    return (f"<div class='cc-top'>{LOGO.format(s=34)}<span class='cc-brand'>Crowdfund Compass</span>"
            f"<span class='cc-tag'>Know before you launch.</span></div>")

def badge(verdict):
    c = VERDICT[verdict]
    return f"<span class='cc-badge' style='background:{SOFT[c]};color:{c}'><span class='cc-dot' style='background:{c}'></span>{verdict}</span>"

def band(score):
    return (RED, "weak") if score <= 25 else (AMBER, "to improve") if score <= 60 else (GREEN, "strong")

def range_bar(low, mid, high, colour, low_is_official=True):
    """Place each estimate on the same 0–100 percent scale. Each end is named by its source, whatever their order."""
    src_low, src_high = ("adjusted to official rates", "from our data") if low_is_official else ("from our data", "adjusted to official rates")
    return (f"<div class='cc-range' role='img' aria-label='Chance of reaching the goal: lower value {low:.0f}% ({src_low}), "
            f"middle estimate {mid:.0f}%, upper value {high:.0f}% ({src_high})'>"
            f"<div class='cc-scale'><span>0%</span><span>100%</span></div>"
            f"<div class='cc-track'><i style='left:{low}%;right:{100-high}%;background:{colour}'></i>"
            f"<b style='left:{mid}%'></b></div></div>"
            f"<div class='cc-estimates'><span>Lower value <b>{low:.0f}%</b><small>{src_low}</small></span>"
            f"<span style='text-align:center'>Middle estimate <b>{mid:.0f}%</b><small>halfway between</small></span>"
            f"<span style='text-align:right'>Upper value <b>{high:.0f}%</b><small>{src_high}</small></span></div>")

def bar(title, sub, score, note=""):
    c, word = band(score)
    note = f"<div class='cc-note' style='margin-top:.15rem'>{note}</div>" if note else ""
    return (f"<div style='margin-bottom:.55rem'><div style='display:flex;justify-content:space-between;align-items:baseline'>"
            f"<span><b>{title}</b> <span class='cc-note'>· {sub}</span></span>"
            f"<span style='color:{c};font-weight:700;font-size:.9rem'>{word} · {score:.0f}</span></div>"
            f"<div class='cc-bar'><div class='cc-fill' style='width:{max(score, 3):.0f}%;background:{c}'></div></div>{note}</div>")

def chart_theme():
    """One Altair style for every chart in the app."""
    def theme():
        return {"config": {"font": "Inter", "background": "transparent", "view": {"stroke": None},
                           "axis": {"labelColor": MUTED, "titleColor": MUTED, "gridColor": "#EEF1F5", "domainColor": LINE, "tickColor": LINE,
                                    "labelFontSize": 12, "titleFontSize": 12, "titleFontWeight": 500, "labelFont": "Inter", "titleFont": "Inter"},
                           "legend": {"labelColor": MUTED, "titleColor": MUTED, "labelFont": "Inter", "titleFont": "Inter"}}}
    try:
        alt.themes.register("compass", theme); alt.themes.enable("compass")
    except Exception:
        pass
