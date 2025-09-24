import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Wood Firing Toolkit", page_icon="🔥", layout="wide")

if "log" not in st.session_state:
    st.session_state.log = []
if "crew" not in st.session_state:
    st.session_state.crew = []
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "kilnmap" not in st.session_state:
    st.session_state.kilnmap = pd.DataFrame(
        [["" for _ in range(6)] for _ in range(4)],
        columns=[f"Col {i+1}" for i in range(6)]
    )
if "timer_end" not in st.session_state:
    st.session_state.timer_end = None

st.title("Wood Firing Toolkit")
st.caption("MVP for potters who do wood firing")

# Sidebar controls
with st.sidebar:
    st.header("Session")
    kiln_name = st.text_input("Kiln name", value="Ana")
    firing_id = st.text_input("Firing ID", value=datetime.now().strftime("%Y%m%d-%H%M"))
    st.markdown("Use the tabs to log, time stokes, manage crew, map the kiln, and track wood.")

# Tabs
log_tab, timer_tab, crew_tab, map_tab, inv_tab, export_tab = st.tabs([
    "Firing Log", "Stoke Timer", "Crew", "Kiln Map", "Wood Inventory", "Export"
])

# Firing Log
with log_tab:
    st.subheader("Log an observation")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        t_now = st.datetime_input("Time", value=datetime.now())
    with col2:
        temp = st.number_input("Temp F", min_value=60, max_value=2600, value=900, step=5)
    with col3:
        cones = st.text_input("Cones movement", value="5 soft")
    with col4:
        o2 = st.selectbox("Atmosphere", ["neutral", "oxidation", "reduction", "heavy reduction"]) 
    notes = st.text_area("Notes", placeholder="Stoke, damper, spyhole, color, sound")
    add = st.button("Add log entry")
    if add:
        st.session_state.log.append({
            "kiln": kiln_name,
            "firing_id": firing_id,
            "time": t_now.strftime("%Y-%m-%d %H:%M:%S"),
            "temp_F": temp,
            "cones": cones,
            "atmosphere": o2,
            "notes": notes
        })
        st.success("Entry added")

    if st.session_state.log:
        df = pd.DataFrame(st.session_state.log)
        df_sorted = df.sort_values("time")
        st.dataframe(df_sorted, use_container_width=True)
        st.line_chart(df_sorted.set_index("time")["temp_F"])  # simple temp trend

# Stoke Timer
with timer_tab:
    st.subheader("Stoke interval timer")
    colA, colB, colC = st.columns(3)
    with colA:
        interval = st.number_input("Interval minutes", min_value=1, max_value=60, value=7)
    with colB:
        if st.button("Start"):
            st.session_state.timer_end = datetime.now() + timedelta(minutes=interval)
    with colC:
        if st.button("Stop"):
            st.session_state.timer_end = None

    if st.session_state.timer_end:
        remaining = st.session_state.timer_end - datetime.now()
        secs = max(int(remaining.total_seconds()), 0)
        m, s = divmod(secs, 60)
        st.metric("Time to next stoke", f"{m:02d}:{s:02d}")
        if secs == 0:
            st.warning("Stoke now")
    else:
        st.info("Timer idle")

# Crew
with crew_tab:
    st.subheader("Crew board")
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("Name", key="crew_name")
    with c2:
        role = st.selectbox("Role", ["lead", "stoker", "spotter", "wood", "float"], key="crew_role")
    with c3:
        start = st.time_input("On shift", key="crew_start")
    addc = st.button("Add crew member")
    if addc and name:
        st.session_state.crew.append({"name": name, "role": role, "on_shift": str(start)})
        st.success("Crew updated")
    if st.session_state.crew:
        st.dataframe(pd.DataFrame(st.session_state.crew), use_container_width=True)

# Kiln Map
with map_tab:
    st.subheader("Kiln map grid")
    st.caption("Click cells to enter cone or test tile info")
    edited = st.data_editor(st.session_state.kilnmap, use_container_width=True, num_rows="dynamic")
    st.session_state.kilnmap = edited

# Wood Inventory
with inv_tab:
    st.subheader("Wood tracking")
    colw1, colw2, colw3, colw4 = st.columns(4)
    with colw1:
        species = st.text_input("Species", value="pine")
    with colw2:
        cords = st.number_input("Cords", min_value=0.0, step=0.1, value=0.5)
    with colw3:
        mc = st.number_input("Moisture percent", min_value=0, max_value=100, value=20)
    with colw4:
        loc = st.text_input("Location", value="shed A")
    addw = st.button("Add inventory")
    if addw:
        st.session_state.inventory.append({
            "species": species,
            "cords": cords,
            "moisture_pct": mc,
            "location": loc
        })
        st.success("Wood added")
    if st.session_state.inventory:
        st.dataframe(pd.DataFrame(st.session_state.inventory), use_container_width=True)

# Export
with export_tab:
    st.subheader("Export data")
    log_df = pd.DataFrame(st.session_state.log) if st.session_state.log else pd.DataFrame()
    crew_df = pd.DataFrame(st.session_state.crew) if st.session_state.crew else pd.DataFrame()
    inv_df = pd.DataFrame(st.session_state.inventory) if st.session_state.inventory else pd.DataFrame()
    map_df = st.session_state.kilnmap.copy()

    colx1, colx2, colx3, colx4 = st.columns(4)
    with colx1:
        st.download_button("Download log CSV", log_df.to_csv(index=False).encode("utf-8"), "firing_log.csv", "text/csv")
    with colx2:
        st.download_button("Download crew CSV", crew_df.to_csv(index=False).encode("utf-8"), "crew.csv", "text/csv")
    with colx3:
        st.download_button("Download wood CSV", inv_df.to_csv(index=False).encode("utf-8"), "wood.csv", "text/csv")
    with colx4:
        st.download_button("Download kiln map CSV", map_df.to_csv(index=False).encode("utf-8"), "kiln_map.csv", "text/csv")

st.caption("Built with Streamlit. Save your CSV files after each session.")

