import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="WoodFirePro", page_icon="🔥", layout="wide")

# Initialize session state
if "log" not in st.session_state:
    st.session_state.log = []
if "crew" not in st.session_state:
    st.session_state.crew = []
if "wood_log" not in st.session_state:
    st.session_state.wood_log = []
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "cone_status" not in st.session_state:
    # Initialize cone tracking grid - 6 rows x 8 columns for typical kiln
    st.session_state.cone_status = {}
    for row in range(6):
        for col in range(8):
            st.session_state.cone_status[f"{row}_{col}"] = {"cones": {}, "last_updated": None}
if "timer_end" not in st.session_state:
    st.session_state.timer_end = None
if "firing_phase" not in st.session_state:
    st.session_state.firing_phase = "heating"
if "active_user" not in st.session_state:
    st.session_state.active_user = "Kiln Master"

st.title("🔥 WoodFirePro")
st.caption("Professional wood firing toolkit - built for real potters")

# Sidebar controls
with st.sidebar:
    st.header("🎯 Session Info")
    kiln_name = st.text_input("Kiln name", value="Ana")
    firing_id = st.text_input("Firing ID", value=datetime.now().strftime("%Y%m%d-%H%M"))
    
    st.header("👤 Active User")
    active_user = st.text_input("Your Name", value=st.session_state.active_user)
    st.session_state.active_user = active_user
    
    st.header("🔥 Firing Phase")
    phase = st.selectbox("Current Phase", 
                        ["heating", "water_smoking", "dehydration", "body_reduction", "glaze_maturation", "flash", "cooling", "finished"],
                        index=["heating", "water_smoking", "dehydration", "body_reduction", "glaze_maturation", "flash", "cooling", "finished"].index(st.session_state.firing_phase))
    st.session_state.firing_phase = phase
    
    # Live stats
    if st.session_state.log:
        df = pd.DataFrame(st.session_state.log)
        latest = df.iloc[-1]
        st.metric("Latest Temp (Front)", f"{latest.get('temp_front', 0)}°F")
        st.metric("Last Entry By", latest.get('logged_by', 'Unknown'))
        st.metric("Firing Duration", f"{(pd.to_datetime(df['time']).max() - pd.to_datetime(df['time']).min()).total_seconds() / 3600:.1f} hrs")
    
    # Current crew on duty
    if st.session_state.crew:
        st.header("👥 Current Crew")
        crew_df = pd.DataFrame(st.session_state.crew)
        for _, member in crew_df.iterrows():
            st.write(f"**{member['name']}** - {member['role']}")

# Main tabs
log_tab, wood_tab, analysis_tab, timer_tab, cones_tab, crew_tab, export_tab, about_tab = st.tabs([
    "📝 Firing Log", "🪵 Wood Tracker", "📊 Analysis", "⏲️ Timer", "🎯 Cone Map", "👥 Crew", "💾 Export", "ℹ️ About"
])

