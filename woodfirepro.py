import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="WoodFirePro", page_icon="🔥", layout="wide")

# Initialize session state
if "log" not in st.session_state:
    st.session_state.log = []
if "crew" not in st.session_state:
    st.session_state.crew = []
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "timer_end" not in st.session_state:
    st.session_state.timer_end = None
if "firing_phase" not in st.session_state:
    st.session_state.firing_phase = "heating"

st.title("🔥 WoodFirePro")
st.caption("Professional wood firing toolkit - inspired by real potter workflows")

# Sidebar controls
with st.sidebar:
    st.header("🎯 Session Info")
    kiln_name = st.text_input("Kiln name", value="Ana")
    firing_id = st.text_input("Firing ID", value=datetime.now().strftime("%Y%m%d-%H%M"))
    
    st.header("🔥 Firing Phase")
    phase = st.selectbox("Current Phase", 
                        ["heating", "body_reduction", "glaze_maturation", "cooling", "finished"],
                        index=["heating", "body_reduction", "glaze_maturation", "cooling", "finished"].index(st.session_state.firing_phase))
    st.session_state.firing_phase = phase
    
    # Quick stats if we have data
    if st.session_state.log:
        df = pd.DataFrame(st.session_state.log)
        latest = df.iloc[-1]
        st.metric("Latest Temp", f"{latest.get('temp_front', 0)}°F")
        st.metric("Last Entry", latest['time'].split()[1] if len(latest['time'].split()) > 1 else latest['time'])

# Main tabs
log_tab, analysis_tab, timer_tab, cones_tab, crew_tab, export_tab = st.tabs([
    "📝 Firing Log", "📊 Analysis", "⏲️ Timer", "🎯 Cone Tracker", "👥 Crew", "💾 Export"
])

# Enhanced Firing Log
with log_tab:
    st.subheader("📝 Log Entry")
    
    # Time and basic info
    col1, col2 = st.columns(2)
    with col1:
        t_now = st.datetime_input("Time", value=datetime.now())
    with col2:
        entry_type = st.selectbox("Entry Type", ["observation", "stoke", "damper_change", "problem", "milestone"])
    
    # Multiple temperature readings
    st.subheader("🌡️ Temperature Readings")
    temp_col1, temp_col2, temp_col3 = st.columns(3)
    with temp_col1:
        temp_front = st.number_input("Front spy (°F)", min_value=60, max_value=2600, value=900, step=5)
    with temp_col2:
        temp_middle = st.number_input("Middle spy (°F)", min_value=60, max_value=2600, value=900, step=5)
    with temp_col3:
        temp_back = st.number_input("Back spy (°F)", min_value=60, max_value=2600, value=900, step=5)
    
    # Enhanced atmosphere controls
    st.subheader("💨 Atmosphere & Controls")
    atm_col1, atm_col2, atm_col3 = st.columns(3)
    with atm_col1:
        atmosphere = st.selectbox("Atmosphere", 
                                 ["neutral", "light_oxidation", "oxidation", "light_reduction", "reduction", "heavy_reduction"])
    with atm_col2:
        damper_position = st.slider("Damper Position", 0, 100, 50, help="0 = closed, 100 = fully open")
    with atm_col3:
        fuel_type = st.selectbox("Primary Fuel", ["wood", "gas", "wood+gas", "coasting"])
    
    # Flame and color observations
    st.subheader("👁️ Visual Observations")
    vis_col1, vis_col2 = st.columns(2)
    with vis_col1:
        flame_color = st.text_input("Flame Color/Character", placeholder="e.g., orange lazy flames, blue/white active")
    with vis_col2:
        spy_color = st.text_input("Spy Hole Color", placeholder="e.g., bright orange, cherry red, white heat")
    
    # Action taken
    action_taken = st.text_area("Action Taken", placeholder="e.g., Added 2 splits pine, closed damper 1/4, increased air")
    
    # General notes
    notes = st.text_area("Additional Notes", placeholder="Observations, decisions, problems, milestones...")
    
    # Add entry button
    if st.button("➕ Add Log Entry", type="primary"):
        entry = {
            "kiln": kiln_name,
            "firing_id": firing_id,
            "time": t_now.strftime("%Y-%m-%d %H:%M:%S"),
            "phase": phase,
            "entry_type": entry_type,
            "temp_front": temp_front,
            "temp_middle": temp_middle,
            "temp_back": temp_back,
            "atmosphere": atmosphere,
            "damper_position": damper_position,
            "fuel_type": fuel_type,
            "flame_color": flame_color,
            "spy_color": spy_color,
            "action_taken": action_taken,
            "notes": notes
        }
        st.session_state.log.append(entry)
        st.success("✅ Entry added successfully!")
        st.rerun()

    # Display recent entries
    if st.session_state.log:
        st.subheader("📋 Recent Entries")
        df = pd.DataFrame(st.session_state.log)
        df_display = df.sort_values("time", ascending=False).head(10)
        
        # Create a more readable display
        for _, row in df_display.iterrows():
            with st.expander(f"{row['time']} - {row['entry_type'].title()} ({row['temp_front']}°F)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Temps:** F:{row['temp_front']}° M:{row['temp_middle']}° B:{row['temp_back']}°")
                    st.write(f"**Atmosphere:** {row['atmosphere']} (Damper: {row['damper_position']}%)")
                    st.write(f"**Fuel:** {row['fuel_type']}")
                with col2:
                    if row['flame_color']:
                        st.write(f"**Flame:** {row['flame_color']}")
                    if row['spy_color']:
                        st.write(f"**Spy Hole:** {row['spy_color']}")
                    if row['action_taken']:
                        st.write(f"**Action:** {row['action_taken']}")
                if row['notes']:
                    st.write(f"**Notes:** {row['notes']}")

