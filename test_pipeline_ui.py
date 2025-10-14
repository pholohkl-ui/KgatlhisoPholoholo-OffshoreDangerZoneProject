
#  DANGER ZONE — Starter with Pipeline UI (5 types)


#  Imports
import streamlit as st
import numpy as np

#  Page setup
st.set_page_config(page_title="Danger Zone", page_icon="⚠️", layout="wide")
st.title("Gas Hydrate Formation Danger Zone — Offshore Pipeline Risk Model")

#  Pipeline profiles (ranges, weights, zone cutoffs)
PIPELINE_PROFILES = {
    "Gathering": {
        "P_range": (10, 80),  "T_range": (-5, 40),
        "weights": {"P":0.34, "T":0.40, "MEG":0.36, "S":0.12, "W":0.18},
        "cuts": (0.33, 0.66),
        "note": "Brings raw multiphase fluids (oil/gas/water) from wells to processing."
    },
    "Feeder": {
        "P_range": (20, 100), "T_range": (-5, 40),
        "weights": {"P":0.35, "T":0.40, "MEG":0.35, "S":0.14, "W":0.16},
        "cuts": (0.33, 0.66),
        "note": "Responsible for product movement from processing facilities to transmission pipelines."
    },
    "Flowline": {
        "P_range": (15, 100), "T_range": (-5, 40),
        "weights": {"P":0.35, "T":0.40, "MEG":0.35, "S":0.14, "W":0.16},
        "cuts": (0.33, 0.66),
        "note": "Production flowline (subsea); hydrate-prone."
    },
    "Transmission": {
        "P_range": (30, 150), "T_range": (-5, 40),
        "weights": {"P":0.38, "T":0.42, "MEG":0.32, "S":0.12, "W":0.12},
        "cuts": (0.35, 0.70),
        "note": "Midstream dry gas; hydrates negligible unless water ingress."
    },
    "Distribution": {
        "P_range": (1, 30),   "T_range": (-5, 40),
        "weights": {"P":0.28, "T":0.45, "MEG":0.35, "S":0.12, "W":0.12},
        "cuts": (0.30, 0.60),
        "note": "Local network delivering processed, dry natural gas to end users."
    },
}

#  Risk function (uses normalized variables per profile)
def profile_norm_and_risk(P, T, MEG, S, W, prof):
    Pmin, Pmax = prof["P_range"]; Tmin, Tmax = prof["T_range"]
    w = prof["weights"]

    # Normalize (guard divide-by-zero)
    Pn = (P - Pmin) / max(1e-6, (Pmax - Pmin))         # ↑P → ↑risk
    Tmid = (Tmin + Tmax) / 2.0
    Tn = (Tmid - T) / max(1e-6, (Tmid - Tmin))         # colder than mid → ↑risk
    Tn = float(np.clip(Tn, 0.0, 1.0))
    MEGn = MEG / 60.0                                  # ↑MEG → ↓risk
    Sn = S / 35000.0                                   # ↑salinity → ↑risk (mild)
    Wn = W / 80.0                                      # ↑water cut → ↑risk

    raw = w["P"]*Pn + w["T"]*Tn + w["S"]*Sn + w["W"]*Wn - w["MEG"]*MEGn
    return float(np.clip(raw, 0.0, 1.0))

#  Sidebar: choose pipeline class
with st.sidebar:
    st.header("Pipeline Class")
    pipeline_type = st.selectbox("Type", list(PIPELINE_PROFILES.keys()), index=0)
    st.caption(PIPELINE_PROFILES[pipeline_type]["note"])

profile = PIPELINE_PROFILES[pipeline_type]
Pmin, Pmax = profile["P_range"]; Tmin, Tmax = profile["T_range"]
lo, hi = profile["cuts"]

#  Pipeline UI — wet vs dry logic
dry_classes = {"Transmission", "Distribution"}
is_dry = pipeline_type in dry_classes

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Inputs")

    # Always show P & T
    P = st.slider("Pressure (bar)", int(Pmin), int(Pmax), int((Pmin+Pmax)//2))
    T = st.slider("Temperature (°C)", int(Tmin), int(Tmax), 15)

    if is_dry:
        st.info("Dry gas class — gas dehydrated to spec. Hydrate risk negligible unless water ingress occurs.")
        ingress = st.toggle("Simulate water ingress event?", value=False)
        MEG = st.slider("Inhibitor (MEG %)", 0, 60, 0)
        if ingress:
            with st.expander("Ingress parameters"):
                S = st.slider("Salinity (ppm)", 0, 35000, 5000)
                W = st.slider("Water Cut (%)", 0, 80, 5)
        else:
            S, W = 0, 0
    else:
        # Wet classes (Gathering / Feeder / Flowline)
        MEG = st.slider("Inhibitor (MEG %)", 0, 60, 10)
        with st.expander("Advanced factors"):
            S = st.slider("Salinity (ppm)", 0, 35000, 10000)
            W = st.slider("Water Cut (%)", 0, 80, 25)

#  Compute risk
risk = profile_norm_and_risk(P, T, MEG, S, W, profile)
if is_dry and not locals().get("ingress", False):
    risk *= 0.1  # damp risk for dry classes without ingress

zone = "✅ SAFE" if risk < lo else ("⚠️ WARNING" if risk < hi else "❌ DANGER")

with col2:
    st.subheader("Status")
    st.markdown(f"## {zone}")
    st.write(f"Risk index: **{int(risk*100)}/100**")
    st.progress(risk)

#  Footer / signature
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray;'>© 2025 Kgatlhiso L. Pholoholo — All rights reserved.</p>",
    unsafe_allow_html=True
)

with st.sidebar.expander("Model Disclaimer - Read"):
    st.write("""
    This simulation is a **conceptual hydrate risk model** inspired by data envelopes 
    from the **Petronius Oil Platform**, operated by Chevron and Marathon. 
    Petronius was chosen as a reference point, because it is a closed, well documented 
    project, making it ideal for academic modeling purposes.

    The pressure, temperature, and inhibitor ranges used here are **generalized** 
    from published offshore flow assurance studies and do not represent 
    exact field data for Petronius or any specific rig. 

    While *every oil platform differs* in size, depth, and operating conditions, 
    the thermodynamic logic and flow assurance concepts applied in this model 
    hold true across offshore production systems worldwide.


    """)
