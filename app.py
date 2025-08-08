import streamlit as st
import math
import pandas as pd

# ===============================
# AMS Profit Levers Simulator — v2
# Monthly model. Currency in AUD '000 by default (toggle to THB).
# Inputs:
#   • Monthly Internal & External Sales
#   • Product cost %% of sales (defaults: Internal 50%%, External 80%%)
#   • Operational Efficiency 30%% → 80%% (default 51%%, current baseline)
#   • Monthly Fixed Costs, Repairs, FX/Exceptionals
# Notes:
#   • Realised margin = (1 - product_cost_pct) * efficiency
#   • OP (monthly) = GP - Fixed - Repairs + FX
#   • "Reset" returns to baselines derived from FY2025 board pack
# ===============================

st.set_page_config(page_title="AMS Profit Levers Simulator (Monthly)", layout="wide")
st.title("AMS Profit Levers Simulator (Monthly)")

# --------- Baseline from FY2025 board pack (AUD '000) ---------
# Annual: External 8,658 ; Internal 8,245 ; Fixed ~3,702 ; OP ≈ -1,405
# Convert to monthly averages for baseline:
BASELINE_ANNUAL = {
    "external_sales": 8658.0,
    "internal_sales": 8245.0,
    "fixed_costs": 3702.0,
}
BASELINE_MONTHLY = {
    "external_sales": BASELINE_ANNUAL["external_sales"] / 12.0,   # ≈ 721.5
    "internal_sales": BASELINE_ANNUAL["internal_sales"] / 12.0,   # ≈ 687.1
    "fixed_costs":    BASELINE_ANNUAL["fixed_costs"] / 12.0,      # ≈ 308.5
    "efficiency": 0.51,  # 51% baseline
    "ext_cost_pct": 0.80, # external product cost % of sales (80%)
    "int_cost_pct": 0.50, # internal product cost % of sales (50%)
    "repairs": 0.0,
    "fx": 0.0,
}

# Session state init / reset
def reset_to_baseline():
    st.session_state.currency = "AUD '000"
    st.session_state.fx_rate = 24.0
    st.session_state.ext_sales_m = BASELINE_MONTHLY["external_sales"]
    st.session_state.int_sales_m = BASELINE_MONTHLY["internal_sales"]
    st.session_state.ext_cost_pct = BASELINE_MONTHLY["ext_cost_pct"]
    st.session_state.int_cost_pct = BASELINE_MONTHLY["int_cost_pct"]
    st.session_state.efficiency = BASELINE_MONTHLY["efficiency"]
    st.session_state.fixed_m = BASELINE_MONTHLY["fixed_costs"]
    st.session_state.repairs_m = BASELINE_MONTHLY["repairs"]
    st.session_state.fx_m = BASELINE_MONTHLY["fx"]

if "ext_sales_m" not in st.session_state:
    reset_to_baseline()

# --------- Sidebar: Global Settings & Reset ---------
with st.sidebar:
    st.header("Global Settings")
    currency = st.selectbox("Display Currency", ["AUD '000", "THB '000"], index=0, key="currency")
    fx_rate = st.number_input("FX Rate (THB per 1 AUD)", min_value=10.0, max_value=50.0, value=st.session_state.fx_rate, step=0.1, key="fx_rate")
    if st.button("🔄 Reset to current baseline (51% efficiency, monthly averages)"):
        reset_to_baseline()
        st.experimental_rerun()

mult = 1.0 if st.session_state.currency == "AUD '000" else st.session_state.fx_rate
unit = "AUD'000" if st.session_state.currency == "AUD '000" else "THB'000"
conv = 1.0 if unit.startswith("AUD") else (1.0 / st.session_state.fx_rate)

# --------- Inputs (Monthly) ---------
colA, colB, colC = st.columns([1,1,1])

with colA:
    st.subheader("Monthly Sales")
    ext_sales = st.number_input(
        f"External Sales per month ({unit})",
        min_value=0.0,
        value=st.session_state.ext_sales_m * mult,
        step=50.0,
        key="ext_sales_m_input"
    )
    int_sales = st.number_input(
        f"Internal Sales per month ({unit})",
        min_value=0.0,
        value=st.session_state.int_sales_m * mult,
        step=50.0,
        key="int_sales_m_input"
    )