# Enhanced Firing Log
with log_tab:
    st.subheader("📝 New Log Entry")
    
    # Time and basic info
    col1, col2, col3 = st.columns(3)
    with col1:
        t_date = st.date_input("Date", value=datetime.now().date())
        t_time = st.time_input("Time", value=datetime.now().time())
        t_now = datetime.combine(t_date, t_time)
    with col2:
        entry_type = st.selectbox("Entry Type", 
                                 ["observation", "stoke", "damper_change", "door_brick", "problem", "milestone", "shift_change"])
    with col3:
        st.write(f"**Logging as:** {active_user}")
    
    # Multiple temperature readings
    st.subheader("🌡️ Temperature Readings")
    temp_col1, temp_col2, temp_col3, temp_col4 = st.columns(4)
    with temp_col1:
        temp_front = st.number_input("Front spy (°F)", min_value=60, max_value=2600, value=900, step=5)
    with temp_col2:
        temp_middle = st.number_input("Middle spy (°F)", min_value=60, max_value=2600, value=900, step=5)
    with temp_col3:
        temp_back = st.number_input("Back spy (°F)", min_value=60, max_value=2600, value=900, step=5)
    with temp_col4:
        temp_stack = st.number_input("Stack temp (°F)", min_value=60, max_value=2600, value=400, step=5)
    
    # Enhanced atmosphere controls
    st.subheader("💨 Atmosphere & Controls")
    atm_col1, atm_col2, atm_col3, atm_col4 = st.columns(4)
    with atm_col1:
        atmosphere = st.selectbox("Atmosphere", 
                                 ["neutral", "light_oxidation", "oxidation", "light_reduction", "reduction", "heavy_reduction"])
    with atm_col2:
        damper_position = st.slider("Damper Position", 0, 100, 50, help="0 = closed, 100 = fully open")
    with atm_col3:
        air_intake = st.slider("Primary Air", 0, 100, 50, help="Primary air intake %")
    with atm_col4:
        fuel_type = st.selectbox("Primary Fuel", ["wood_only", "gas_only", "wood+gas", "coasting"])
    
    # Flame and color observations
    st.subheader("👁️ Visual Observations")
    vis_col1, vis_col2, vis_col3 = st.columns(3)
    with vis_col1:
        flame_color = st.text_input("Flame Character", placeholder="e.g., orange lazy flames, blue/white tips")
    with vis_col2:
        spy_color = st.text_input("Spy Hole Colors", placeholder="e.g., bright orange, cherry red, white heat")
    with vis_col3:
        draft_sound = st.text_input("Draft/Sound", placeholder="e.g., roaring, whistling, quiet")
    
    # Action taken
    action_taken = st.text_area("Action Taken", placeholder="e.g., Added 2 splits oak, closed damper 1/4, pulled door brick")
    
    # General notes
    notes = st.text_area("Notes & Observations", placeholder="Problems, decisions, atmospheric conditions, crew changes...")
    
    # Add entry button
    if st.button("➕ Add Log Entry", type="primary"):
        entry = {
            "kiln": kiln_name,
            "firing_id": firing_id,
            "time": t_now.strftime("%Y-%m-%d %H:%M:%S"),
            "logged_by": active_user,
            "phase": phase,
            "entry_type": entry_type,
            "temp_front": temp_front,
            "temp_middle": temp_middle,
            "temp_back": temp_back,
            "temp_stack": temp_stack,
            "atmosphere": atmosphere,
            "damper_position": damper_position,
            "air_intake": air_intake,
            "fuel_type": fuel_type,
            "flame_color": flame_color,
            "spy_color": spy_color,
            "draft_sound": draft_sound,
            "action_taken": action_taken,
            "notes": notes
        }
        st.session_state.log.append(entry)
        st.success(f"✅ Entry logged by {active_user}")
        st.rerun()

    # Display recent entries with better formatting
    if st.session_state.log:
        st.subheader("📋 Recent Entries")
        df = pd.DataFrame(st.session_state.log)
        df_display = df.sort_values("time", ascending=False).head(8)
        
        for i, (_, row) in enumerate(df_display.iterrows()):
            # Color-code by entry type
            entry_colors = {
                "observation": "🔍", "stoke": "🔥", "damper_change": "💨", 
                "door_brick": "🧱", "problem": "⚠️", "milestone": "🎯", "shift_change": "👥"
            }
            icon = entry_colors.get(row['entry_type'], "📝")
            
            with st.expander(f"{icon} {row['time']} - {row['entry_type'].replace('_', ' ').title()} by {row.get('logged_by', 'Unknown')} ({row['temp_front']}°F)"):
                temp_col, atm_col = st.columns(2)
                with temp_col:
                    st.write(f"**Temps:** F:{row['temp_front']}° M:{row['temp_middle']}° B:{row['temp_back']}° Stack:{row['temp_stack']}°")
                    if row['flame_color']:
                        st.write(f"**Flame:** {row['flame_color']}")
                    if row['spy_color']:
                        st.write(f"**Spy Holes:** {row['spy_color']}")
                    if row['draft_sound']:
                        st.write(f"**Draft:** {row['draft_sound']}")
                with atm_col:
                    st.write(f"**Atmosphere:** {row['atmosphere']}")
                    st.write(f"**Damper:** {row['damper_position']}% | **Air:** {row['air_intake']}%")
                    st.write(f"**Fuel:** {row['fuel_type']}")
                    if row['action_taken']:
                        st.write(f"**Action:** {row['action_taken']}")
                if row['notes']:
                    st.write(f"**Notes:** {row['notes']}")

