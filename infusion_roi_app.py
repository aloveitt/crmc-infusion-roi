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
    utilization_rate = st.slider("Chair Utilization Rate (%)", min_value=50, max_value=100, value=85) / 100

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

    st.subheader("📈 Forecast Settings")
    forecast_years = st.number_input("Forecast Period (Years)", value=10)
    discount_rate = st.number_input("Discount Rate (%)", value=3.0) / 100

    growth_toggle = st.checkbox("Include Annual Visit Growth?")
    annual_growth = st.number_input("Annual Visit Growth (%)", value=5.0) / 100 if growth_toggle else 0.0

# ---------------- Calculations ----------------
facility_sqft = num_chairs * sqft_per_chair
construction_cost = facility_sqft * cost_per_sqft
equipment_cost = num_chairs * equipment_cost_per_chair
capital_cost_total = construction_cost + equipment_cost

rn_fte_required = np.ceil((num_chairs / chairs_per_rn) * shifts_per_day)
rn_cost_total = rn_fte_required * rn_cost

# Visits per year
visits_per_year = []
for year in range(forecast_years):
    if year == 0:
        raw_visits = num_chairs * visits_per_chair_per_day * days_per_year
    else:
        raw_visits = visits_per_year[-1] / utilization_rate * (1 + annual_growth)

    adjusted_visits = raw_visits * utilization_rate
    visits_per_year.append(adjusted_visits)

# Annual Financials
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
    "Visits": np.round(visits_per_year),
    "Revenue ($)": np.round(revenue),
    "Op Costs ($)": np.round(operating_costs),
    "Net Income ($)": np.round(net_income),
    "Cum Cashflow ($)": np.round(cumulative_cashflow),
    "NPV ($)": np.round(discounted_cashflow),
    "Cum NPV ($)": np.round(cumulative_npv)
})

st.dataframe(summary_df.style.format("{:,.0f}"), use_container_width=True)

# Chart
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

# ---------------- FAQ Section ----------------
with st.expander("ℹ️ FAQ & Financial Definitions"):
    st.markdown("""
**Net Present Value (NPV):**  
The total profit of a project in today’s dollars, accounting for inflation and risk. NPV > 0 means it’s worth doing.

**Discount Rate:**  
The annual % used to adjust future earnings back to present-day value. Higher = more conservative.

**Chair Utilization (%):**  
Reflects real-world capacity — chairs are rarely at 100% due to clean-up, late arrivals, and downtime. This input adjusts total visits and revenue.

**RN FTE Calculation:**  
Calculated based on total chairs, shifts/day, and chair-to-RN ratio.

**Breakeven Point:**  
The year when cumulative NPV becomes positive — meaning you’ve recovered your capital investment and are generating true profit.

**Forecast Period:**  
The number of years the ROI model looks ahead. Longer periods can show delayed profitability.

**Why This Matters:**  
This tool helps model different growth and investment strategies for infusion expansion — letting you size the buildout to match projected demand, staffing, and space.
    """)
