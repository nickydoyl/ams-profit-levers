import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="AMS Profit Levers Simulator (Monthly)", layout="wide")
st.title("AMS Profit Levers Simulator (Monthly)")

# --------- Baseline from FY2025 board pack (AUD '000) ---------
BASELINE_ANNUAL = {
    "external_sales": 8658.0,
    "internal_sales": 8245.0,
    "fixed_costs": 3702.0,
}
BASELINE_MONTHLY = {
    "external_sales": BASELINE_ANNUAL["external_sales"] / 12.0,
    "internal_sales": BASELINE_ANNUAL["internal_sales"] / 12.0,
    "fixed_costs": BASELINE_ANNUAL["fixed_costs"] / 12.0,
    "efficiency": 0.51,
    "ext_cost_pct": 0.80,
    "int_cost_pct": 0.50,
    "repairs": 0.0,
    "fx": 0.0,
}

RESET_KEYS = [
    "currency","fx_rate","ext_sales_m","int_sales_m","ext_cost_pct",
    "int_cost_pct","efficiency","fixed_m","repairs_m","fx_m",
    "ext_sales_m_input","int_sales_m_input","ext_cost_pct_input",
    "int_cost_pct_input","fixed_m_input","repairs_m_input","fx_m_input"
]

def reset_to_baseline():
    # Clear any widget state that may conflict
    for k in RESET_KEYS:
        st.session_state.pop(k, None)
    # Seed fresh baseline state
    st.session_state.update({
        "currency": "AUD '000",
        "fx_rate": 24.0,
        "ext_sales_m": BASELINE_MONTHLY["external_sales"],
        "int_sales_m": BASELINE_MONTHLY["internal_sales"],
        "ext_cost_pct": BASELINE_MONTHLY["ext_cost_pct"],
        "int_cost_pct": BASELINE_MONTHLY["int_cost_pct"],
        "efficiency": BASELINE_MONTHLY["efficiency"],
        "fixed_m": BASELINE_MONTHLY["fixed_costs"],
        "repairs_m": BASELINE_MONTHLY["repairs"],
        "fx_m": BASELINE_MONTHLY["fx"],
    })

# First run seed
if "seeded" not in st.session_state:
    reset_to_baseline()
    st.session_state["seeded"] = True

# --------- Sidebar: Global Settings & Reset ---------
with st.sidebar:
    st.header("Global Settings")
    currency = st.selectbox("Display Currency", ["AUD '000", "THB '000"], index=0, key="currency")
    fx_rate = st.number_input("FX Rate (THB per 1 AUD)", min_value=10.0, max_value=50.0,
                               value=st.session_state.get("fx_rate", 24.0), step=0.1, key="fx_rate")
    if st.button("🔄 Reset to current baseline (51% efficiency, monthly averages)"):
        reset_to_baseline()
        st.rerun()

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
        "External Product Cost (% of sales)", 0, 100, int(st.session_state.ext_cost_pct * 100),
        key="ext_cost_pct_input", help="Default 80% for external"
    ) / 100.0
    int_cost_pct = st.slider(
        "Internal Product Cost (% of sales)", 0, 100, int(st.session_state.int_cost_pct * 100),
        key="int_cost_pct_input", help="Default 50% for internal"
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
ext_base_margin = max(0.0, 1.0 - ext_cost_pct)
int_base_margin = max(0.0, 1.0 - int_cost_pct)

ext_gp = _ext_sales * ext_base_margin * efficiency
int_gp = _int_sales * int_base_margin * efficiency
total_gp = ext_gp + int_gp
op = total_gp - _fixed - _repairs + _fx

# Derived KPIs
total_sales = _ext_sales + _int_sales
annualize = 12.0
annual_op = op * annualize
annual_sales = total_sales * annualize

# Break-even external sales (monthly)
den = (ext_base_margin * efficiency)
if den > 0:
    be_ext_sales = max(0.0, (_fixed + _repairs - _fx - int_gp) / den)
else:
    be_ext_sales = math.inf

# --------- Outputs ---------
st.markdown("---")
col0, col1, col2, col3, col4 = st.columns(5)
with col0:
    st.metric(f"Total Sales (per month, {unit})", f"{total_sales*mult:,.0f}")
with col1:
    st.metric(f"External GP (per month, {unit})", f"{ext_gp*mult:,.0f}")
with col2:
    st.metric(f"Total GP (per month, {unit})", f"{total_gp*mult:,.0f}")
with col3:
    st.metric(f"Operating Profit (per month, {unit})", f"{op*mult:,.0f}")
with col4:
    st.metric(f"Break-even External Sales (per month, {unit})", f"{be_ext_sales*mult:,.0f}")

st.caption(f"Annualized totals → Sales: {annual_sales*mult:,.0f} {unit}, OP: {annual_op*mult:,.0f} {unit}")

st.markdown("---")

# Sensitivity: OP vs External Sales (monthly)
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

with st.expander("How this works"):
    st.write(
        f"- Baseline monthly sales: External ≈ {BASELINE_MONTHLY['external_sales']:.1f} AUD'000, "
        f"Internal ≈ {BASELINE_MONTHLY['internal_sales']:.1f} AUD'000, Fixed ≈ {BASELINE_MONTHLY['fixed_costs']:.1f} AUD'000.\n"
        "- Realised margin = (1 − product cost %) × efficiency.\n"
        "- Efficiency slider is capped 30%–80% (current baseline 51%).\n"
        "- All inputs are monthly; currency toggle is for display only."
    )
