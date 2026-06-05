import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="centered")
st.title("📊 Mom's Financial Runway")

START_YEAR = 2026
START_AGE = 68
YEARS = 27 
INF = 0.03
COLA = 0.03          
GROWTH = 0.04       
RE_GROWTH = 0.04        
LOAN_INT = 0.06
TAX_RATE = 0.20  

airbnb_val = 700000
airbnb_basis = 400000   
airbnb_gross = 92475
airbnb_exp = 92475 - 34089 

curr_liquid = 45000
curr_home_val = 317000
curr_mortgage = 174000 
curr_ss = 1450 * 12

with st.container():
    val = st.slider("Spending", 60000, 300000, 250000)

airbnb_sold_year = None
home_sold_year = None
broke_year = None
airbnb_owned = True
home_owned = True
loan_active = True
is_broke = False
chart_data = []

for t in range(YEARS + 1):
    year = START_YEAR + t
    age = START_AGE + t
    inf_factor = (1 + INF) ** t
    
    if t > 0:
        airbnb_val *= (1 + RE_GROWTH)
        curr_home_val *= (1 + RE_GROWTH)
        curr_ss *= (1 + COLA)
        if curr_liquid > 0:
            curr_liquid *= (1 + GROWTH)

    if year == 2027:
        curr_liquid += 450000
        curr_liquid -= curr_mortgage
        curr_mortgage = 0 
        
    if year == 2029 and loan_active:
        curr_liquid += 245000 * ((1 + LOAN_INT) ** 3)
        loan_active = False

    if year == 2036 and airbnb_owned:
        gain = max(0, airbnb_val - airbnb_basis)
        curr_liquid += airbnb_val - (gain * TAX_RATE)
        airbnb_owned = False
        airbnb_sold_year = year

    target_spending = val * inf_factor
    m_cost = 12500 if curr_mortgage > 0 else 0

    if airbnb_owned:
        inc = curr_ss + (airbnb_gross * inf_factor)
        exp = target_spending + m_cost
    else:
        inc = curr_ss
        l_spend = max(0, val - airbnb_exp)
        exp = (l_spend * inf_factor) + m_cost
    
    curr_liquid += inc - exp
    
    if curr_liquid < 0 and year > 2027:
        if airbnb_owned:
            gain = max(0, airbnb_val - airbnb_basis)
            curr_liquid += airbnb_val - (gain * TAX_RATE)
            airbnb_owned = False
            airbnb_sold_year = year
            
        if curr_liquid < 0 and home_owned:
            curr_liquid += curr_home_val - curr_mortgage
            curr_mortgage = 0
            home_owned = False
            home_sold_year = year
            
        if curr_liquid < 0:
            is_broke = True
            if broke_year is None:
                broke_year = year
            curr_liquid = 0

    if is_broke:
        nw = 0
        curr_liquid = 0
    else:
        nw = curr_liquid
        if airbnb_owned:
            nw += airbnb_val
        if home_owned:
            nw += curr_home_val - curr_mortgage
        if loan_active:
            nw += 245000 * ((1 + LOAN_INT) ** t)
        
    chart_data.append({"Yr": year, "Age": age, "NW": nw})

df = pd.DataFrame(chart_data)

st.subheader("Net Worth Trajectory")
fig = go.Figure()
x_v = df["Yr"].tolist()
y_v = df["NW"].tolist()
sc = go.Scatter(x=x_v, y=y_v, mode="lines+markers")
fig.add_trace(sc)

if airbnb_sold_year:
    fig.add_vline(x=airbnb_sold_year, line_dash="dash")

if home_sold_year:
    fig.add_vline(x=home_sold_year, line_dash="dash")

fig.update_layout(height=375, template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("🏁 Key Milestones")

if broke_year:
    b_age = broke_year - START_YEAR + START_AGE
    st.header(f"🔴 Broke: {broke_year} (Age {b_age})")
else:
    st.header("🟢 Broke: Never")

if airbnb_sold_year:
    a_age = airbnb_sold_year - START_YEAR + START_AGE
    st.header(f"🟠 Airbnb: {airbnb_sold_year} (Age {a_age})")
else:
    st.header("🟢 Airbnb: Not Sold")

if home_sold_year:
    h_age = home_sold_year - START_YEAR + START_AGE
    st.header(f"💗 Home: {home_sold_year} (Age {h_age})")
else:
    st.header("🟢 Home: Not Sold")
