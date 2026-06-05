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
SS_COLA = 0.03          # Social Security adjustments
INVESTMENT_GROWTH = 0.06
RE_GROWTH = 0.04        # Real estate appreciation
LOAN_INT = 0.06

# Initial Portfolio Values
cash = 3000
investments = 42000

airbnb_val = 700000
airbnb_net = 34089

home_val = 317000
home_equity = 143000
mortgage_payment = 12500 # Estimated annual Principal + Interest

family_loan = 245000
ss_annual = 1450 * 12

# --- LIVE TRACKING VARIABLES (Updated dynamically in the loop) ---
curr_liquid = cash + investments
curr_airbnb_val = airbnb_val
curr_airbnb_net = airbnb_net
curr_home_val = home_val
curr_mortgage = home_val - home_equity # $174,000
curr_ss = ss_annual

# Tracking variables for milestones
airbnb_sold_year = "Not Sold"
home_sold_year = "Not Sold"
broke_year = "Never (Maintains Wealth)"

airbnb_owned = True
home_owned = True
loan_active = True

chart_data = []

# --- 3. THE FINANCIAL SIMULATION ENGINE ---
for year in range(START_YEAR, START_YEAR + YEARS_TO_PROJECT + 1):
    t = year - START_YEAR
    inf_factor = (1 + INFLATION) ** t
    
    # Compound asset values and index income to inflation
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

    # Event: Oct 2027 Lump Sum ($450k arrives, wipes out remaining mortgage)
    if year == 2027:
        curr_liquid += 450000
        curr_liquid -= curr_mortgage
        curr_mortgage = 0 # Mortgage is completely paid off
        
    # Event: Family Loan repayment (Assumed mid-point: 3 years out, 2029)
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
            if broke_year == "Never (Maintains Wealth)":
                broke_year = str(year)
            curr_liquid = 0

    # Calculate Aggregate Net Worth
    nw = curr_liquid
    if airbnb_owned:
