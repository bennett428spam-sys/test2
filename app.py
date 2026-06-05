import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE SETUP FOR MOBILE ---
st.set_page_config(
    page_title="Mom's Financial Runway", 
    layout="centered"
)

st.title("📊 Mom's Financial Runway Planner")
st.write("Adjust the slider to see how changing annual spending changes her financial future.")

# --- CREATE LAYOUT CONTAINERS FOR UI ORDERING ---
milestones_layout = st.container()
slider_layout = st.container()
graph_layout = st.container()

# --- 1. SIMULATION CONSTANTS & ASSUMPTIONS ---
START_YEAR = 2026
START_AGE = 68
END_AGE = 95
YEARS_TO_PROJECT = END_AGE - START_AGE 

# Rates & Taxes
INFLATION = 0.03
SS_COLA = 0.03          
INVESTMENT_GROWTH = 0.04       
RE_GROWTH = 0.04        
LOAN_INT = 0.06
CAP_GAINS_RATE = 0.20  

# Airbnb Specific Breakdowns
airbnb_val = 700000
airbnb_basis = 400000   
airbnb_gross = 92475
airbnb_net = 34089
airbnb_exp = airbnb_gross - airbnb_net 

# Initial Portfolio Values
cash = 3000
investments = 42000
home_val = 317000
home_equity = 143000
mortgage_payment = 12500 
family_loan = 245000
ss_annual = 1450 * 12

# --- 2. RENDER SLIDER (Placed inside its visual container) ---
with slider_layout:
    spending_today = st.slider(
        "Target Annual Spending (In Today's Dollars)", 
        min_value=60000, 
        max_value=300000, 
        value=100000, 
        step=5000,
        format="$%d",
        help="Current spending baseline is marked at $200,000 below."
    )
    st.markdown("📍 **Current Spending Baseline: $200,000**")

# --- 3. LIVE TRACKING VARIABLES & SIMULATION ENGINE ---
curr_liquid = cash + investments
curr_airbnb_val = airbnb_val
curr_home_val = home_val
curr_mortgage = home_val - home_equity 
curr_ss = ss_annual

airbnb_sold_year = None
home_sold_year = None
broke_year = None

airbnb_owned = True
home_owned = True
loan_active = True
is_broke = False

chart_data = []

for t in range(YEARS_TO_PROJECT + 1):
    year = START_YEAR + t
    age = START_AGE + t
    inf_factor = (1 + INFLATION) ** t
    
    if t > 0:
        curr_airbnb_val *= (1 + RE_GROWTH)
        curr_home_val *= (1 + RE_GROWTH)
        curr_ss *= (1 + SS_COLA)
        
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

    # Event: Forced Planned Airbnb Sale (2036)
    if year == 2036 and airbnb_owned:
        gain = max(0, curr_airbnb_val - airbnb_basis)
        tax_owed = gain * CAP_GAINS_RATE
        curr_liquid += (curr_airbnb_val - tax_owed)
        airbnb_owned = False
        airbnb_sold_year = year

    # Calculate net annual cash flow
    target_spending = spending_today * inf_factor
    
    if airbnb_owned:
        income = curr_ss + (airbnb_gross * inf_factor)
        expenses = target_spending + (mortgage_