# Analysis Tab
with analysis_tab:
    if st.session_state.log and len(st.session_state.log) > 1:
        df = pd.DataFrame(st.session_state.log)
        df['datetime'] = pd.to_datetime(df['time'])
        df = df.sort_values('datetime')
        
        # Multi-temperature chart
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Temperature Progress', 'Atmosphere & Damper'),
            vertical_spacing=0.1
        )
        
        # Temperature traces
        fig.add_trace(
            go.Scatter(x=df['datetime'], y=df['temp_front'], name='Front Spy', line=dict(color='red')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['datetime'], y=df['temp_middle'], name='Middle Spy', line=dict(color='orange')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['datetime'], y=df['temp_back'], name='Back Spy', line=dict(color='yellow')),
            row=1, col=1
        )
        
        # Damper position
        fig.add_trace(
            go.Scatter(x=df['datetime'], y=df['damper_position'], name='Damper %', line=dict(color='blue')),
            row=2, col=1
        )
        
        fig.update_layout(height=600, title="Firing Analysis")
        fig.update_yaxes(title_text="Temperature (°F)", row=1, col=1)
        fig.update_yaxes(title_text="Damper Position (%)", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Phase analysis
        st.subheader("📊 Firing Statistics")
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        with stats_col1:
            st.metric("Duration", f"{(df['datetime'].max() - df['datetime'].min()).total_seconds() / 3600:.1f} hrs")
        with stats_col2:
            st.metric("Max Temp", f"{df[['temp_front', 'temp_middle', 'temp_back']].max().max():.0f}°F")
        with stats_col3:
            st.metric("Avg Climb Rate", f"{(df[['temp_front', 'temp_middle', 'temp_back']].max().max() - df[['temp_front', 'temp_middle', 'temp_back']].min().min()) / ((df['datetime'].max() - df['datetime'].min()).total_seconds() / 3600):.0f}°F/hr")
        with stats_col4:
            reduction_pct = (df['atmosphere'].str.contains('reduction').sum() / len(df) * 100)
            st.metric("Reduction Time", f"{reduction_pct:.0f}%")
    else:
        st.info("Add some log entries to see analysis charts and statistics.")

# Enhanced Timer
with timer_tab:
    st.subheader("⏲️ Stoke Timer")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        interval = st.number_input("Interval (minutes)", min_value=1, max_value=120, value=15)
    with col2:
        if st.button("🔥 Start Timer"):
            st.session_state.timer_end = datetime.now() + timedelta(minutes=interval)
    with col3:
        if st.button("⏹️ Stop Timer"):
            st.session_state.timer_end = None
    
    if st.session_state.timer_end:
        remaining = st.session_state.timer_end - datetime.now()
        secs = max(int(remaining.total_seconds()), 0)
        m, s = divmod(secs, 60)
        
        if secs > 0:
            st.metric("⏰ Time to next stoke", f"{m:02d}:{s:02d}")
            # Auto-refresh every second
            st.rerun()
        else:
            st.error("🚨 STOKE NOW! 🚨")
            # Auto-stop timer when it hits zero
            st.session_state.timer_end = None
    else:
        st.info("⏸️ Timer idle - Click 'Start Timer' when you're ready")

# Cone Tracker Tab
with cones_tab:
    st.subheader("🎯 Cone Movement Tracker")
    st.caption("Track cone progression across different areas of your kiln")
    
    # Cone tracking would be a more sophisticated grid here
    # For now, simple tracking
    cone_areas = ["Front Bottom", "Front Top", "Middle Bottom", "Middle Top", "Back Bottom", "Back Top"]
    common_cones = ["08", "06", "04", "03", "1", "3", "5", "6", "7", "8", "9", "10", "11", "12"]
    
    st.write("Quick cone status entry:")
    cone_col1, cone_col2, cone_col3, cone_col4 = st.columns(4)
    with cone_col1:
        cone_area = st.selectbox("Kiln Area", cone_areas)
    with cone_col2:
        cone_number = st.selectbox("Cone Number", common_cones)
    with cone_col3:
        cone_status = st.selectbox("Status", ["standing", "soft", "bending", "bent", "down", "overfired"])
    with cone_col4:
        if st.button("Add Cone Status"):
            st.success(f"Cone {cone_number} in {cone_area}: {cone_status}")

# Crew tab (simplified from original)
with crew_tab:
    st.subheader("👥 Crew Management")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("Name")
    with col2:
        role = st.selectbox("Role", ["lead", "stoker", "spotter", "wood_prep", "floater", "observer"])
    with col3:
        shift_start = st.time_input("Shift Start")
    
    if st.button("Add Crew Member") and name:
        st.session_state.crew.append({"name": name, "role": role, "shift_start": str(shift_start)})
        st.success(f"Added {name} as {role}")
    
    if st.session_state.crew:
        crew_df = pd.DataFrame(st.session_state.crew)
        st.dataframe(crew_df, use_container_width=True)

# Export tab
with export_tab:
    st.subheader("💾 Export Data")
    
    if st.session_state.log:
        log_df = pd.DataFrame(st.session_state.log)
        csv = log_df.to_csv(index=False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download Full Firing Log",
                csv.encode('utf-8'),
                f"{kiln_name}_{firing_id}_complete_log.csv",
                "text/csv"
            )
        with col2:
            # Summary export
            summary_data = {
                "firing_id": firing_id,
                "kiln": kiln_name,
                "phase": phase,
                "start_time": log_df['time'].min() if not log_df.empty else "",
                "end_time": log_df['time'].max() if not log_df.empty else "",
                "max_temp": log_df[['temp_front', 'temp_middle', 'temp_back']].max().max() if not log_df.empty else 0,
                "total_entries": len(log_df)
            }
            summary_csv = pd.DataFrame([summary_data]).to_csv(index=False)
            st.download_button(
                "📋 Download Summary",
                summary_csv.encode('utf-8'),
                f"{kiln_name}_{firing_id}_summary.csv",
                "text/csv"
            )
    else:
        st.info("No firing data to export yet. Start logging to enable export.")

# Footer
st.markdown("---")
st.caption("🔥 WoodFirePro - Built for potters, by potters. Save your data regularly!")