# Wood Consumption Tracker
with wood_tab:
    st.subheader("🪵 Active Wood Consumption")
    st.caption("Track wood as it goes into the kiln - not just inventory")
    
    # Quick wood logging
    wood_col1, wood_col2, wood_col3, wood_col4, wood_col5 = st.columns(5)
    with wood_col1:
        wood_time = st.time_input("Time Used", value=datetime.now().time())
    with wood_col2:
        wood_species = st.selectbox("Species", ["pine", "oak", "hardwood_mix", "softwood_mix", "cherry", "maple", "ash", "hickory", "other"])
    with wood_col3:
        wood_size = st.selectbox("Size", ["kindling", "small_split", "medium_split", "large_split", "chunk", "slab"])
    with wood_col4:
        wood_quantity = st.number_input("Pieces", min_value=1, max_value=50, value=2)
    with wood_col5:
        wood_location = st.selectbox("Firebox", ["primary", "secondary", "side_stoke", "all"])
    
    wood_notes = st.text_input("Wood Notes", placeholder="e.g., very dry, some bark, perfect for reduction")
    
    if st.button("🔥 Log Wood Consumption"):
        wood_entry = {
            "time": f"{datetime.now().strftime('%Y-%m-%d')} {wood_time}",
            "logged_by": active_user,
            "species": wood_species,
            "size": wood_size,
            "quantity": wood_quantity,
            "location": wood_location,
            "notes": wood_notes,
            "firing_id": firing_id
        }
        st.session_state.wood_log.append(wood_entry)
        st.success(f"✅ Logged {wood_quantity} {wood_size} {wood_species} to {wood_location}")
    
    # Wood consumption summary
    if st.session_state.wood_log:
        st.subheader("📊 Today's Wood Consumption")
        wood_df = pd.DataFrame(st.session_state.wood_log)
        
        # Summary stats
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        with summary_col1:
            total_pieces = wood_df['quantity'].sum()
            st.metric("Total Pieces", total_pieces)
        with summary_col2:
            species_variety = wood_df['species'].nunique()
            st.metric("Species Used", species_variety)
        with summary_col3:
            last_stoke = wood_df.iloc[-1]['time'] if not wood_df.empty else "None"
            st.metric("Last Stoke", last_stoke.split()[1] if len(last_stoke.split()) > 1 else last_stoke)
        
        # Recent wood entries
        st.subheader("🪵 Recent Wood Usage")
        recent_wood = wood_df.tail(10).sort_values('time', ascending=False)
        for _, wood in recent_wood.iterrows():
            st.write(f"**{wood['time']}** - {wood['quantity']} {wood['size']} {wood['species']} → {wood['location']} *(by {wood['logged_by']})*")
    
    # Traditional inventory section
    st.subheader("📦 Wood Inventory Management")
    inv_col1, inv_col2, inv_col3, inv_col4 = st.columns(4)
    with inv_col1:
        inv_species = st.text_input("Species", value="oak", key="inv_species")
    with inv_col2:
        inv_cords = st.number_input("Cords", min_value=0.0, step=0.1, value=0.5, key="inv_cords")
    with inv_col3:
        inv_mc = st.number_input("Moisture %", min_value=0, max_value=100, value=18, key="inv_mc")
    with inv_col4:
        inv_loc = st.text_input("Storage Location", value="shed A", key="inv_loc")
    
    if st.button("Add to Inventory"):
        st.session_state.inventory.append({
            "species": inv_species,
            "cords": inv_cords,
            "moisture_pct": inv_mc,
            "location": inv_loc,
            "added_date": datetime.now().strftime("%Y-%m-%d")
        })
        st.success("Added to inventory")
    
    if st.session_state.inventory:
        st.dataframe(pd.DataFrame(st.session_state.inventory), use_container_width=True)

# Analysis Tab - Enhanced
with analysis_tab:
    if st.session_state.log and len(st.session_state.log) > 1:
        df = pd.DataFrame(st.session_state.log)
        df['datetime'] = pd.to_datetime(df['time'])
        df = df.sort_values('datetime')
        df_chart = df.set_index('datetime')
        
        # Temperature Progress Chart
        st.subheader("🌡️ Temperature Progress (All Sensors)")
        temp_chart_data = df_chart[['temp_front', 'temp_middle', 'temp_back', 'temp_stack']].copy()
        temp_chart_data.columns = ['Front Spy', 'Middle Spy', 'Back Spy', 'Stack']
        st.line_chart(temp_chart_data)
        
        # Atmosphere Control Chart
        st.subheader("💨 Atmosphere Control")
        control_chart_data = df_chart[['damper_position', 'air_intake']].copy()
        control_chart_data.columns = ['Damper Position %', 'Air Intake %']
        st.line_chart(control_chart_data)
        
        # Wood Consumption Chart if available
        if st.session_state.wood_log:
            st.subheader("🪵 Wood Consumption Rate")
            wood_df = pd.DataFrame(st.session_state.wood_log)
            wood_df['datetime'] = pd.to_datetime(wood_df['time'])
            wood_df = wood_df.sort_values('datetime')
            
            # Create cumulative wood consumption
            wood_df['cumulative_pieces'] = wood_df['quantity'].cumsum()
            wood_chart_data = wood_df.set_index('datetime')[['cumulative_pieces']].copy()
            wood_chart_data.columns = ['Total Wood Pieces Used']
            st.line_chart(wood_chart_data)
        
        # Atmosphere distribution
        st.subheader("🔥 Atmosphere Distribution")
        atmosphere_counts = df['atmosphere'].value_counts()
        st.bar_chart(atmosphere_counts)
        
        # Enhanced statistics
        st.subheader("📊 Firing Statistics")
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        with stats_col1:
            duration = (df['datetime'].max() - df['datetime'].min()).total_seconds() / 3600
            st.metric("Total Duration", f"{duration:.1f} hrs")
        with stats_col2:
            max_temp = df[['temp_front', 'temp_middle', 'temp_back']].max().max()
            st.metric("Peak Temperature", f"{max_temp:.0f}°F")
        with stats_col3:
            temp_range = df[['temp_front', 'temp_middle', 'temp_back']].max() - df[['temp_front', 'temp_middle', 'temp_back']].min()
            avg_variance = temp_range.mean()
            st.metric("Avg Temp Variance", f"{avg_variance:.0f}°F")
        with stats_col4:
            total_entries = len(df)
            avg_interval = duration * 60 / max(total_entries - 1, 1)  # minutes between entries
            st.metric("Avg Entry Interval", f"{avg_interval:.0f} min")
    else:
        st.info("📈 Add multiple log entries to see detailed analysis charts.")

