import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE SETUP FOR MOBILE ---
st.set_page_config(page_title="Mom's Financial Runway", layout="centered")

st.title("📊 Mom's Financial Runway Planner")
st.write("Adjust the slider to see how changing annual spending changes her financial future.")

# --- 1. INTERACTIVE SLIDER ---
spending_today = st.slider(
    "Target Annual Spending (In Today's Dollars)", 
    min_value=60000, 
    max_value=220000, 
    value=100000, 
    step=5000,
    format="$%d"
)

# --- 2. SIMULATION CONSTANTS & ASSUMPTIONS ---
START_YEAR = 2026
YEARS_TO_PROJECT = 50

# Rates
INFLATION = 0.03
SS_COLA = 0.03          
INVESTMENT_GROWTH = 0.06
RE_GROWTH = 0.04        
LOAN_INT = 0.06

# Initial Portfolio Values
cash = 3000
investments = 42000

airbnb_val = 700000
airbnb_net = 34089

home_val = 317000
home_equity = 143000
mortgage_payment = 12500 

family_loan = 245000
ss_annual = 1450 * 12

# --- LIVE TRACKING VARIABLES ---
curr_liquid = cash + investments
curr_airbnb_val = airbnb_val
curr_airbnb_net = airbnb_net
curr_home_val = home_val
curr_mortgage = home_val - home_equity 
curr_ss = ss_annual

# Tracking variables for milestones
airbnb_sold_year = "Not Sold"
home_sold_year = "Not Sold"
broke_year = "Never (Maintains Wealth)"

airbnb_owned = True
home_owned = True
loan_active = True
is_broke = False

chart_data = []

# --- 3. THE FINANCIAL SIMULATION ENGINE ---
for year in range(START_YEAR, START_YEAR + YEARS_TO_PROJECT + 1):
    t = year - START_YEAR
    inf_factor = (1 + INFLATION) ** t
    
    if t > 0:
        curr_airbnb_val *= (1 + RE_GROWTH)
        curr_home_val *= (1 + RE_GROWTH)
        curr_ss *= (1 + SS_COLA)
        if airbnb_owned:
            curr_airbnb_net *= (1 + INFLATION)
        else:
            curr_airbnb_net = 0
        
        if curr_liquid > 0:
            curr_liquid *= (1 + INVESTMENT_GROWTH)

    # Event: Oct 2027 Lump Sum
    if year == 2027:
        curr_liquid += 450000
        curr_liquid -= curr_mortgage
        curr_mortgage = 0 
        
    # Event: Family Loan repayment (2029)
    if year == 2029 and loan_active:
        loan_payback = family_loan * ((1 + LOAN_INT) ** 3)
        curr_liquid += loan_payback
        loan_active = False

    # Calculate net annual cash flow
    target_spending = spending_today * inf_factor
    income = curr_ss + (curr_airbnb_net if airbnb_owned else 0)
    expenses = target_spending + (mortgage_payment if curr_mortgage > 0 else 0)
    
    net_cash_flow = income - expenses
    curr_liquid += net_cash_flow
    
    # Liquidation triggers if cash runs out
    if curr_liquid < 0:
        if airbnb_owned:
            curr_liquid += curr_airbnb_val
            airbnb_owned = False
            airbnb_sold_year = str(year)
            curr_airbnb_net = 0
            
        if curr_liquid < 0 and home_owned:
            curr_liquid += (curr_home_val - curr_mortgage)
            curr_mortgage = 0
            home_owned = False
            home_sold_year = str(year)
            
        if curr_liquid < 0:
            is_broke = True
            if broke_year == "Never (Maintains Wealth)":
                broke_year = str(year)
            curr_liquid = 0

    # Calculate Aggregate Net Worth
    if is_broke:
        nw = 0
        curr_liquid = 0
    else:
        nw = curr_liquid
        if airbnb_owned:
            nw += curr_airbnb_val
        if home_owned:
            nw += (curr_home_val - curr_mortgage)
        if loan_active:
            nw += family_loan * ((1 + LOAN_INT) ** t)
        
    chart_data.append({"Year": year, "Net Worth": nw})

df = pd.DataFrame(chart_data)

# --- 4. DISPLAY METRICS ---
st.subheader("Key Milestones")
col1, col2, col3 = st.columns(3)
col1.metric("Net Worth Hits $0", broke_year)
col2.metric("Sell Airbnb", airbnb_sold_year)
col3.metric("Sell Primary Home", home_sold_year)

# --- 5. NET WORTH GRAPH ---
st.subheader("Net Worth Trajectory")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df["Year"], 
    y=df["Net Worth"], 
    mode="lines", 
    name="Net Worth", 
    line=dict(color="#10b981", width=3)
))
fig.update_layout(
    margin=dict(l=20, r=20, t=20, b=20),
    height=300,
    xaxis_title="Year",
    yaxis_title="Net Worth ($)",
    template="plotly_white",
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

# --- 6. ASSUMPTIONS BLOCK ---
st.markdown("---")
st.subheader("📋 System Assumptions & Rules")
st.markdown(f"""
* **Current Setup (2026):** Starting cash of **$3,000** and investments of **$42,000**.
* **Inflation & Cost of Living:** Estimated at **{INFLATION*100:.0f}%** annually. Social Security starts at **$1,450/month** and receives a **{SS_COLA*100:.0f}%** annual COLA increase.
* **Real Estate Growth:** Property values scale up at **{RE_GROWTH*100:.0f}%** per year.
* **Airbnb Income:** Generates **$34,089/yr** net income (adjusts with inflation). Income completely stops if the property is liquidated.
* **Primary Home Mortgage:** Wiped out completely in **October 2027** using the incoming **$450,000** lump sum. The remaining surplus from that lump sum is funneled directly into her liquid savings.
* **Family Loan:** The **$245,000** loan compiles interest at **{LOAN_INT*100:.0f}%** and pays back fully as a single lump sum in **2029** (3-year average marker).
* **Investment Growth:** Liquid asset funds grow at **{INVESTMENT_GROWTH*100:.0f}%** annually.
* **Liquidation Protocol:** If her cash balance runs below $0, the system automatically triggers a sale of the Airbnb first at its appreciated value. If cash bottoms out again down the road, it triggers the sale of her primary home.
""")
