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

# --- INTERACTIVE SLIDER (Moved closer to chart engine processing) ---
spending_today = st.slider(
    "Target Annual Spending (In Today's Dollars)", 
    min_value=60000, 
    max_value=300000, 
    value=100000, 
    step=5000,
    format="$%d",
    help="Current spending baseline is marked at $200,000 below."
)

# Visual marker directly beneath the slider
st.markdown("📍 **Current Spending Baseline: $200,000**")

# --- 2. LIVE TRACKING VARIABLES ---
curr_liquid = cash + investments
curr_airbnb_val = airbnb_val
curr_home_val = home_val
curr_mortgage = home_val - home_equity 
curr_ss = ss_annual

# Tracking variables for milestones
airbnb_sold_year = None
home_sold_year = None
broke_year = None

airbnb_owned = True
home_owned = True
loan_active = True
is_broke = False

chart_data = []

# --- 3. THE FINANCIAL SIMULATION ENGINE ---
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

    # Event: Oct 2027 Lump Sum ($450k arrives, wipes out remaining mortgage)
    if year == 2027:
        curr_liquid += 450000
        curr_liquid -= curr_mortgage
        curr_mortgage = 0 
        
    # Event: Family Loan repayment (2029)
    if year == 2029 and loan_active:
        loan_payback = family_loan * ((1 + LOAN_INT) ** 3)
        curr_liquid += loan_payback
        loan_active = False

    # Event: Forced Planned Airbnb Sale (Maximum 10 Years out -> 2036 / Age 78)
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
        expenses = target_spending + (mortgage_payment if curr_mortgage > 0 else 0)
    else:
        income = curr_ss
        lifestyle_spending_today = max(0, spending_today - airbnb_exp)
        expenses = (lifestyle_spending_today * inf_factor) + (mortgage_payment if curr_mortgage > 0 else 0)
    
    net_cash_flow = income - expenses
    curr_liquid += net_cash_flow
    
    # Liquidation triggers (ONLY active after 2027 to allow temporary bridge debt)
    if curr_liquid < 0 and year > 2027:
        if airbnb_owned:
            gain = max(0, curr_airbnb_val - airbnb_basis)
            tax_owed = gain * CAP_GAINS_RATE
            curr_liquid += (curr_airbnb_val - tax_owed)
            airbnb_owned = False
            airbnb_sold_year = year
            
        if curr_liquid < 0 and home_owned:
            curr_liquid += (curr_home_val - curr_mortgage)
            curr_mortgage = 0
            home_owned = False
            home_sold_year = year
            
        if curr_liquid < 0:
            is_broke = True
            if broke_year is None:
                broke_year = year
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
        
    chart_data.append({
        "Year": int(year), 
        "Age": int(age), 
        "Net Worth": float(nw)
    })

df = pd.DataFrame(chart_data)

# --- 4. DISPLAY METRICS (Optimized Single Line for Mobile) ---
st.subheader("🏁 Key Milestones")

broke_status = f"🔴 **Net Worth $0:** Year {broke_year} (Age {broke_year - START_YEAR + START_AGE})" if broke_year else "🟢 **Net Worth $0:** Never"
airbnb_status = f"🟠 **Sell Airbnb:** Year {airbnb_sold_year} (Age {airbnb_sold_year - START_YEAR + START_AGE})" if airbnb_sold_year else "🟢 **Airbnb:** Not Sold"
home_status = f"💗 **Sell Home:** Year {home_sold_year} (Age {home_sold_year - START_YEAR + START_AGE})" if home_sold_year else "🟢 **Home:** Not Sold"

# Outputs all items cleanly on one horizontal wrapping line
st.markdown(f"{broke_status} &nbsp;•&nbsp; {airbnb_status} &nbsp;•&nbsp; {home_status}")

# --- 5. NET WORTH GRAPH ---
st.subheader("Net Worth Trajectory (Ages 68 to 95)")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Year"].tolist(), 
    y=df["Net Worth"].tolist(), 
    mode="lines+markers", 
    name="Net Worth", 
    line=dict(color="#10b981", width=3),
    hovertemplate="<b>Year:</b> %{x}<br><b>Net Worth:</b> %{y:$,.0f}<extra></extra>"
))

# Alternating positions to eliminate vertical overlaps
if airbnb_sold_year:
    airbnb_age = airbnb_sold_year - START_YEAR + START_AGE
    fig.add_vline(
        x=airbnb_sold_year, 
        line_dash="dash", 
        line_color="#f59e0b", 
        annotation_text=f"Sell Airbnb (Age {airbnb_age})", 
        annotation_position="top right"
    )

if home_sold_year:
    home_age = home_sold_year - START_YEAR + START_AGE
    fig.add_vline(
        x=home_sold_year, 
        line_dash="dash", 
        line_color="#ec4899", 
        annotation_text=f"Sell Home (Age {home_age})", 
        annotation_position="top left"
    )

fig.update_layout(
    margin=dict(l=15, r=15, t=40, b=15),
    height=375,
    xaxis_title="Year",
    yaxis_title="Net Worth ($)",
    template="plotly_white",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# --- 6. ASSUMPTIONS BLOCK ---
st.markdown("---")
st.subheader("📋 System Assumptions & Rules")
st.markdown("""
* **Timeline Parameters:** The simulation starts in **2026** (Mom's Age: **68**) and cuts off strictly at **2053** (Mom's Age: **95**).
* **Slider Spending Inclusions:** The target spending slider **includes** the Airbnb's yearly operating expenses (**$58,386**). If the Airbnb is sold, her annual expenses automatically drop by that exact amount since she no longer carries those property liabilities.
* **Airbnb Tax & Sale Timeline:** The Airbnb is sold **no later than 2036** (Age **78**). Upon sale (planned or emergency), a **20% capital gains tax** is applied to all asset growth above the **$400,000** cost basis before the net funds flow into cash reserves.
* **Safe-Harbor Debt Rule (2026–2027):** The system permits a temporary negative cash balance during her first two years. This prevents an accidental, premature liquidation of the Airbnb before the **$450,000** cash windfall lands in October 2027.
* **Inflation & Cost of Living:** Estimated at **3%** annually. Social Security starts at **$1,450/month** and receives a **3%** annual COLA increase.
* **Real Estate Growth:** Property values scale up at **4%** per year.
* **Primary Home Mortgage:** Wiped out completely in **October 2027** using the incoming **$450,000** lump sum. The remaining surplus from that lump sum is funneled directly into her liquid savings.
* **Family Loan:** The **$245,000** loan compiles interest at **6%** and pays back fully as a single lump sum in **2029** (3-year average marker).
* **Investment Growth:** Liquid asset funds grow at **4%** annually.
""")
