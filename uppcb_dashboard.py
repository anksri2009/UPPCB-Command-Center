import streamlit as st
import pandas as pd
import numpy as np
import random
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# --- 1. ENTERPRISE LIGHT THEME CONFIGURATION ---
st.set_page_config(page_title="UPPCB Command Centre", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Sabhiv-Grade Enterprise Light Theme */
    .stApp { background-color: #f4f7f6; color: #1e293b; font-family: 'Inter', sans-serif; }
    .noc-header { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #0f172a; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid #cbd5e1; padding-bottom: 10px; margin-bottom: 20px;}
    .kpi-card { background: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: center; }
    .kpi-title { font-size: 0.85rem; color: #64748b; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;}
    .kpi-val { font-size: 2.2rem; font-weight: 800; color: #0f172a;}
    .alert-critical { color: #dc2626; }
    .alert-safe { color: #16a34a; }
    .terminal { background-color: #f8fafc; color: #334155; font-family: 'Courier New', monospace; padding: 15px; border-radius: 5px; border: 1px solid #cbd5e1; border-left: 4px solid #3b82f6; font-size: 0.85rem; height: 180px; overflow-y: auto;}
    .legal-notice { background-color: #ffffff; color: #000000; padding: 30px; font-family: 'Times New Roman', serif; border: 1px solid #94a3b8; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border-top: 8px solid #0f172a; border-radius: 4px; }
    .waste-metric { font-size: 1.5rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA GENERATION (170 STPs, 25 BMWs, and ~200 HCFs) ---
@st.cache_data
def load_full_infrastructure():
    # Anchor Facilities
    data = [
        {"ID": "STP-LKO-01", "Type": "STP", "Name": "Bharwara STP", "District": "Lucknow", "Capacity": 345, "Lat": 26.8500, "Lon": 81.0500, "Status": "Compliant"},
        {"ID": "STP-LKO-02", "Type": "STP", "Name": "Daulatganj STP", "District": "Lucknow", "Capacity": 56, "Lat": 26.8650, "Lon": 80.9000, "Status": "Compliant"},
        {"ID": "STP-KNP-01", "Type": "STP", "Name": "Jajmau STP", "District": "Kanpur", "Capacity": 130, "Lat": 26.4333, "Lon": 80.4000, "Status": "Critical"},
        {"ID": "STP-VAR-01", "Type": "STP", "Name": "Dinapur STP", "District": "Varanasi", "Capacity": 140, "Lat": 25.3333, "Lon": 83.0167, "Status": "Compliant"},
        {"ID": "BMW-LKO-01", "Type": "BMW", "Name": "SMS Water Grace BMW", "District": "Lucknow", "Capacity": 0, "Lat": 26.8467, "Lon": 80.9462, "Status": "Compliant"},
        {"ID": "BMW-KNP-01", "Type": "BMW", "Name": "Medical Pollution Control", "District": "Kanpur", "Capacity": 0, "Lat": 26.4499, "Lon": 80.3319, "Status": "Compliant"},
        {"ID": "BMW-MRT-01", "Type": "BMW", "Name": "Synergy Waste Mgmt", "District": "Meerut", "Capacity": 0, "Lat": 28.9800, "Lon": 77.7000, "Status": "Compliant"},
        {"ID": "BMW-GZB-01", "Type": "BMW", "Name": "Biotic Waste Solutions", "District": "Ghaziabad", "Capacity": 0, "Lat": 28.6667, "Lon": 77.4500, "Status": "Critical"}
    ]
    
    up_districts = {
        "Agra": (27.17, 78.00), "Prayagraj": (25.43, 81.84), "Bareilly": (28.36, 79.43), 
        "Gorakhpur": (26.76, 83.37), "Jhansi": (25.44, 78.56), "Saharanpur": (29.96, 77.54), 
        "Ayodhya": (26.79, 82.19), "Mirzapur": (25.14, 82.56)
    }
    
    # Pad STPs to 170
    current_stps = len([d for d in data if d["Type"] == "STP"])
    for i in range(current_stps + 1, 171):
        dist, coords = random.choice(list(up_districts.items()))
        stat = np.random.choice(["Compliant", "Warning", "Critical"], p=[0.75, 0.15, 0.10])
        data.append({"ID": f"STP-{dist[:3].upper()}-{i}", "Type": "STP", "Name": f"{dist} Jal Nigam STP {i}", "District": dist, "Capacity": random.randint(5, 60), "Lat": coords[0]+random.uniform(-0.3,0.3), "Lon": coords[1]+random.uniform(-0.3,0.3), "Status": stat})
    
    # Pad BMWs to 25
    current_bmws = len([d for d in data if d["Type"] == "BMW"])
    for i in range(current_bmws + 1, 26):
        dist, coords = random.choice(list(up_districts.items()))
        stat = np.random.choice(["Compliant", "Warning", "Critical"], p=[0.85, 0.10, 0.05])
        data.append({"ID": f"BMW-{dist[:3].upper()}-{i}", "Type": "BMW", "Name": f"{dist} CBWTF {i}", "District": dist, "Capacity": 0, "Lat": coords[0]+random.uniform(-0.3,0.3), "Lon": coords[1]+random.uniform(-0.3,0.3), "Status": stat})
        
    df = pd.DataFrame(data)
    df["Color"] = df["Status"].map({"Compliant": "#16a34a", "Warning": "#ca8a04", "Critical": "#dc2626"})
    return df

@st.cache_data
def generate_hcf_network(bmw_df):
    hcf_data = []
    hcf_types = ["District Hospital", "City Care Clinic", "Pathology Lab", "Surgical Centre", "Maternity Home"]
    
    for idx, bmw in bmw_df.iterrows():
        num_hcfs = random.randint(6, 15) # Generate 6 to 15 hospitals per CBWTF
        for i in range(num_hcfs):
            h_type = random.choice(hcf_types)
            base_lat, base_lon = bmw['Lat'], bmw['Lon']
            
            # Scatter HCFs within a ~15-30km radius of the BMW plant
            lat = base_lat + random.uniform(-0.15, 0.15)
            lon = base_lon + random.uniform(-0.15, 0.15)
            
            # Generate daily waste in kg
            scale = 5.0 if "Hospital" in h_type else 1.0
            yellow = round(random.uniform(10, 50) * scale, 1) # Anatomical/Infectious
            red = round(random.uniform(8, 40) * scale, 1)     # Plastics/Tubing
            white = round(random.uniform(1, 10) * scale, 1)   # Sharps/Needles
            blue = round(random.uniform(2, 15) * scale, 1)    # Glassware
            
            hcf_data.append({
                "HCF_ID": f"HCF-{bmw['District'][:3].upper()}-{idx}-{i}",
                "Name": f"{bmw['District']} {h_type} {i+1}",
                "Parent_BMW_ID": bmw['ID'],
                "Parent_BMW_Name": bmw['Name'],
                "Lat": lat, "Lon": lon,
                "Yellow_kg": yellow, "Red_kg": red, "White_kg": white, "Blue_kg": blue,
                "Total_kg": round(yellow + red + white + blue, 1)
            })
    return pd.DataFrame(hcf_data)

df = load_full_infrastructure()
hcf_df = generate_hcf_network(df[df["Type"] == "BMW"])

# --- 3. COMMAND NAVIGATION & GLOBAL SEARCH ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/fa/Seal_of_Uttar_Pradesh.svg", width=90)
    st.markdown("### GoUP Environment NOC")
    st.caption("Central Command | HCF Network Edition")
    st.markdown("---")
    
    # Global Search
    search_query = st.text_input("🔍 Global Facility Search", placeholder="Enter Name or ID...")
    
    st.markdown("---")
    module = st.radio("OPERATIONAL DESKS", [
        "🗺️ State GIS Matrix", 
        "💧 STP Command Node", 
        "🏥 BMW & HCF Command Node", 
        "⚖️ Enforcement Desk"
    ])

# Filter dataframe based on search
display_df = df
if search_query:
    display_df = df[df['Name'].str.contains(search_query, case=False, na=False) | 
                    df['ID'].str.contains(search_query, case=False, na=False)]

# --- 4. MODULE: GLOBAL GRID ---
if module == "🗺️ State GIS Matrix":
    st.markdown("<h2 class='noc-header'>Global Infrastructure Matrix (UP)</h2>", unsafe_allow_html=True)
    
    if search_query and display_df.empty:
        st.warning(f"No facilities found matching '{search_query}'.")
    else:
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f"<div class='kpi-card'><div class='kpi-title'>Displayed Nodes</div><div class='kpi-val'>{len(display_df)}</div></div>", unsafe_allow_html=True)
        k2.markdown(f"<div class='kpi-card'><div class='kpi-title'>Active STPs</div><div class='kpi-val'>{len(display_df[display_df['Type']=='STP'])}</div></div>", unsafe_allow_html=True)
        k3.markdown(f"<div class='kpi-card'><div class='kpi-title'>Active CBWTFs</div><div class='kpi-val'>{len(display_df[display_df['Type']=='BMW'])}</div></div>", unsafe_allow_html=True)
        k4.markdown(f"<div class='kpi-card'><div class='kpi-title'>Critical Deviations</div><div class='kpi-val alert-critical'>{len(display_df[display_df['Status']=='Critical'])}</div></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        fig = px.scatter_mapbox(display_df, lat="Lat", lon="Lon", hover_name="Name", hover_data=["ID", "Type", "Status"],
                                color="Status", color_discrete_map={"Compliant": "#16a34a", "Warning": "#ca8a04", "Critical": "#dc2626"},
                                zoom=6.2 if not search_query else 9, height=600)
        fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="#f4f7f6")
        st.plotly_chart(fig, use_container_width=True)

# --- 5. MODULE: STP COMMAND NODE ---
elif module == "💧 STP Command Node":
    st.markdown("<h2 class='noc-header'>Sewage Treatment (STP) Digital Twin</h2>", unsafe_allow_html=True)
    
    stp_df = display_df[display_df["Type"] == "STP"]
    if stp_df.empty:
        st.warning("No STPs found matching your search.")
    else:
        target = st.selectbox("Establish Connection to STP Node:", stp_df["Name"].tolist())
        node = stp_df[stp_df["Name"] == target].iloc[0]
        
        st.markdown(f"**Uplink Established:** `{node['ID']}` | **Processing Load:** `{node['Capacity']} MLD` | **Compliance:** <span style='color:{node['Color']}; font-weight:bold;'>{node['Status'].upper()}</span>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 1, 1.5])
        with c1:
            st.subheader("Live Effluent Quality (BOD)")
            current_bod = 45 if node['Status'] == 'Critical' else random.randint(18, 28)
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = current_bod, title = {'text': "BOD (mg/l)"},
                gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#0f172a"},
                         'steps': [{'range': [0, 30], 'color': "#dcfce7"}, {'range': [30, 100], 'color': "#fee2e2"}],
                         'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 30}}
            ))
            fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="#ffffff")
            st.plotly_chart(fig_gauge, use_container_width=True)

        with c2:
            st.subheader("BOD Trend (Last 5 Mins)")
            times = [datetime.now() - timedelta(seconds=i*10) for i in range(30, -1, -1)]
            vals = [random.randint(35, 55) if node['Status'] == 'Critical' else random.randint(18, 28) for _ in range(31)]
            df_trend = pd.DataFrame({"Time": times, "BOD": vals}).set_index("Time")
            st.line_chart(df_trend, height=260, color="#2563eb")

        with c3:
            st.subheader("Live RTSP Uplink (UPJN)")
            st.components.v1.iframe("http://upjn.utplindia.in/Default/Home.aspx", height=280)

# --- 6. MODULE: BMW & HCF COMMAND NODE ---
elif module == "🏥 BMW & HCF Command Node":
    st.markdown("<h2 class='noc-header'>Bio-Medical Waste & Supply Chain Tracking</h2>", unsafe_allow_html=True)
    
    bmw_df = display_df[display_df["Type"] == "BMW"]
    if bmw_df.empty:
        st.warning("No CBWTFs found matching your search.")
    else:
        target = st.selectbox("Select Core CBWTF Node:", bmw_df["Name"].tolist())
        node = bmw_df[bmw_df["Name"] == target].iloc[0]
        
        # Filter HCFs connected to this BMW
        connected_hcfs = hcf_df[hcf_df["Parent_BMW_ID"] == node["ID"]]
        
        st.markdown(f"**Uplink:** `{node['ID']}` | **Status:** <span style='color:{node['Color']}; font-weight:bold;'>{node['Status'].upper()}</span> | **Connected Healthcare Facilities:** `{len(connected_hcfs)}`", unsafe_allow_html=True)
        st.markdown("---")
        
        map_col, data_col = st.columns([1.2, 1])
        
        with map_col:
            st.subheader(f"Service Catchment Area")
            # Create a combined dataframe for the map (The Plant + Its HCFs)
            map_nodes = pd.DataFrame([{"Name": node["Name"], "Lat": node["Lat"], "Lon": node["Lon"], "Role": "Processing Plant (CBWTF)", "Size": 15}])
            hcf_map_nodes = connected_hcfs[["Name", "Lat", "Lon"]].copy()
            hcf_map_nodes["Role"] = "Healthcare Facility (HCF)"
            hcf_map_nodes["Size"] = 5
            combined_map = pd.concat([map_nodes, hcf_map_nodes])
            
            fig = px.scatter_mapbox(combined_map, lat="Lat", lon="Lon", hover_name="Name", color="Role", size="Size",
                                    color_discrete_map={"Processing Plant (CBWTF)": "#dc2626", "Healthcare Facility (HCF)": "#2563eb"},
                                    zoom=9.5, height=450)
            fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)
            
        with data_col:
            st.subheader("HCF Daily Waste Manifest")
            selected_hcf = st.selectbox("Inspect Facility Data:", connected_hcfs["Name"].tolist())
            hcf_data = connected_hcfs[connected_hcfs["Name"] == selected_hcf].iloc[0]
            
            st.markdown(f"**Facility ID:** `{hcf_data['HCF_ID']}`")
            st.markdown(f"**Total Daily Generation:** `{hcf_data['Total_kg']} kg/day`")
            
            # Color-coded waste breakdown per CPCB guidelines
            st.markdown("#### Waste Segregation Matrix")
            w1, w2 = st.columns(2)
            w1.markdown(f"<div style='background-color:#fef08a; padding:10px; border-radius:5px; margin-bottom:10px; border-left: 5px solid #ca8a04;'>"
                        f"<b>🟡 YELLOW BAG</b><br><span class='waste-metric'>{hcf_data['Yellow_kg']} kg</span><br><small>Human Anatomical, Infectious</small></div>", unsafe_allow_html=True)
            w1.markdown(f"<div style='background-color:#ffffff; padding:10px; border-radius:5px; border: 1px solid #e2e8f0; border-left: 5px solid #94a3b8;'>"
                        f"<b>⚪ WHITE (Translucent)</b><br><span class='waste-metric'>{hcf_data['White_kg']} kg</span><br><small>Sharps, Needles, Scalpels</small></div>", unsafe_allow_html=True)
            
            w2.markdown(f"<div style='background-color:#fecaca; padding:10px; border-radius:5px; margin-bottom:10px; border-left: 5px solid #dc2626;'>"
                        f"<b>🔴 RED BAG</b><br><span class='waste-metric'>{hcf_data['Red_kg']} kg</span><br><small>Contaminated Plastics, Tubing</small></div>", unsafe_allow_html=True)
            w2.markdown(f"<div style='background-color:#bfdbfe; padding:10px; border-radius:5px; border-left: 5px solid #2563eb;'>"
                        f"<b>🔵 BLUE MARKING</b><br><span class='waste-metric'>{hcf_data['Blue_kg']} kg</span><br><small>Glassware, Metallic Implants</small></div>", unsafe_allow_html=True)

# --- 7. MODULE: ENFORCEMENT DESK ---
elif module == "⚖️ Enforcement Desk":
    st.markdown("<h2 class='noc-header'>Statutory Enforcement Engine</h2>", unsafe_allow_html=True)
    
    critical_nodes = display_df[display_df["Status"] == "Critical"]
    
    if critical_nodes.empty:
        st.success("✅ All displayed facilities are operating within UPPCB parameters. No enforcement actions required.")
    else:
        st.error(f"⚠️ {len(critical_nodes)} facilities require immediate statutory enforcement.")
        
        action_target = st.selectbox("Select Non-Compliant Facility:", critical_nodes["Name"].tolist())
        target_data = critical_nodes[critical_nodes["Name"] == action_target].iloc[0]
        
        c1, c2 = st.columns([1, 1.2])
        
        with c1:
            st.markdown("### AI Deviation Report")
            if target_data["Type"] == "STP":
                reason = "BOD effluent continuously exceeding 30 mg/l limit for the past 72 hours. Serious failure in biological treatment stage."
                act = "Section 33A of the Water (Prevention and Control of Pollution) Act, 1974"
            else:
                reason = "Secondary incineration chamber temperature recorded severely below 1050°C. Immediate risk of atmospheric Dioxin/Furan emissions."
                act = "Section 5 of the Environment (Protection) Act, 1986"
                
            st.markdown(f"**Facility:** {target_data['Name']} ({target_data['ID']})")
            st.markdown(f"**Infraction:** {reason}")
            st.markdown(f"**Statutory Provision:** `{act}`")
            
            st.markdown("---")
            if st.button("📨 SHOOT COMPLIANCE NOTICE", type="primary", use_container_width=True):
                with st.spinner("Authenticating credentials & dispatching via GoUP Exchange Server..."):
                    time.sleep(2)
                st.success(f"Official Notice successfully dispatched to {target_data['Name']} administration.")
                st.balloons()
                
        with c2:
            st.markdown("### Official Notice Preview")
            notice_text = f"""
            <div class='legal-notice'>
            <div style="text-align: center; margin-bottom: 20px;">
                <h3 style="margin:0; padding:0;">UTTAR PRADESH POLLUTION CONTROL BOARD</h3>
                <p style="margin:0; padding:0; font-size: 0.9em; color: #475569;">TC-12V, Vibhuti Khand, Gomti Nagar, Lucknow</p>
            </div>
            <hr style="border-top: 1px solid #000;">
            <b>Ref No:</b> UPPCB/ENF/2026/00{random.randint(100,999)}<br>
            <b>Date:</b> {datetime.now().strftime('%d-%b-%Y')}<br><br>
            <b>To,</b><br>
            The Plant Superintendent / Occupier,<br>
            <b>{target_data['Name']}</b>, {target_data['District']}<br><br>
            <b>Subject: Show Cause Notice for Non-Compliance under {act}.</b><br><br>
            <b>Sir/Madam,</b><br>
            Whereas, the Uttar Pradesh Pollution Control Board (UPPCB) has established a Centralized Real-Time Monitoring capability via OCEMS.<br><br>
            It has been automatically detected by our AI-Monitoring Engine that your facility (Node ID: {target_data['ID']}) is operating in severe violation of the prescribed environmental standards.<br><br>
            <b>Specific Anomaly Detected:</b> {reason}<br><br>
            You are hereby directed to rectify the operational failure within 48 hours and submit a detailed compliance report to the Regional Office, failing which, closure directions or environmental compensation will be levied without further notice.<br><br>
            <b>Digitally Signed,</b><br>
            Apex Command System<br>
            For Member Secretary, UPPCB
            </div>
            """
            st.markdown(notice_text, unsafe_allow_html=True)