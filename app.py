import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="centered")
st.title("📊 Mom's Financial Runway")

Y_ST = 2026
A_ST = 68
YRS = 27 
INF = 0.03
COLA = 0.03          
GRW = 0.04       
RE_GRW = 0.04        
L_INT = 0.06
TAX = 0.20  

ab_val = 700000
ab_bas = 400000   
ab_grs = 92475
ab_exp = 92475 - 34089 

liq = 45000
hm_val = 317000
mtg = 174000 
ss = 1450 * 12

val = st.slider(
    "Spending", 60000, 300000, 250000
)

ay = None
hy = None
by = None
ao = True
ho = True
la = True
ib = False
cd = []

for t in range(YRS + 1):
    yr = Y_ST + t
    ag = A_ST + t
    inf = (1 + INF) ** t
    
    if t > 0:
        ab_val *= (1 + RE_GRW)
        hm_val *= (1 + RE_GRW)
        ss *= (1 + COLA)
        if liq > 0:
            liq *= (1 + GRW)

    if yr == 2027:
        liq += 450000
        liq -= mtg
        mtg = 0 
        
    if yr == 2029 and la:
        liq += 245000 * ((1 + L_INT) ** 3)
        la = False

    if yr == 2036 and ao:
        gn = max(0, ab_val - ab_bas)
        liq += ab_val - (gn * TAX)
        ao = False
        ay = yr

    tgt = val * inf
    mc = 12500 if mtg > 0 else 0

    if ao:
        inc = ss + (ab_grs * inf)
        exp = tgt + mc
    else:
        inc = ss
        lsp = max(0, val - ab_exp)
        exp = (lsp * inf) + mc
    
    liq += inc - exp
    
    if liq < 0 and yr > 2027:
        if ao:
            gn = max(0, ab_val - ab_bas)
            liq += ab_val - (gn * TAX)
            ao = False
            ay = yr
            
        if liq < 0 and ho:
            liq += hm_val - mtg
            mtg = 0
            ho = False
            hy = yr
            
        if liq < 0:
            ib = True
            if by is None:
                by = yr
            liq = 0

    if ib:
        nw = 0
        liq = 0
    else:
        nw = liq
        if ao:
            nw += ab_val
        if ho:
            nw += hm_val - mtg
        if la:
            nw += 245000 * ((1 + L_INT) ** t)
        
    cd.append({"Yr": yr, "Age": ag, "NW": nw})

df = pd.DataFrame(cd)

st.subheader("Net Worth Trajectory")
fig = go.Figure()
sc = go.Scatter(
    x=df["Yr"].tolist(), 
    y=df["NW"].tolist(), 
    mode="lines+markers"
)
fig.add_trace(sc)

if ay:
    ag_a = ay - Y_ST + A_ST
    t_a = f"Airbnb (Age {ag_a})"
    da = {"x": ay, "line_dash": "dash"}
    da["line_color"] = "#f59e0b"
    da["annotation_text"] = t_a
    da["annotation_position"] = "bottom right"
    fig.add_vline(**da)

if hy:
    ag_h = hy - Y_ST + A_ST
    t_h = f"Home (Age {ag_h})"
    dh = {"x": hy, "line_dash": "dash"}
    dh["line_color"] = "#ec4899"
    dh["annotation_text"] = t_h
    dh["annotation_position"] = "top left"
    fig.add_vline(**dh)

fig.update_layout(
    height=375, template="plotly_white"
)
st.plotly_chart(
    fig, use_container_width=True
)

st.divider()
st.subheader("🏁 Key Milestones")

if by:
    ag_b = by - Y_ST + A_ST
    st.header(f"🔴 Broke: {by} (Age {ag_b})")
else:
    st.header("🟢 Broke: Never")

if ay:
    ag_a = ay - Y_ST + A_ST
    st.header(f"🟠 Airbnb: {ay} (Age {ag_a})")
else:
    st.header("🟢 Airbnb: Not Sold")

if hy:
    ag_h = hy - Y_ST + A_ST
    st.header(f"💗 Home: {hy} (Age {ag_h})")
else:
    st.header("🟢 Home: Not Sold")
