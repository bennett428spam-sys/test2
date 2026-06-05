import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(
    page_title="Mom's Runway",
    layout="centered"
)

st.title("📊 Mom's Financial Runway Planner")
st.write("Adjust slider to see changes.")

# --- CONTAINERS ---
milestones_layout = st.container()
slider_layout = st.container()
graph_layout = st.container()

# --- CONSTANTS ---
START_YEAR = 2026
START_AGE = 68
END_AGE = 95
YEARS_TO_PROJECT = 27 

INFLATION = 0.03
SS_COLA = 0.03          
INVESTMENT_GROWTH = 0.04       
RE_GROWTH = 0.04        
LOAN_INT = 0.06
CAP_GAINS_RATE = 0.20  

airbnb_val = 700000
airbnb_basis = 400000   
airbnb_gross = 92475
airbnb_net = 34089
airbnb_exp = airbnb_gross - airbnb_net 

cash = 3000
investments = 42000
home_val = 317000
home_equity = 143000
mortgage_payment = 12500 
family_loan = 245000
ss_annual = 1450 * 12

# --- SLIDER ---
with slider_layout:
    spending_today = st.slider(
        "Target Annual Spending",
        min_value=60000,
        max_value=300000,
        value=100000,
        step=5000,
        format="$%d"
    )
    st.markdown("📍 **Baseline: $200,000**")

# --- VARIABLES ---
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

# --- ENGINE ---
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

    if year == 2027:
        curr_liquid += 450000
        curr_liquid -= curr_mortgage
        curr_mortgage = 0 
        
    if year == 2029 and loan_active:
        p_val = (1 + LOAN_INT) ** 3
        p_back = family_loan * p_val
        curr_liquid += p_back
        loan_active = False

    if year == 2036 and airbnb_owned:
        gain = max(
            0, 
            curr_airbnb_val - airbnb_basis
        )
        tax_owed = gain * CAP_GAINS_RATE
        curr_liquid += (
            curr_airbnb_val - tax_owed
        )
        airbnb_owned = False
        airbnb_sold_year = year

    target_spending = spending_today * inf_factor
    
    m_cost = 0
    if curr_mortgage > 0:
        m_cost = mortgage_payment

    if airbnb_owned:
        income = curr_ss + (
            airbnb_gross * inf_factor
        )
        expenses = target_spending + m_cost
    else:
        income = curr_ss
        l_spend = max(
            0, 
            spending_today - airbnb_exp
        )
        expenses = (
            l_spend * inf_factor
        ) + m_cost
    
    net_cash_flow = income - expenses
    curr_liquid += net_cash_flow
    
    if curr_liquid < 0 and year > 2027:
        if airbnb_owned:
            gain = max(
                0, 
                curr_airbnb_val - airbnb_basis
            )
            tax_owed = gain * CAP_GAINS_RATE
            curr_liquid += (
                curr_airbnb_val - tax_owed
            )
            airbnb_owned = False
            airbnb_sold_year = year
            
        if curr_liquid < 0 and home_owned:
            curr_liquid += (
                curr_home_val - curr_mortgage
            )
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
            nw += curr_airbnb_val
        if home_owned:
            nw += (
                curr_home_val - curr_mortgage
            )
        if loan_active:
            nw += family_loan * (
                (1 + LOAN_INT) ** t
            )
        
    chart_data.append({
        "Year": int(year),
        "Age": int(age),
        "Net Worth": float(nw)
    })

df = pd.DataFrame(chart_data)

# --- MILESTONES ---
with milestones_layout:
    st.subheader("🏁 Key Milestones")
    
    if broke_year:
        b_age = broke_year - START_YEAR + START_AGE
        broke_status = (
            f"🔴 **Net Worth $0:** "
            f"Year {broke_year} (Age {b_age})"
        )
    else:
        broke_status = "🟢 **Net Worth $0:** Never"
        
    if airbnb_sold_year:
        a_age = (
            airbnb_sold_year - 
            START_YEAR + START_AGE
        )
        airbnb_status = (
            f"🟠 **Sell Airbnb:** "
            f"Year {airbnb_sold_year} "
            f"(Age {a_age})"
        )
    else:
        airbnb_status = "🟢 **Airbnb:** Not Sold"
        
    if home_sold_year:
        h_age = (
            home_sold_year - 
            START_YEAR + START_AGE
        )
        home_status = (
            f"💗 **Sell Home:** "
            f"Year {home_sold_year} "
            f"(Age {h_age})"
        )
    else:
        home_status = "🟢 **Home:** Not Sold"
    
    msg = (
        f"{broke_status} &nbsp;•&nbsp; "
        f"{airbnb_status} &nbsp;•&nbsp; "
        f"{home_status}"
    )
    st.markdown(msg)
    st.divider()

# --- GRAPH ---
with graph_layout:
    st.subheader("Net Worth Trajectory")
    fig = go.Figure()
    
    x_vals = df["Year"].tolist()
    y_vals = df["Net Worth"].tolist()
    
    ht = (
        "<b>Year:</b> %{x}<br>"
        "<b>Net Worth:</b> "
        "%{y:$,.0f}<extra></extra>"
    )
    
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="lines+markers",
        name="Net Worth",
        line=dict(color="#10b981", width=3),
        hovertemplate=ht
    ))

    if airbnb_sold_year:
        a_age = (
            airbnb_sold_year - 
            START_YEAR + START_AGE
        )
        txt_a = f"Sell Airbnb (Age {a_age})"
        fig.add_vline(
            x=airbnb_sold_year,
            line_dash="dash",
            line_color="#f59e0b",
            annotation_text=txt_a,
            annotation_position="bottom right"
        )

    if home_sold_year:
        h_age = (
            home_sold_year - 
            START_YEAR + START_AGE
        )
        txt_h = f"Sell Home (Age {h_age})"
        fig.add_vline(
            x=home_sold_year,
            line_dash="dash",
            line_color="#ec4899",
            annotation_text=txt_h,
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
    st.plotly_chart(
        fig, 
        use_container_width=True
    )


st.markdown("* **Investments:** Liquid moves at 4%.")