# Enhanced Timer with Phase Awareness
with timer_tab:
    st.subheader("⏲️ Firing Timer")
    
    # Phase-aware default intervals
    phase_intervals = {
        "heating": 15, "water_smoking": 20, "dehydration": 15,
        "body_reduction": 10, "glaze_maturation": 8, "flash": 5,
        "cooling": 30, "finished": 60
    }
    default_interval = phase_intervals.get(phase, 15)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        interval = st.number_input("Interval (minutes)", min_value=1, max_value=120, 
                                  value=default_interval, 
                                  help=f"Suggested for {phase}: {default_interval} min")
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
            st.metric("⏰ Time to next check", f"{m:02d}:{s:02d}")
            # Progress bar
            total_secs = interval * 60
            elapsed_secs = total_secs - secs
            progress = elapsed_secs / total_secs
            st.progress(progress)
            st.rerun()
        else:
            st.error("🚨 TIME TO CHECK KILN! 🚨")
            st.balloons()  # Visual alert
            st.session_state.timer_end = None
    else:
        st.info(f"⏸️ Timer idle - Suggested interval for {phase} phase: {default_interval} minutes")

# Visual Kiln Map for Cone Tracking
with cones_tab:
    st.subheader("🎯 Interactive Kiln Cone Map")
    st.caption("Click grid positions to update cone status. Visual representation of your kiln interior.")
    
    # Cone selection controls
    cone_col1, cone_col2, cone_col3 = st.columns(3)
    with cone_col1:
        selected_cone = st.selectbox("Cone Number", ["08", "06", "04", "03", "01", "1", "3", "5", "6", "7", "8", "9", "10", "11", "12"])
    with cone_col2:
        cone_status = st.selectbox("Status", ["standing", "soft", "bending", "bent", "down", "overfired"])
    with cone_col3:
        st.write(f"**Updating as:** {active_user}")
    
    # Visual kiln grid (6 rows x 8 columns)
    st.subheader("Kiln Interior View (Front to Back)")
    
    # Create visual grid
    for row in range(6):
        cols = st.columns(8)
        for col in range(8):
            position_key = f"{row}_{col}"
            
            with cols[col]:
                # Get current status for this position
                position_data = st.session_state.cone_status.get(position_key, {"cones": {}, "last_updated": None})
                
                # Create a summary display
                if position_data["cones"]:
                    # Show the most advanced cone status
                    cone_summary = []
                    for cone_num, status in position_data["cones"].items():
                        if status in ["bent", "down", "overfired"]:
                            cone_summary.append(f"🔴 {cone_num}")
                        elif status in ["bending", "soft"]:
                            cone_summary.append(f"🟡 {cone_num}")
                        else:
                            cone_summary.append(f"⚪ {cone_num}")
                    display_text = "\n".join(cone_summary)
                else:
                    display_text = "Empty"
                
                # Button for this position
                if st.button(f"R{row+1}C{col+1}", key=f"pos_{row}_{col}", help=display_text):
                    # Update the position
                    if position_key not in st.session_state.cone_status:
                        st.session_state.cone_status[position_key] = {"cones": {}, "last_updated": None}
                    
                    st.session_state.cone_status[position_key]["cones"][selected_cone] = cone_status
                    st.session_state.cone_status[position_key]["last_updated"] = f"{datetime.now().strftime('%H:%M')} by {active_user}"
                    st.success(f"Updated R{row+1}C{col+1}: Cone {selected_cone} = {cone_status}")
                    st.rerun()
                
                # Show current status
                if position_data["cones"]:
                    st.caption(display_text.replace('\n', ' | '))
    
    # Cone status legend
    st.subheader("📋 Cone Status Legend")
    legend_col1, legend_col2 = st.columns(2)
    with legend_col1:
        st.write("🔴 Bent/Down/Overfired")
        st.write("🟡 Bending/Soft")
        st.write("⚪ Standing")
    with legend_col2:
        st.write("**Quick Summary:**")
        total_positions = sum(1 for pos_data in st.session_state.cone_status.values() if pos_data["cones"])
        st.write(f"Positions tracked: {total_positions}")
    
    # Recent cone updates
    if any(pos_data["last_updated"] for pos_data in st.session_state.cone_status.values()):
        st.subheader("🕒 Recent Cone Updates")
        for position, data in st.session_state.cone_status.items():
            if data["last_updated"] and data["cones"]:
                row, col = position.split("_")
                cone_list = ", ".join([f"{cone}:{status}" for cone, status in data["cones"].items()])
                st.write(f"**R{int(row)+1}C{int(col)+1}:** {cone_list} *(updated {data['last_updated']})*")