with colB:
    st.subheader("Product Cost % of Sales")
    ext_cost_pct = st.slider(
        "External Product Cost (% of sales)", 0, 100, int(st.session_state.ext_cost_pct * 100), key="ext_cost_pct_input",
        help="Default 80% for external"
    ) / 100.0
    int_cost_pct = st.slider(
        "Internal Product Cost (% of sales)", 0, 100, int(st.session_state.int_cost_pct * 100), key="int_cost_pct_input",
        help="Default 50% for internal"
    ) / 100.0

with colC:
    st.subheader("Efficiency & Overheads (Monthly)")
    efficiency = st.slider(
        "Operational Efficiency (30%–80%)",
        0.30, 0.80, st.session_state.efficiency, 0.01,
        help="Current baseline is 51% (0.51). This multiplies the gross margin."
    )
    fixed_costs = st.number_input(
        f"Fixed Costs per month ({unit})",
        min_value=0.0,
        value=st.session_state.fixed_m * mult,
        step=25.0,
        key="fixed_m_input"
    )
    repairs = st.number_input(
        f"Repairs & Maintenance this month ({unit})",
        min_value=0.0,
        value=st.session_state.repairs_m * mult,
        step=10.0,
        key="repairs_m_input"
    )
    fx_impact = st.number_input(
        f"FX / Exceptionals this month ({unit})",
        value=st.session_state.fx_m * mult,
        step=10.0,
        key="fx_m_input",
        help="Positive = gain; Negative = loss"
    )

# Convert to AUD'000 for calculations
_ext_sales = ext_sales * conv
_int_sales = int_sales * conv
_fixed = fixed_costs * conv
_repairs = repairs * conv
_fx = fx_impact * conv

# --------- Calculations (Monthly) ---------
# Base margins before efficiency
ext_base_margin = max(0.0, 1.0 - ext_cost_pct)   # e.g., 20% if cost is 80%
int_base_margin = max(0.0, 1.0 - int_cost_pct)   # e.g., 50% if cost is 50%

ext_gp = _ext_sales * ext_base_margin * efficiency
int_gp = _int_sales * int_base_margin * efficiency
total_gp = ext_gp + int_gp
op = total_gp - _fixed - _repairs + _fx

# Break-even external sales (monthly) with current settings
den = (ext_base_margin * efficiency)
if den > 0:
    be_ext_sales = max(0.0, (_fixed + _repairs - _fx - int_gp) / den)
else:
    be_ext_sales = math.inf

# --------- Outputs ---------
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(f"External GP (per month, {unit})", f"{ext_gp*mult:,.0f}")
with col2:
    st.metric(f"Total GP (per month, {unit})", f"{total_gp*mult:,.0f}")
with col3:
    st.metric(f"Operating Profit (per month, {unit})", f"{op*mult:,.0f}")
with col4:
    st.metric(f"Break-even External Sales (per month, {unit})", f"{be_ext_sales*mult:,.0f}")

st.markdown("---")

# --------- Sensitivity: OP vs External Sales (monthly) ---------
base = int(_ext_sales if _ext_sales > 0 else BASELINE_MONTHLY["external_sales"])
step = max(20, int(base * 0.10))
sizes = list(range(int(base*0.5), int(base*1.8) + 1, step))
rows = []
for s in sizes:
    gp = s * ext_base_margin * efficiency + int_gp
    opp = gp - _fixed - _repairs + _fx
    rows.append({"External Sales (AUD'000/month)": s, "OP (AUD'000/month)": opp})
df = pd.DataFrame(rows)
st.line_chart(df.set_index("External Sales (AUD'000/month)"))

# --------- Footer / Info ---------
with st.expander("How this works"):
    st.write(
        f"""
- Baseline monthly sales: External ≈ {BASELINE_MONTHLY['external_sales']:.1f} AUD'000, "
        f"Internal ≈ {BASELINE_MONTHLY['internal_sales']:.1f} AUD'000, Fixed ≈ {BASELINE_MONTHLY['fixed_costs']:.1f} AUD'000.
"
        "- Realised margin = (1 − product cost %) × efficiency.
"
        "- Efficiency slider is capped 30%–80% (current baseline 51%).
"
        "- All inputs are monthly; currency toggle is for display only.
"
        """"
    )

