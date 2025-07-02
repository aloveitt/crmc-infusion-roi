import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="CRMC Infusion ROI Simulator", layout="wide")

# ---------------- Password Protection ----------------
PASSWORD = "CRMC2024"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 CRMC Infusion ROI Simulator")
    password = st.text_input("Enter password to continue:", type="password")
    if password == PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    else:
        st.stop()

# ---------------- Inputs ----------------
st.title("💉 Infusion Chair ROI Model")

with st.sidebar:
    st.header("Model Inputs")

    st.subheader("💺 Capacity & Construction")
    num_chairs = st.slider("Number of Chairs", min_value=5, max_value=40, value=20)
    sqft_per_chair = st.number_input("Square Feet per Chair", value=100)
    cost_per_sqft = st.number_input("Construction Cost per Sqft ($)", value=400)
    equipment_cost_per_chair = st.number_input("Equipment Cost per Chair ($)", value=20000)

    st.subheader("📈 Utilization & Growth")
    initial_utilization = st.slider("Initial Chair Utilization (%)", min_value=0, max_value=100, value=50) / 100
    max_utilization = st.slider("Max Utilization Cap (%)", min_value=50, max_value=100, value=85) / 100
    annual_growth = st.slider("Annual Visit Growth (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1) / 100

    st.subheader("🩺 Operating Costs")
    rn_cost = st.number_input("RN Annual Cost per FTE ($)", value=90000)
    chairs_per_rn = st.number_input("Chairs per RN", value=4)
    shifts_per_day = st.number_input("Shifts per Day", value=2)
    supply_cost_per_visit = st.number_input("Drug/Supply Cost per Visit ($)", value=500)
    overhead_cost = st.number_input("Annual Overhead/Admin Cost ($)", value=300000)

    st.subheader("💵 Revenue")
    reimbursement = st.number_input("Reimbursement per Visit ($)", value=1200)
    visits_per_chair_per_day = st.number_input("Visits per Chair per Day", value=3.0)
    hours_per_day = st.number_input("Operating Hours per Day (for info only)", value=10)
    days_per_year = st.number_input("Operational Days per Year", value=260)

    st.subheader("📊 Financial Settings")
    forecast_years = st.number_input("Forecast Period (Years)", value=10)
    discount_rate = st.number_input("Discount Rate (%)", value=3.0) / 100

# ---------------- Calculations ----------------
facility_sqft = num_chairs * sqft_per_chair
construction_cost = facility_sqft * cost_per_sqft
equipment_cost = num_chairs * equipment_cost_per_chair
capital_cost_total = construction_cost + equipment_cost

rn_fte_required = np.ceil((num_chairs / chairs_per_rn) * shifts_per_day)
rn_cost_total = rn_fte_required * rn_cost

max_visits = num_chairs * visits_per_chair_per_day * days_per_year

# Visits per year based on ramping utilization
visits_per_year = []
utilization_by_year = []

for year in range(forecast_years):
    utilization = min(initial_utilization * ((1 + annual_growth) ** year), max_utilization)
    adjusted_visits = max_visits * utilization
    visits_per_year.append(adjusted_visits)
    utilization_by_year.append(utilization)

# Financials
revenue = [v * reimbursement for v in visits_per_year]
supply_costs = [v * supply_cost_per_visit for v in visits_per_year]
operating_costs = [rn_cost_total + overhead_cost + sc for sc in supply_costs]
net_income = [rev - cost for rev, cost in zip(revenue, operating_costs)]

# Discounted Cash Flow
cumulative_cashflow = []
discounted_cashflow = []
cumulative_npv = []
total_npv = 0

for year in range(forecast_years):
    cash = net_income[year] if year > 0 else net_income[year] - capital_cost_total
    discounted = cash / ((1 + discount_rate) ** year)
    total_npv += discounted
    discounted_cashflow.append(discounted)
    cumulative_cashflow.append(sum(net_income[:year + 1]) - capital_cost_total)
    cumulative_npv.append(total_npv)

# ---------------- Output ----------------
st.subheader("📊 ROI Summary")
summary_df = pd.DataFrame({
    "Year": list(range(1, forecast_years + 1)),
    "Utilization (%)": [f"{u*100:.1f}%" for u in utilization_by_year],
    "Visits": np.round(visits_per_year),
    "Revenue ($)": np.round(revenue),
    "Op Costs ($)": np.round(operating_costs),
    "Net Income ($)": np.round(net_income),
    "Cum Cashflow ($)": np.round(cumulative_cashflow),
    "NPV ($)": np.round(discounted_cashflow),
    "Cum NPV ($)": np.round(cumulative_npv)
})

st.dataframe(summary_df.style.format({
    "Visits": "{:,.0f}",
    "Revenue ($)": "{:,.0f}",
    "Op Costs ($)": "{:,.0f}",
    "Net Income ($)": "{:,.0f}",
    "Cum Cashflow ($)": "{:,.0f}",
    "NPV ($)": "{:,.0f}",
    "Cum NPV ($)": "{:,.0f}"
}), use_container_width=True)

# ROI Chart
st.subheader("💡 Breakeven Visualization")
fig, ax = plt.subplots()
ax.plot(summary_df["Year"], summary_df["Cum NPV ($)"], marker="o", label="Cumulative NPV")
ax.axhline(0, color='red', linestyle='--', linewidth=1)
ax.set_xlabel("Year")
ax.set_ylabel("Cumulative Net Gain ($)")
ax.set_title("Net Present Value Over Time")
ax.ticklabel_format(style='plain', axis='y')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax.legend()
st.pyplot(fig)

# Interpretation
final_npv = cumulative_npv[-1]
if final_npv > 0:
    st.success(f"✅ Positive ROI. 10-Year NPV = ${final_npv:,.0f}")
else:
    st.error(f"❌ Project not profitable over 10 years. NPV = ${final_npv:,.0f}")

# Growth Forecast Chart (Always Visible)
st.subheader("📈 Projected Annual Infusion Visits")
fig2, ax2 = plt.subplots()
years = list(range(1, forecast_years + 1))
ax2.plot(years, visits_per_year, marker="o", label="Adjusted Visits (Utilization Ramp)")
ax2.plot(years, [max_visits] * forecast_years, linestyle="--", color="gray", label="100% Max Capacity")
ax2.plot(years, [max_visits * max_utilization] * forecast_years, linestyle="--", color="orange", label=f"{int(max_utilization*100)}% Cap")
ax2.set_xlabel("Year")
ax2.set_ylabel("Annual Infusion Visits")
ax2.set_title("Projected Visit Volume Over Time")
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax2.legend()
st.pyplot(fig2)

# Tabs: FAQ & Calculations
tab1, tab2 = st.tabs(["📘 FAQ & Definitions", "🧮 Calculations & Formulas"])

with tab1:
    st.markdown("""
**Net Present Value (NPV):**  
The total profit of a project in today’s dollars, accounting for inflation and risk. NPV > 0 means it’s worth doing.

**Discount Rate:**  
The annual % used to adjust future earnings back to present-day value. Higher = more conservative.

**Chair Utilization:**  
Starts at your selected % and increases annually with growth, capped at the maximum utilization.

**Breakeven Point:**  
The year when cumulative NPV becomes positive — meaning you’ve recovered your capital investment and are generating true profit.

**Forecast Period:**  
The number of years the ROI model looks ahead. Longer periods can show delayed profitability.
    """)

with tab2:
    st.markdown("""
**Capital Costs:**  
- Construction = Chairs × SqFt/Chair × $/SqFt  
- Equipment = Chairs × Equipment Cost  
- Total Capital = Construction + Equipment  

**Operating Costs:**  
- RN FTEs = ceil((Chairs ÷ Chairs/RN) × Shifts/Day)  
- RN Cost = RN FTEs × Cost/FTE  
- Supplies = Visits × Supply Cost/Visit  
- Total Op Cost = RN + Overhead + Supplies  

**Revenue & Visits:**  
- Max Visits = Chairs × Visits/Day × Days/Year  
- Utilization increases yearly:  
  Util = min(Start × (1 + Growth)^Year, MaxCap)  
- Adjusted Visits = Max Visits × Utilization  
- Revenue = Visits × Reimbursement  

**Profit & ROI:**  
- Net Income = Revenue − Operating Cost  
- Year 0 Cashflow = Net Income − Capital Cost  
- Discounted Cash = Cash ÷ (1 + Discount Rate)^Year  
- NPV = Sum of Discounted Cash Flows
    """)