# Enhanced Crew Management with Real-time Collaboration
with crew_tab:
    st.subheader("👥 Crew Management & Collaboration")
    
    # Add crew member
    crew_col1, crew_col2, crew_col3, crew_col4 = st.columns(4)
    with crew_col1:
        crew_name = st.text_input("Name")
    with crew_col2:
        crew_role = st.selectbox("Role", 
                               ["kiln_master", "lead_stoker", "stoker", "spotter", "wood_prep", "door_tender", "floater", "observer", "student"])
    with crew_col3:
        shift_start = st.time_input("Shift Start")
    with crew_col4:
        shift_end = st.time_input("Shift End", value=datetime.now().time())
    
    crew_notes = st.text_input("Crew Notes", placeholder="Experience level, special instructions, contact info")
    
    if st.button("Add Crew Member") and crew_name:
        crew_entry = {
            "name": crew_name,
            "role": crew_role, 
            "shift_start": str(shift_start),
            "shift_end": str(shift_end),
            "notes": crew_notes,
            "added_by": active_user,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        st.session_state.crew.append(crew_entry)
        st.success(f"✅ Added {crew_name} as {crew_role}")
    
    # Current crew display
    if st.session_state.crew:
        st.subheader("🔥 Active Firing Crew")
        crew_df = pd.DataFrame(st.session_state.crew)
        
        # Display crew in a nice format
        for _, member in crew_df.iterrows():
            role_icons = {
                "kiln_master": "👑", "lead_stoker": "🔥", "stoker": "🪵", 
                "spotter": "👁️", "wood_prep": "🪓", "door_tender": "🧱", 
                "floater": "🔄", "observer": "📝", "student": "🎓"
            }
            icon = role_icons.get(member['role'], "👤")
            
            with st.container():
                member_col1, member_col2, member_col3 = st.columns([2, 2, 3])
                with member_col1:
                    st.write(f"{icon} **{member['name']}**")
                    st.write(f"*{member['role'].replace('_', ' ').title()}*")
                with member_col2:
                    st.write(f"**Shift:** {member['shift_start']} - {member['shift_end']}")
                    st.write(f"*Added by: {member.get('added_by', 'Unknown')}*")
                with member_col3:
                    if member.get('notes'):
                        st.write(f"**Notes:** {member['notes']}")
                st.divider()
        
        # Crew activity summary
        if st.session_state.log:
            st.subheader("📊 Crew Activity Summary")
            log_df = pd.DataFrame(st.session_state.log)
            activity_summary = log_df['logged_by'].value_counts()
            
            for person, count in activity_summary.items():
                st.write(f"**{person}:** {count} log entries")

# Enhanced Export
with export_tab:
    st.subheader("💾 Export Complete Firing Data")
    
    if st.session_state.log:
        # Complete firing package
        log_df = pd.DataFrame(st.session_state.log)
        wood_df = pd.DataFrame(st.session_state.wood_log) if st.session_state.wood_log else pd.DataFrame()
        crew_df = pd.DataFrame(st.session_state.crew) if st.session_state.crew else pd.DataFrame()
        
        # Create comprehensive export
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            st.download_button(
                "📥 Complete Firing Log",
                log_df.to_csv(index=False).encode('utf-8'),
                f"{kiln_name}_{firing_id}_firing_log.csv",
                "text/csv"
            )
        
        with export_col2:
            if not wood_df.empty:
                st.download_button(
                    "🪵 Wood Consumption Log", 
                    wood_df.to_csv(index=False).encode('utf-8'),
                    f"{kiln_name}_{firing_id}_wood_log.csv",
                    "text/csv"
                )
            else:
                st.write("*No wood data to export*")
        
        with export_col3:
            if not crew_df.empty:
                st.download_button(
                    "👥 Crew Records",
                    crew_df.to_csv(index=False).encode('utf-8'),
                    f"{kiln_name}_{firing_id}_crew.csv", 
                    "text/csv"
                )
            else:
                st.write("*No crew data to export*")
        
        # Cone status export
        if any(pos_data["cones"] for pos_data in st.session_state.cone_status.values()):
            cone_export_data = []
            for position, data in st.session_state.cone_status.items():
                if data["cones"]:
                    row, col = position.split("_")
                    for cone_num, status in data["cones"].items():
                        cone_export_data.append({
                            "position": f"R{int(row)+1}C{int(col)+1}",
                            "cone_number": cone_num,
                            "status": status,
                            "last_updated": data["last_updated"]
                        })
            
            if cone_export_data:
                cone_df = pd.DataFrame(cone_export_data)
                st.download_button(
                    "🎯 Cone Status Map",
                    cone_df.to_csv(index=False).encode('utf-8'),
                    f"{kiln_name}_{firing_id}_cone_map.csv",
                    "text/csv"
                )
        
        # Master summary export
        st.subheader("📋 Firing Summary")
        summary_data = {
            "firing_id": firing_id,
            "kiln": kiln_name, 
            "final_phase": phase,
            "start_time": log_df['time'].min(),
            "last_entry": log_df['time'].max(),
            "duration_hours": (pd.to_datetime(log_df['time']).max() - pd.to_datetime(log_df['time']).min()).total_seconds() / 3600,
            "max_temp_front": log_df['temp_front'].max(),
            "max_temp_middle": log_df['temp_middle'].max(), 
            "max_temp_back": log_df['temp_back'].max(),
            "total_log_entries": len(log_df),
            "total_crew_members": len(crew_df) if not crew_df.empty else 0,
            "wood_pieces_used": wood_df['quantity'].sum() if not wood_df.empty else 0,
            "primary_kiln_master": log_df['logged_by'].mode().iloc[0] if not log_df.empty else active_user
        }
        
        summary_df = pd.DataFrame([summary_data])
        st.download_button(
            "📊 Master Firing Summary",
            summary_df.to_csv(index=False).encode('utf-8'),
            f"{kiln_name}_{firing_id}_SUMMARY.csv",
            "text/csv"
        )
        
        # Display summary stats
        st.json(summary_data)
        
    else:
        st.info("🔍 No firing data to export yet. Start logging to enable exports!")

# About & Help Section
with about_tab:
    st.header("🔥 About WoodFirePro")
    st.subheader("Professional Wood Firing Toolkit for Ceramic Artists")
    
    st.markdown("""
    **WoodFirePro** was developed by analyzing real wood firing logs from experienced potters. 
    This tool respects the kiln master's expertise while providing comprehensive documentation 
    and collaboration features for firing teams.
    
    ### 🎯 **Core Philosophy**
    - **Kiln Master Authority**: No auto-suggestions or algorithmic interference
    - **Real-world Workflow**: Built from actual firing log patterns  
    - **Collaborative**: Support full firing crews with role-based logging
    - **Comprehensive**: Track everything that matters during a wood firing
    """)
    
    st.markdown("---")
    
    st.subheader("📖 Feature Guide")
    
    # Firing Log Help
    with st.expander("📝 **Firing Log** - Core Documentation"):
        st.markdown("""
        **Primary logging interface for all firing observations**
        
        **Key Features:**
        - **Multiple Temperature Sensors**: Front, Middle, Back spy holes + Stack temperature
        - **Atmosphere Control**: Track atmosphere type, damper position, and air intake
        - **Visual Observations**: Record flame character, spy hole colors, draft sounds
        - **Action Tracking**: Document exactly what actions you took
        - **Entry Types**: Categorize entries (observation, stoke, damper change, etc.)
        - **User Attribution**: Every entry tagged with who logged it
        
        **Best Practices:**
        - Log every 10-20 minutes during active firing phases
        - Include specific actions taken, not just observations
        - Use descriptive flame and color observations
        - Note any problems or unusual behavior immediately
        """)
    
    # Wood Tracker Help
    with st.expander("🪵 **Wood Tracker** - Active Consumption Logging"):
        st.markdown("""
        **Track wood as it goes into the kiln - not just static inventory**
        
        **Active Consumption Features:**
        - **Real-time Usage**: Log each stoking session with species, size, quantity
        - **Firebox Location**: Track where wood goes (primary, secondary, side stoke)
        - **Consumption Patterns**: Analyze wood usage rates over time
        - **Species Tracking**: Monitor which woods are used in which phases
        
        **Inventory Management:**
        - Traditional cord/moisture tracking for pre-firing planning
        - Storage location management
        - Moisture content documentation
        
        **Pro Tips:**
        - Log wood immediately after stoking while details are fresh
        - Note wood condition (dry, bark, splits easily, etc.)
        - Track different species usage for different firing phases
        """)
    
    # Analysis Help  
    with st.expander("📊 **Analysis** - Data Visualization & Statistics"):
        st.markdown("""
        **Comprehensive firing analysis with multiple chart views**
        
        **Available Charts:**
        - **Temperature Progress**: All sensor readings over time
        - **Atmosphere Control**: Damper and air intake positions
        - **Wood Consumption**: Cumulative usage patterns
        - **Atmosphere Distribution**: Time spent in each atmosphere type
        
        **Key Statistics:**
        - Total firing duration
        - Peak temperatures across all sensors
        - Temperature variance between sensors
        - Average logging interval
        - Reduction time percentage
        
        **When to Use:**
        - During firing for trend monitoring
        - Post-firing for results analysis
        - Comparing multiple firings
        - Identifying optimal firing curves
        """)
    
    # Timer Help
    with st.expander("⏲️ **Timer** - Phase-Aware Stoking Intervals"):
        st.markdown("""
        **Smart timer system that adapts to firing phases**
        
        **Features:**
        - **Phase-Aware Defaults**: Suggested intervals for each firing phase
        - **Visual Progress**: Progress bar shows elapsed time
        - **Alert System**: Visual and audio alerts when timer expires
        - **Auto-Reset**: Timer stops automatically when time is up
        
        **Suggested Intervals by Phase:**
        - **Heating**: 15 minutes
        - **Water Smoking**: 20 minutes  
        - **Dehydration**: 15 minutes
        - **Body Reduction**: 10 minutes
        - **Glaze Maturation**: 8 minutes
        - **Flash**: 5 minutes
        - **Cooling**: 30 minutes
        
        **Note**: These are suggestions only - kiln master always decides actual timing!
        """)
    
    # Cone Map Help
    with st.expander("🎯 **Cone Map** - Visual Kiln Interior Tracking"):
        st.markdown("""
        **Interactive grid representation of your kiln interior**
        
        **How It Works:**
        1. Select cone number and status from dropdowns
        2. Click grid position (R1C1 = Row 1, Column 1) to update
        3. Visual indicators show cone progression across kiln
        
        **Status Indicators:**
        - 🔴 **Red**: Bent, Down, or Overfired cones
        - 🟡 **Yellow**: Bending or Soft cones  
        - ⚪ **White**: Standing cones
        
        **Grid Layout:**
        - Default 6 rows × 8 columns
        - Front to back representation
        - Multiple cones can be tracked per position
        - Timestamp and user tracking for all updates
        
        **Pro Tips:**
        - Update cone status as soon as you observe changes
        - Track draw trials and guide cones separately
        - Use consistent positioning between firings for comparison
        """)
    
    # Crew Help
    with st.expander("👥 **Crew** - Collaborative Team Management"):
        st.markdown("""
        **Comprehensive crew management for team firings**
        
        **Role Types:**
        - 👑 **Kiln Master**: Overall firing authority and decision maker
        - 🔥 **Lead Stoker**: Primary stoking responsibilities  
        - 🪵 **Stoker**: Additional stoking support
        - 👁️ **Spotter**: Temperature and cone monitoring
        - 🪓 **Wood Prep**: Wood preparation and staging
        - 🧱 **Door Tender**: Door brick and damper management
        - 🔄 **Floater**: Flexible support role
        - 📝 **Observer**: Documentation and learning
        - 🎓 **Student**: Learning observer
        
        **Collaboration Features:**
        - Shift tracking with start/end times
        - Activity logging (who logged what entries)
        - Role-based responsibility clarity
        - Experience level and contact info tracking
        
        **Best Practices:**
        - Clearly define roles before firing begins
        - Update active user name when logging
        - Track shift changes in firing log
        - Include experience levels for safety planning
        """)
    
    # Export Help
    with st.expander("💾 **Export** - Comprehensive Data Management"):
        st.markdown("""
        **Complete firing documentation export system**
        
        **Available Exports:**
        - **Complete Firing Log**: All temperature, atmosphere, and observation data
        - **Wood Consumption Log**: Detailed wood usage tracking
        - **Crew Records**: Team member information and shift data  
        - **Cone Status Map**: Visual kiln map data with timestamps
        - **Master Summary**: Key metrics and firing overview
        
        **File Formats:**
        - CSV format for spreadsheet compatibility
        - Structured data for database import
        - Human-readable summaries
        
        **Data Backup Strategy:**
        - Export data regularly during long firings
        - Save complete datasets after each firing
        - Archive successful firing data for reference
        - Share data with firing team members
        
        **Pro Tips:**
        - Export mid-firing as backup during multi-day firings
        - Use consistent naming conventions (kiln_date_type)
        - Keep master summaries for firing comparison
        """)
    
    st.markdown("---")
    
    st.subheader("🚀 **Getting Started Workflow**")
    
    workflow_col1, workflow_col2 = st.columns(2)
    
    with workflow_col1:
        st.markdown("""
        **Pre-Firing Setup:**
        1. Set kiln name and firing ID
        2. Add crew members with roles
        3. Set current firing phase
        4. Load wood inventory data
        5. Set your active user name
        """)
    
    with workflow_col2:
        st.markdown("""
        **During Firing:**
        1. Start with initial temperature log entry
        2. Use timer for regular check intervals
        3. Log all significant observations and actions
        4. Update cone status as cones move
        5. Track wood consumption in real-time
        """)
    
    st.markdown("""
    **Post-Firing:**
    1. Log final temperatures and observations
    2. Update all remaining cone positions
    3. Export complete firing documentation
    4. Review analysis charts for insights
    5. Archive data for future reference
    """)
    
    st.markdown("---")
    
    st.subheader("💡 **Pro Tips & Best Practices**")
    
    tips_col1, tips_col2 = st.columns(2)
    
    with tips_col1:
        st.markdown("""
        **Logging Excellence:**
        - Log immediately when you observe changes
        - Be specific with color and flame descriptions
        - Always note the actions you take
        - Include atmospheric conditions (wind, rain, etc.)
        - Document problems and how you solved them
        """)
    
    with tips_col2:
        st.markdown("""
        **Team Coordination:**  
        - Clearly communicate role responsibilities
        - Update active user when logging entries
        - Use consistent terminology across team
        - Share observation techniques with students
        - Keep communication open between shifts
        """)
    
    st.markdown("---")
    
    st.subheader("🔧 **Troubleshooting & FAQ**")
    
    faq_col1, faq_col2 = st.columns(2)
    
    with faq_col1:
        st.markdown("""
        **Common Issues:**
        
        **Q: Timer not alerting?**
        A: Make sure browser allows notifications and keep tab active
        
        **Q: Data not saving?**  
        A: Export data regularly - session state resets on browser refresh
        
        **Q: Cone map confusing?**
        A: Start simple - track just a few key positions first
        """)
    
    with faq_col2:
        st.markdown("""
        **Technical Notes:**
        
        **Q: Mobile compatibility?**
        A: Yes! Works on phones/tablets for quick logging
        
        **Q: Multiple users simultaneously?**
        A: Share same device or export/merge data later
        
        **Q: Data backup?**
        A: Export CSV files regularly - no automatic cloud sync
        """)
    
    st.markdown("---")
    
    st.subheader("🏺 **About the Development**")
    
    st.markdown("""
    **WoodFirePro** was created by analyzing real handwritten wood firing logs from experienced ceramic artists. 
    The interface design prioritizes the expertise and intuition of the kiln master while providing comprehensive 
    documentation tools for the entire firing team.
    
    **Managed and created by [Alford Wayman](https://creekroadpottery.com) of Creek Road Pottery LLC with the help of Claude and ChatGPT coding.**
    
    **Core Values:**
    - **Respect for Traditional Knowledge**: Digital tools should enhance, not replace, potter intuition
    - **Real-world Tested**: Every feature based on actual firing log patterns
    - **Community Focused**: Built for collaboration and knowledge sharing
    - **Open and Transparent**: No black-box algorithms making firing decisions
    
    **Built with ❤️ for the wood firing community**
    
    ---
    *"The kiln master's senses and experience are irreplaceable. Technology should document the journey, not dictate the destination."*
    
    **© 2025 Creek Road Pottery LLC | WoodFirePro**
    """)

# Footer with collaboration status
st.markdown("---")
current_time = datetime.now().strftime("%H:%M:%S")
st.caption(f"🔥 WoodFirePro - Active User: **{active_user}** | Current Time: {current_time} | Phase: **{phase}** | Save data regularly!")
