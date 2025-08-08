import streamlit as st
import math
import pandas as pd

# ===============================
# AMS Profit Levers Simulator
# Baseline: FY2025 (JUL'24–JUN'25) Outlook from June 2025 Board Pack
# Currency: AUD (thousands) — switch to THB using FX below
# ===============================

st.set_page_config(page_title="AMS Profit Levers Simulator", layout="wide")
st.title("AMS Profit Levers Simulator")

st.caption(
    "Baseline seeded from FY2025 Outlook in the June 2025 board report: "
    "External sales 8,658, Internal sales 8,245, Operating Profit −1,405, "
    "External gross margin ≈17% (roll-cost average)."
)

# --------- Baseline (AUD '000) from report ---------
BASELINE = {
    "external_sales": 8658.0,   # Non-ANCA, '000 AUD
    "internal_sales": 8245.0,   # ANCA, '000 AUD
    "external_margin_pct": 17.0,  # roll-cost margin average for external
    # Internal margin not explicitly stated; using conservative 10% placeholder
    "internal_margin_pct": 10.0,
    # Solve fixed costs so that OP ≈ -1,405 given margins above
    # GP = 8658*0.17 + 8245*0.10 ≈ 2,297 ; OP = GP - Fixed = -1,405 → Fixed ≈ 3,702
    "fixed_costs": 3702.0,      # SG&A + fixed OH, '000 AUD
    "operating_profit_outlook": -1405.0,
}

# --------- Sidebar Controls ---------
with st.sidebar:
    st.header("Global Settings")
    currency = st.selectbox("Display Currency", ["AUD '000", "THB '000"], index=0)
    fx_rate = st.number_input("FX Rate (THB per 1 AUD)", min_value=10.0, max_value=50.0, value=24.0, step=0.1,
                              help="Used only for display conversion")

    st.markdown("---")
    use_baseline = st.checkbox("Start from FY2025 baseline", value=True)
    st.caption("Uncheck to start from zeros or your last inputs.")

# Helper to convert units for display
mult = 1.0 if currency == "AUD '000" else fx_rate
unit = "AUD'000" if currency == "AUD '000" else "THB'000"

# --------- Inputs ---------
colA, colB, colC = st.columns([1,1,1])
with colA:
    st.subheader("Sales")
    ext_sales = st.number_input(
        f"External Sales ({unit}):",
        min_value=0.0,
        value=BASELINE["external_sales"] * mult if use_baseline else 0.0,
        step=100.0,
    )
    int_sales = st.number_input(
        f"Internal Sales ({unit}):",
        min_value=0.0,
        value=BASELINE["internal_sales"] * mult if use_baseline else 0.0,
        step=100.0,
    )

with colB:
    st.subheader("Margins & Efficiency")
    ext_margin = st.slider("External Gross Margin (%)", 0, 60, int(BASELINE["external_margin_pct"]) if use_baseline else 15)
    int_margin = st.slider("Internal Gross Margin (%)", 0, 40, int(BASELINE["internal_margin_pct"]) if use_baseline else 8)
    efficiency = st.slider(
        "Operational Efficiency Factor",
        0.80, 1.20, 1.00 if use_baseline else 1.00, 0.01,
        help=">1.00 improves margins; <1.00 worsens margins (proxy for utilisation/variance).",
    )

with colC:
    st.subheader("Overheads & One‑offs")
    fixed_costs = st.number_input(
        f"Fixed Costs ({unit}):",
        min_value=0.0,
        value=BASELINE["fixed_costs"] * mult if use_baseline else 0.0,
        step=50.0,
        help="SG&A + fixed factory overheads"
    )
    repairs = st.number_input(
        f"Extra Repairs & Maintenance this year ({unit})", min_value=0.0, value=0.0, step=10.0
    )
    fx_impact = st.number_input(
        f"FX / Exceptional items ({unit}):",
        value=0.0,
        step=10.0,
        help="Positive = gain; Negative = loss (e.g., remove +1,800 THB'000 prior FX gain).",
    )

# Convert inputs back to AUD'000 for calc if user is in THB mode
conv = 1.0 if unit.startswith("AUD") else (1.0 / fx_rate)
_ext_sales = ext_sales * conv
_int_sales = int_sales * conv
_fixed = fixed_costs * conv
_repairs_aud = repairs * conv
_fx_aud = fx_impact * conv

# --------- Calculations ---------
ext_gp = _ext_sales * (ext_margin / 100.0) * efficiency
int_gp = _int_sales * (int_margin / 100.0) * efficiency
total_gp = ext_gp + int_gp
op = total_gp - _fixed - _repairs_aud + _fx_aud

# Break-even external sales given other inputs (to hit OP = 0)
# 0 = (X * ext_margin% * efficiency) + int_gp - fixed - repairs + fx
# → X = (fixed + repairs - fx - int_gp) / (ext_margin% * efficiency)
if ext_margin > 0 and efficiency > 0:
    be_ext_sales = max(0.0, (_fixed + _repairs_aud - _fx_aud - int_gp) / ((ext_margin/100.0) * efficiency))
else:
    be_ext_sales = math.inf

# Target OP input & sales needed to hit target (optional target could be added later)

st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(f"External GP ({unit})", f"{ext_gp*mult:,.0f}")
with col2:
    st.metric(f"Total GP ({unit})", f"{total_gp*mult:,.0f}")
with col3:
    st.metric(f"Operating Profit ({unit})", f"{op*mult:,.0f}")
with col4:
    st.metric(f"Break‑even External Sales ({unit})", f"{be_ext_sales*mult:,.0f}")

st.markdown("---")

colL, colR = st.columns([1,1])
with colL:
    st.subheader("What moves the needle most?")
    st.write(
        """

        * Increase **External Sales** at a solid **margin** (17–20%+) before adding fixed costs.

        * Improve **Efficiency** to lift realised margin (reduce variance, overtime, rework, breakdowns).

        * Hold **Fixed Costs** flat while scaling to drive SG&A % down.

        * Avoid **one‑offs** (repairs spikes, FX losses) that erase gains.

        """

    )

with colR:
    st.subheader("Baseline (from report)")
    st.json(BASELINE)

st.info(
    "Tip: set Repairs to 700 (AUD'000) to simulate a folding breakdown month; set FX to −1,800 to remove last year's FX gain; "
    "nudge Efficiency to 0.95 to simulate variance/slippage."
)

# Simple sensitivity: OP over a range of external sales around current value
base = int(_ext_sales if _ext_sales > 0 else BASELINE["external_sales"])
step = max(100, int(base * 0.05))
sizes = list(range(int(base*0.6), int(base*1.6) + 1, step))
rows = []
for s in sizes:
    gp = s*(ext_margin/100.0)*efficiency + int_gp
    opp = gp - _fixed - _repairs_aud + _fx_aud
    rows.append({"External Sales (AUD'000)": s, "OP (AUD'000)": opp})
df = pd.DataFrame(rows)
st.line_chart(df.set_index("External Sales (AUD'000)"))

st.caption("This tool is a simplification: it treats efficiency as a margin multiplier and fixed costs as flat. Pair it with your monthly variance analysis.")
