import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import requests

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
if "historical_firings" not in st.session_state:
    st.session_state.historical_firings = []
if "safety_checklist" not in st.session_state:
    st.session_state.safety_checklist = {}
if "emergency_contacts" not in st.session_state:
    st.session_state.emergency_contacts = []
if "mobile_mode" not in st.session_state:
    st.session_state.mobile_mode = False

# Weather API function (using OpenWeatherMap - requires API key)
def get_weather_data(api_key=None, location="40.7128,-74.0060"):  # Default NYC coords
    if not api_key:
        return {
            "temperature": 72, "humidity": 65, "pressure": 29.92, 
            "wind_speed": 8, "wind_direction": "SW", "conditions": "Clear",
            "note": "Demo data - add API key for real weather"
        }
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={location.split(',')[0]}&lon={location.split(',')[1]}&appid={api_key}&units=imperial"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        return {
            "temperature": data['main']['temp'],
            "humidity": data['main']['humidity'], 
            "pressure": data['main']['pressure'] * 0.02953,  # Convert hPa to inHg
            "wind_speed": data['wind']['speed'],
            "wind_direction": data['wind'].get('deg', 0),
            "conditions": data['weather'][0]['description'],
            "note": "Live weather data"
        }
    except:
        return {
            "temperature": 72, "humidity": 65, "pressure": 29.92,
            "wind_speed": 8, "wind_direction": "SW", "conditions": "Unable to fetch",
            "note": "Weather API error - using demo data"
        }

st.title("🔥 WoodFirePro")
st.caption("Professional wood firing toolkit - built for real potters")

# Mobile mode toggle
mobile_toggle = st.sidebar.checkbox("📱 Mobile Mode", value=st.session_state.mobile_mode, 
                                   help="Optimized interface for phones/tablets at the kiln")
st.session_state.mobile_mode = mobile_toggle

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
    
    # Weather integration
    st.header("🌤️ Current Weather")
    weather_api_key = st.text_input("Weather API Key (optional)", type="password", 
                                   help="OpenWeatherMap API key for live weather")
    location_coords = st.text_input("Location (lat,lon)", value="40.7128,-74.0060",
                                   help="Your kiln's GPS coordinates")
    
    current_weather = get_weather_data(weather_api_key, location_coords)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Temp", f"{current_weather['temperature']:.0f}°F")
        st.metric("Humidity", f"{current_weather['humidity']}%")
    with col2:
        st.metric("Pressure", f"{current_weather['pressure']:.2f} inHg")
        st.metric("Wind", f"{current_weather['wind_speed']} mph")
    st.caption(current_weather['note'])
    
    # Live stats
    if st.session_state.log:
        df = pd.DataFrame(st.session_state.log)
        latest = df.iloc[-1]
        st.header("📊 Current Status")
        st.metric("Latest Temp (Front)", f"{latest.get('temp_front', 0)}°F")
        st.metric("Last Entry By", latest.get('logged_by', 'Unknown'))
        st.metric("Firing Duration", f"{(pd.to_datetime(df['time']).max() - pd.to_datetime(df['time']).min()).total_seconds() / 3600:.1f} hrs")

# Emergency contacts quick access
if st.session_state.emergency_contacts:
    with st.sidebar:
        st.header("🚨 Emergency Contacts")
        for contact in st.session_state.emergency_contacts[:3]:  # Show first 3
            st.write(f"**{contact['name']}**: {contact['phone']}")

# Historical firing comparison
if st.session_state.historical_firings and st.session_state.log:
    with st.sidebar:
        st.header("📊 Historical Comparison")
        current_df = pd.DataFrame(st.session_state.log)
        if not current_df.empty:
            current_temp = current_df.iloc[-1]['temp_front']
            current_duration = (pd.to_datetime(current_df['time']).max() - pd.to_datetime(current_df['time']).min()).total_seconds() / 3600
            
            # Find similar point in historical data
            for firing in st.session_state.historical_firings:
                hist_df = pd.DataFrame(firing['log_data'])
                if not hist_df.empty:
                    # Find entry with similar temperature
                    similar_entries = hist_df[abs(hist_df['temp_front'] - current_temp) < 50]
                    if not similar_entries.empty:
                        similar_entry = similar_entries.iloc[0]
                        st.write(f"**{firing['firing_id']}** at {current_temp}°F:")
                        st.caption(f"Action: {similar_entry.get('action_taken', 'N/A')}")
                        break

# Main content area
if st.session_state.mobile_mode:
    # Mobile-optimized layout
    st.header("📱 Quick Mobile Log")
    
    # Simplified mobile entry form
    with st.form("mobile_log"):
        temp_front = st.number_input("Front Temp (°F)", value=900, step=25)
        atmosphere = st.selectbox("Atmosphere", ["oxidation", "neutral", "reduction", "heavy_reduction"])
        action = st.text_area("What did you do?", placeholder="Added 3 oak splits, adjusted damper...")
        notes = st.text_area("Voice Notes (use speech-to-text)", placeholder="Tap here and use voice input...")
        
        # Weather inclusion
        include_weather = st.checkbox("Include current weather", value=True)
        
        submitted = st.form_submit_button("🔥 Quick Log Entry")
        
        if submitted:
            entry = {
                "kiln": kiln_name,
                "firing_id": firing_id,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "logged_by": active_user,
                "phase": phase,
                "entry_type": "mobile_quick",
                "temp_front": temp_front,
                "temp_middle": temp_front,  # Assume similar for quick entry
                "temp_back": temp_front,
                "temp_stack": temp_front - 500,
                "atmosphere": atmosphere,
                "damper_position": 50,  # Default
                "air_intake": 50,  # Default
                "fuel_type": "wood_only",
                "action_taken": action,
                "notes": notes
            }
            
            if include_weather:
                entry.update({
                    "weather_temp": current_weather['temperature'],
                    "weather_humidity": current_weather['humidity'],
                    "weather_pressure": current_weather['pressure'],
                    "weather_wind": current_weather['wind_speed'],
                    "weather_conditions": current_weather['conditions']
                })
            
            st.session_state.log.append(entry)
            st.success("✅ Quick entry logged!")
            st.rerun()
    
    # Recent entries for mobile
    if st.session_state.log:
        st.subheader("Recent Entries")
        df = pd.DataFrame(st.session_state.log)
        recent = df.tail(3).sort_values("time", ascending=False)
        for _, row in recent.iterrows():
            st.write(f"**{row['time'].split()[1]}** - {row['temp_front']}°F - {row.get('action_taken', 'No action')}")

else:
    # Full desktop interface
    # Main tabs
    log_tab, safety_tab, wood_tab, analysis_tab, timer_tab, cones_tab, crew_tab, history_tab, export_tab, about_tab = st.tabs([
        "📝 Firing Log", "⚠️ Safety", "🪵 Wood Tracker", "📊 Analysis", "⏲️ Timer", "🎯 Cone Map", "👥 Crew", "📊 History", "💾 Export", "ℹ️ About"
    ])

    # Safety Tab - NEW
    with safety_tab:
        st.subheader("⚠️ Pre-Firing Safety Checklist")
        
        safety_items = [
            "Damper and stack clear and operational",
            "Fire extinguisher present and charged", 
            "Water source available and accessible",
            "First aid kit present and stocked",
            "Emergency phone numbers posted",
            "Kiln area clear of flammable materials",
            "Proper protective equipment available",
            "Weather conditions acceptable for firing",
            "Crew briefed on emergency procedures",
            "Local fire department notified (if required)"
        ]
        
        st.write("**Check off completed items:**")
        for i, item in enumerate(safety_items):
            checked = st.checkbox(item, key=f"safety_{i}", 
                                value=st.session_state.safety_checklist.get(f"safety_{i}", False))
            st.session_state.safety_checklist[f"safety_{i}"] = checked
        
        # Safety status
        completed_items = sum(st.session_state.safety_checklist.values())
        total_items = len(safety_items)
        
        if completed_items == total_items:
            st.success(f"✅ All safety items completed ({completed_items}/{total_items})")
        else:
            st.warning(f"⚠️ Safety checklist: {completed_items}/{total_items} completed")
        
        # Emergency contacts management
        st.subheader("🚨 Emergency Contacts")
        
        with st.expander("Add Emergency Contact"):
            contact_name = st.text_input("Contact Name")
            contact_phone = st.text_input("Phone Number")
            contact_role = st.selectbox("Role", ["Fire Department", "Medical", "Kiln Owner", "Supervisor", "Other"])
            
            if st.button("Add Contact"):
                st.session_state.emergency_contacts.append({
                    "name": contact_name,
                    "phone": contact_phone,
                    "role": contact_role
                })
                st.success("Contact added!")
        
        # Display emergency contacts
        if st.session_state.emergency_contacts:
            st.write("**Current Emergency Contacts:**")
            for i, contact in enumerate(st.session_state.emergency_contacts):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{contact['name']}** ({contact['role']})")
                with col2:
                    st.write(f"📞 {contact['phone']}")
                with col3:
                    if st.button("Remove", key=f"remove_contact_{i}"):
                        st.session_state.emergency_contacts.pop(i)
                        st.rerun()
        
        # Incident logging
        st.subheader("📋 Incident Logging")
        with st.form("incident_form"):
            incident_type = st.selectbox("Incident Type", 
                                       ["Near Miss", "Minor Injury", "Equipment Failure", "Fire/Safety", "Other"])
            incident_description = st.text_area("Description")
            incident_action = st.text_area("Action Taken")
            
            if st.form_submit_button("Log Incident"):
                incident = {
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": incident_type,
                    "description": incident_description,
                    "action_taken": incident_action,
                    "reported_by": active_user,
                    "firing_id": firing_id
                }
                
                # Add to regular log as well
                log_entry = {
                    "kiln": kiln_name,
                    "firing_id": firing_id,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "logged_by": active_user,
                    "phase": phase,
                    "entry_type": "incident",
                    "temp_front": 0,
                    "temp_middle": 0,
                    "temp_back": 0,
                    "temp_stack": 0,
                    "atmosphere": "n/a",
                    "damper_position": 0,
                    "air_intake": 0,
                    "fuel_type": "n/a",
                    "action_taken": f"INCIDENT: {incident_type} - {incident_action}",
                    "notes": f"SAFETY INCIDENT: {incident_description}"
                }
                
                st.session_state.log.append(log_entry)
                st.error(f"⚠️ {incident_type} incident logged!")

    # Enhanced Firing Log with weather integration
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
            
            # Weather impact assessment
            weather_impact = st.selectbox("Weather Impact", 
                                        ["none", "helping_draft", "hindering_draft", "affecting_heat", "other"])
        
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
        
        # General notes with weather context
        notes = st.text_area("Notes & Observations", 
                           placeholder="Problems, decisions, atmospheric conditions, weather effects...")
        
        # Historical comparison suggestion
        if st.session_state.historical_firings:
            st.info("💡 Check the History tab for similar temperature comparisons from previous firings")
        
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
                "notes": notes,
                "weather_impact": weather_impact,
                # Include current weather data
                "weather_temp": current_weather['temperature'],
                "weather_humidity": current_weather['humidity'],
                "weather_pressure": current_weather['pressure'],
                "weather_wind": current_weather['wind_speed'],
                "weather_conditions": current_weather['conditions']
            }
            st.session_state.log.append(entry)
            st.success(f"✅ Entry logged by {active_user}")
            st.rerun()

        # Display recent entries with edit/delete functionality
        if st.session_state.log:
            st.subheader("📋 Recent Entries")
            df = pd.DataFrame(st.session_state.log)
            df_display = df.sort_values("time", ascending=False).head(8)
            
            for i, (_, row) in enumerate(df_display.iterrows()):
                # Find the actual index in the session state
                entry_index = None
                for idx, entry in enumerate(st.session_state.log):
                    if (entry['time'] == row['time'] and 
                        entry.get('logged_by') == row.get('logged_by') and
                        entry['temp_front'] == row['temp_front']):
                        entry_index = idx
                        break
                
                # Color-code by entry type
                entry_colors = {
                    "observation": "🔍", "stoke": "🔥", "damper_change": "💨", 
                    "door_brick": "🧱", "problem": "⚠️", "milestone": "🎯", "shift_change": "👥",
                    "incident": "🚨", "mobile_quick": "📱"
                }
                icon = entry_colors.get(row['entry_type'], "📝")
                
                with st.expander(f"{icon} {row['time']} - {row['entry_type'].replace('_', ' ').title()} by {row.get('logged_by', 'Unknown')} ({row['temp_front']}°F)"):
                    # Entry content
                    temp_col, atm_col, weather_col = st.columns(3)
                    with temp_col:
                        st.write(f"**Temps:** F:{row['temp_front']}° M:{row['temp_middle']}° B:{row['temp_back']}° Stack:{row['temp_stack']}°")
                        if row.get('flame_color'):
                            st.write(f"**Flame:** {row['flame_color']}")
                        if row.get('spy_color'):
                            st.write(f"**Spy Holes:** {row['spy_color']}")
                        if row.get('draft_sound'):
                            st.write(f"**Draft:** {row['draft_sound']}")
                    with atm_col:
                        st.write(f"**Atmosphere:** {row['atmosphere']}")
                        st.write(f"**Damper:** {row['damper_position']}% | **Air:** {row['air_intake']}%")
                        st.write(f"**Fuel:** {row['fuel_type']}")
                        if row.get('action_taken'):
                            st.write(f"**Action:** {row['action_taken']}")
                    with weather_col:
                        if row.get('weather_temp'):
                            st.write(f"**Weather:** {row['weather_temp']:.0f}°F, {row['weather_humidity']}% humidity")
                            st.write(f"**Wind:** {row['weather_wind']} mph")
                            st.write(f"**Conditions:** {row['weather_conditions']}")
                            if row.get('weather_impact', 'none') != 'none':
                                st.write(f"**Impact:** {row['weather_impact']}")
                    if row.get('notes'):
                        st.write(f"**Notes:** {row['notes']}")
                    
                    # Edit/Delete buttons
                    edit_col, delete_col = st.columns(2)
                    with edit_col:
                        if st.button(f"✏️ Edit Entry", key=f"edit_{i}"):
                            st.session_state[f"editing_{entry_index}"] = True
                            st.rerun()
                    with delete_col:
                        if st.button(f"🗑️ Delete Entry", key=f"delete_{i}", type="secondary"):
                            if entry_index is not None:
                                st.session_state.log.pop(entry_index)
                                st.success("Entry deleted!")
                                st.rerun()
        
        # Edit form for entries
        if st.session_state.log:
            for idx, entry in enumerate(st.session_state.log):
                if st.session_state.get(f"editing_{idx}", False):
                    st.subheader(f"✏️ Editing Entry: {entry['time']}")
                    
                    with st.form(f"edit_form_{idx}"):
                        # Editable fields
                        edit_col1, edit_col2 = st.columns(2)
                        with edit_col1:
                            new_temp_front = st.number_input("Front Temp", value=entry['temp_front'], key=f"edit_temp_front_{idx}")
                            new_atmosphere = st.selectbox("Atmosphere", 
                                                        ["neutral", "light_oxidation", "oxidation", "light_reduction", "reduction", "heavy_reduction"],
                                                        index=["neutral", "light_oxidation", "oxidation", "light_reduction", "reduction", "heavy_reduction"].index(entry.get('atmosphere', 'neutral')),
                                                        key=f"edit_atmosphere_{idx}")
                            new_damper = st.slider("Damper Position", 0, 100, entry.get('damper_position', 50), key=f"edit_damper_{idx}")
                        
                        with edit_col2:
                            new_action = st.text_area("Action Taken", value=entry.get('action_taken', ''), key=f"edit_action_{idx}")
                            new_notes = st.text_area("Notes", value=entry.get('notes', ''), key=f"edit_notes_{idx}")
                        
                        # Form buttons
                        save_col, cancel_col = st.columns(2)
                        with save_col:
                            if st.form_submit_button("💾 Save Changes"):
                                # Update the entry
                                st.session_state.log[idx]['temp_front'] = new_temp_front
                                st.session_state.log[idx]['atmosphere'] = new_atmosphere
                                st.session_state.log[idx]['damper_position'] = new_damper
                                st.session_state.log[idx]['action_taken'] = new_action
                                st.session_state.log[idx]['notes'] = new_notes
                                st.session_state.log[idx]['edited_by'] = active_user
                                st.session_state.log[idx]['edited_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                
                                # Clear editing state
                                st.session_state[f"editing_{idx}"] = False
                                st.success("Entry updated!")
                                st.rerun()
                        
                        with cancel_col:
                            if st.form_submit_button("❌ Cancel"):
                                st.session_state[f"editing_{idx}"] = False
                                st.rerun()
        
        # Bulk operations for log entries
        if st.session_state.log:
            st.subheader("🔧 Bulk Log Operations")
            bulk_log_col1, bulk_log_col2 = st.columns(2)
            
            with bulk_log_col1:
                if st.button("🗑️ Clear Last Entry", type="secondary"):
                    if st.session_state.log:
                        removed = st.session_state.log.pop()
                        st.success(f"Removed entry from {removed['time']}")
                        st.rerun()
            
            with bulk_log_col2:
                entry_count = len(st.session_state.log)
                st.write(f"**Total Entries:** {entry_count}")
                if entry_count > 0:
                    latest_entry = st.session_state.log[-1]
                    st.write(f"**Latest:** {latest_entry['time']} - {latest_entry['temp_front']}°F")

    # Historical Comparison Tab - NEW
    with history_tab:
        st.subheader("📊 Historical Firing Comparison")
        
        # Upload historical firing data
        st.write("**Import Previous Firing Data:**")
        uploaded_file = st.file_uploader("Upload previous firing CSV", type="csv")
        
        if uploaded_file:
            try:
                historical_df = pd.read_csv(uploaded_file)
                firing_name = st.text_input("Name this firing", value=f"Import_{datetime.now().strftime('%m%d')}")
                
                if st.button("Add to Historical Database"):
                    historical_firing = {
                        "firing_id": firing_name,
                        "date_imported": datetime.now().strftime("%Y-%m-%d"),
                        "log_data": historical_df.to_dict('records')
                    }
                    st.session_state.historical_firings.append(historical_firing)
                    st.success(f"Added {firing_name} to historical database!")
                    
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
        
        # Display historical firings
        if st.session_state.historical_firings:
            st.write(f"**Historical Firings Available: {len(st.session_state.historical_firings)}**")
            
            selected_firing = st.selectbox("Select firing for comparison", 
                                         [f["firing_id"] for f in st.session_state.historical_firings])
            
            if selected_firing and st.session_state.log:
                # Current firing data
                current_df = pd.DataFrame(st.session_state.log)
                current_df['datetime'] = pd.to_datetime(current_df['time'])
                
                # Selected historical firing data
                historical_firing = next(f for f in st.session_state.historical_firings if f["firing_id"] == selected_firing)
                historical_df = pd.DataFrame(historical_firing["log_data"])
                
                if 'time' in historical_df.columns:
                    historical_df['datetime'] = pd.to_datetime(historical_df['time'])
                    
                    # Real-time comparison
                    if not current_df.empty:
                        current_temp = current_df.iloc[-1]['temp_front']
                        current_duration = (current_df['datetime'].max() - current_df['datetime'].min()).total_seconds() / 3600
                        
                        st.subheader(f"📈 Comparison: Current vs {selected_firing}")
                        
                        # Find similar points
                        temp_tolerance = 50  # degrees F
                        similar_entries = historical_df[abs(historical_df['temp_front'] - current_temp) < temp_tolerance]
                        
                        if not similar_entries.empty:
                            st.success(f"Found {len(similar_entries)} similar temperature points in {selected_firing}")
                            
                            # Show most relevant comparison
                            closest_entry = similar_entries.iloc[0]
                            
                            comp_col1, comp_col2 = st.columns(2)
                            with comp_col1:
                                st.write("**Current Firing:**")
                                st.write(f"Temperature: {current_temp}°F")
                                st.write(f"Duration: {current_duration:.1f} hours")
                                if not current_df.empty:
                                    latest = current_df.iloc[-1]
                                    st.write(f"Last action: {latest.get('action_taken', 'None')}")
                                    
                            with comp_col2:
                                st.write(f"**{selected_firing} at similar temp:**")
                                st.write(f"Temperature: {closest_entry['temp_front']}°F")
                                st.write(f"Action taken: {closest_entry.get('action_taken', 'None')}")
                                st.write(f"Notes: {closest_entry.get('notes', 'None')[:100]}...")
                            
                            # Temperature progression comparison
                            st.subheader("🔥 Temperature Progression Comparison")
                            
                            # Prepare data for comparison chart
                            current_chart_data = current_df.set_index('datetime')[['temp_front']].copy()
                            current_chart_data.columns = ['Current Firing Front Temp']
                            
                            # Normalize historical data to start at same time as current
                            if not historical_df.empty:
                                hist_start = historical_df['datetime'].min()
                                current_start = current_df['datetime'].min()
                                time_offset = current_start - hist_start
                                
                                historical_df['adjusted_datetime'] = historical_df['datetime'] + time_offset
                                historical_chart_data = historical_df.set_index('adjusted_datetime')[['temp_front']].copy()
                                historical_chart_data.columns = [f'{selected_firing} Front Temp']
                                
                                # Combine datasets
                                combined_data = pd.concat([current_chart_data, historical_chart_data], axis=1)
                                st.line_chart(combined_data)
                        
                        else:
                            st.info("No similar temperature points found in historical data")
                
        else:
            st.info("No historical firings loaded. Upload previous firing CSV files to enable comparison.")
        
        # Quick historical insights
        if st.session_state.historical_firings and st.session_state.log:
            st.subheader("💡 Historical Insights")
            
            current_df = pd.DataFrame(st.session_state.log)
            if not current_df.empty:
                current_temp = current_df.iloc[-1]['temp_front']
                
                insights = []
                for firing in st.session_state.historical_firings:
                    hist_df = pd.DataFrame(firing["log_data"])
                    if not hist_df.empty and 'temp_front' in hist_df.columns:
                        max_temp = hist_df['temp_front'].max()
                        if max_temp > current_temp:
                            final_actions = hist_df.tail(3)['action_taken'].tolist()
                            insights.append({
                                "firing_id": firing["firing_id"],
                                "max_temp": max_temp,
                                "final_actions": [a for a in final_actions if pd.notna(a)]
                            })
                
                if insights:
                    st.write("**What happened next in previous firings:**")
                    for insight in insights[:3]:  # Show top 3
                        st.write(f"**{insight['firing_id']}** (reached {insight['max_temp']}°F):")
                        for action in insight['final_actions'][-2:]:  # Last 2 actions
                            st.write(f"  • {action}")

    # Rest of the tabs (Wood Tracker, Analysis, Timer, Cone Map, Crew, Export, About) remain the same as before
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
            
            # Recent wood entries with edit/delete options
            st.subheader("🪵 Recent Wood Usage")
            recent_wood = wood_df.tail(10).sort_values('time', ascending=False)
            for idx, wood in recent_wood.iterrows():
                wood_col1, wood_col2 = st.columns([4, 1])
                with wood_col1:
                    st.write(f"**{wood['time']}** - {wood['quantity']} {wood['size']} {wood['species']} → {wood['location']} *(by {wood['logged_by']})*")
                with wood_col2:
                    # Find the actual index in wood_log
                    wood_index = None
                    for i, entry in enumerate(st.session_state.wood_log):
                        if (entry['time'] == wood['time'] and 
                            entry['species'] == wood['species'] and 
                            entry['quantity'] == wood['quantity']):
                            wood_index = i
                            break
                    
                    if wood_index is not None:
                        if st.button("🗑️", key=f"delete_wood_{idx}", help="Delete this wood entry"):
                            st.session_state.wood_log.pop(wood_index)
                            st.success("Wood entry deleted!")
                            st.rerun()
        
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

    # Analysis Tab - Enhanced with weather correlation
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
            
            # Weather correlation analysis
            if 'weather_temp' in df.columns:
                st.subheader("🌤️ Weather Impact Analysis")
                weather_chart_data = df_chart[['weather_temp', 'weather_humidity', 'weather_wind']].copy()
                weather_chart_data.columns = ['Outside Temp (°F)', 'Humidity (%)', 'Wind Speed (mph)']
                st.line_chart(weather_chart_data)
                
                # Weather impact insights
                weather_impacts = df['weather_impact'].value_counts()
                if len(weather_impacts) > 1:
                    st.bar_chart(weather_impacts)
            
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
            
            # Enhanced statistics with weather
            st.subheader("📊 Firing Statistics")
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            with stats_col1:
                duration = (df['datetime'].max() - df['datetime'].min()).total_seconds() / 3600
                st.metric("Total Duration", f"{duration:.1f} hrs")
            with stats_col2:
                max_temp = df[['temp_front', 'temp_middle', 'temp_back']].max().max()
                st.metric("Peak Temperature", f"{max_temp:.0f}°F")
            with stats_col3:
                if 'weather_wind' in df.columns:
                    avg_wind = df['weather_wind'].mean()
                    st.metric("Avg Wind Speed", f"{avg_wind:.1f} mph")
                else:
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

    # Visual Kiln Map for Cone Tracking with Edit/Clear functionality
    with cones_tab:
        st.subheader("🎯 Interactive Kiln Cone Map")
        st.caption("Click grid positions to update cone status. Right-click options for editing/clearing.")
        
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
        
        # Create visual grid with edit/clear options
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
                    
                    # Main button for this position
                    if st.button(f"R{row+1}C{col+1}", key=f"pos_{row}_{col}", help=display_text):
                        # Update the position
                        if position_key not in st.session_state.cone_status:
                            st.session_state.cone_status[position_key] = {"cones": {}, "last_updated": None}
                        
                        st.session_state.cone_status[position_key]["cones"][selected_cone] = cone_status
                        st.session_state.cone_status[position_key]["last_updated"] = f"{datetime.now().strftime('%H:%M')} by {active_user}"
                        st.success(f"Updated R{row+1}C{col+1}: Cone {selected_cone} = {cone_status}")
                        st.rerun()
                    
                    # Edit/Clear options if position has data
                    if position_data["cones"]:
                        edit_clear_col1, edit_clear_col2 = st.columns(2)
                        with edit_clear_col1:
                            if st.button("✏️", key=f"edit_pos_{row}_{col}", help="Edit this position"):
                                st.session_state[f"editing_cone_{position_key}"] = True
                                st.rerun()
                        with edit_clear_col2:
                            if st.button("🗑️", key=f"clear_pos_{row}_{col}", help="Clear this position"):
                                st.session_state.cone_status[position_key] = {"cones": {}, "last_updated": None}
                                st.success(f"Cleared R{row+1}C{col+1}")
                                st.rerun()
                    
                    # Show current status
                    if position_data["cones"]:
                        st.caption(display_text.replace('\n', ' | '))
        
        # Edit forms for cone positions
        for position_key, data in st.session_state.cone_status.items():
            if st.session_state.get(f"editing_cone_{position_key}", False):
                row, col = position_key.split("_")
                st.subheader(f"✏️ Editing Position R{int(row)+1}C{int(col)+1}")
                
                with st.form(f"edit_cone_form_{position_key}"):
                    st.write("**Current Cones at this Position:**")
                    
                    # Show existing cones with individual edit/delete options
                    cones_to_remove = []
                    updated_cones = {}
                    
                    for cone_num, status in data["cones"].items():
                        cone_edit_col1, cone_edit_col2, cone_edit_col3 = st.columns([2, 2, 1])
                        
                        with cone_edit_col1:
                            st.write(f"**Cone {cone_num}:**")
                        with cone_edit_col2:
                            new_status = st.selectbox(f"Status", 
                                                    ["standing", "soft", "bending", "bent", "down", "overfired"],
                                                    index=["standing", "soft", "bending", "bent", "down", "overfired"].index(status),
                                                    key=f"edit_cone_{position_key}_{cone_num}")
                            updated_cones[cone_num] = new_status
                        with cone_edit_col3:
                            if st.checkbox("Remove", key=f"remove_cone_{position_key}_{cone_num}"):
                                cones_to_remove.append(cone_num)
                    
                    # Add new cone option
                    st.write("**Add New Cone:**")
                    add_col1, add_col2 = st.columns(2)
                    with add_col1:
                        new_cone_num = st.selectbox("New Cone", ["", "08", "06", "04", "03", "01", "1", "3", "5", "6", "7", "8", "9", "10", "11", "12"], key=f"new_cone_{position_key}")
                    with add_col2:
                        new_cone_status = st.selectbox("New Status", ["standing", "soft", "bending", "bent", "down", "overfired"], key=f"new_status_{position_key}")
                    
                    # Form buttons
                    save_col, cancel_col = st.columns(2)
                    with save_col:
                        if st.form_submit_button("💾 Save Changes"):
                            # Apply updates
                            for cone_num in cones_to_remove:
                                updated_cones.pop(cone_num, None)
                            
                            # Add new cone if specified
                            if new_cone_num:
                                updated_cones[new_cone_num] = new_cone_status
                            
                            # Save to session state
                            st.session_state.cone_status[position_key]["cones"] = updated_cones
                            st.session_state.cone_status[position_key]["last_updated"] = f"{datetime.now().strftime('%H:%M')} by {active_user} (edited)"
                            
                            # Clear editing state
                            st.session_state[f"editing_cone_{position_key}"] = False
                            st.success(f"Updated R{int(row)+1}C{int(col)+1}")
                            st.rerun()
                    
                    with cancel_col:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state[f"editing_cone_{position_key}"] = False
                            st.rerun()
        
        # Bulk operations
        st.subheader("🔧 Bulk Operations")
        bulk_col1, bulk_col2, bulk_col3 = st.columns(3)
        
        with bulk_col1:
            if st.button("🗑️ Clear All Cone Data", type="secondary"):
                if st.button("⚠️ Confirm Clear All", type="secondary"):
                    for position_key in st.session_state.cone_status:
                        st.session_state.cone_status[position_key] = {"cones": {}, "last_updated": None}
                    st.success("All cone data cleared!")
                    st.rerun()
        
        with bulk_col2:
            # Export cone data for backup before clearing
            if any(pos_data["cones"] for pos_data in st.session_state.cone_status.values()):
                cone_backup_data = []
                for position, data in st.session_state.cone_status.items():
                    if data["cones"]:
                        row, col = position.split("_")
                        for cone_num, status in data["cones"].items():
                            cone_backup_data.append({
                                "position": f"R{int(row)+1}C{int(col)+1}",
                                "cone_number": cone_num,
                                "status": status,
                                "last_updated": data["last_updated"]
                            })
                
                if cone_backup_data:
                    cone_backup_df = pd.DataFrame(cone_backup_data)
                    st.download_button(
                        "💾 Backup Cone Data",
                        cone_backup_df.to_csv(index=False).encode('utf-8'),
                        f"{kiln_name}_{firing_id}_cone_backup.csv",
                        "text/csv"
                    )
        
        with bulk_col3:
            # Quick cone summary
            total_positions = sum(1 for pos_data in st.session_state.cone_status.values() if pos_data["cones"])
            total_cones = sum(len(pos_data["cones"]) for pos_data in st.session_state.cone_status.values())
            st.metric("Positions Tracked", total_positions)
            st.metric("Total Cones", total_cones)
        
        # Cone status legend and recent updates
        st.subheader("📋 Cone Status Legend & Recent Updates")
        legend_col1, legend_col2 = st.columns(2)
        with legend_col1:
            st.write("🔴 Bent/Down/Overfired")
            st.write("🟡 Bending/Soft")
            st.write("⚪ Standing")
        with legend_col2:
            # Recent cone updates
            if any(pos_data["last_updated"] for pos_data in st.session_state.cone_status.values()):
                st.write("**Recent Updates:**")
                recent_updates = []
                for position, data in st.session_state.cone_status.items():
                    if data["last_updated"] and data["cones"]:
                        row, col = position.split("_")
                        cone_list = ", ".join([f"{cone}:{status}" for cone, status in data["cones"].items()])
                        recent_updates.append({
                            "position": f"R{int(row)+1}C{int(col)+1}",
                            "cones": cone_list,
                            "updated": data["last_updated"]
                        })
                
                # Sort by most recent and show top 5
                recent_updates.sort(key=lambda x: x["updated"], reverse=True)
                for update in recent_updates[:5]:
                    st.write(f"**{update['position']}:** {update['cones']}")
                    st.caption(f"*{update['updated']}*")

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
            
            # Display crew in a nice format with edit/delete options
            for idx, member in crew_df.iterrows():
                role_icons = {
                    "kiln_master": "👑", "lead_stoker": "🔥", "stoker": "🪵", 
                    "spotter": "👁️", "wood_prep": "🪓", "door_tender": "🧱", 
                    "floater": "🔄", "observer": "📝", "student": "🎓"
                }
                icon = role_icons.get(member['role'], "👤")
                
                with st.container():
                    member_col1, member_col2, member_col3, member_col4 = st.columns([2, 2, 2, 1])
                    with member_col1:
                        st.write(f"{icon} **{member['name']}**")
                        st.write(f"*{member['role'].replace('_', ' ').title()}*")
                    with member_col2:
                        st.write(f"**Shift:** {member['shift_start']} - {member['shift_end']}")
                        st.write(f"*Added by: {member.get('added_by', 'Unknown')}*")
                    with member_col3:
                        if member.get('notes'):
                            st.write(f"**Notes:** {member['notes']}")
                    with member_col4:
                        # Find actual index in crew list
                        crew_index = None
                        for i, crew_member in enumerate(st.session_state.crew):
                            if (crew_member['name'] == member['name'] and 
                                crew_member['role'] == member['role']):
                                crew_index = i
                                break
                        
                        if crew_index is not None:
                            if st.button("🗑️", key=f"remove_crew_{idx}", help="Remove crew member"):
                                st.session_state.crew.pop(crew_index)
                                st.success(f"Removed {member['name']}")
                                st.rerun()
                    st.divider()
            
            # Crew activity summary
            if st.session_state.log:
                st.subheader("📊 Crew Activity Summary")
                log_df = pd.DataFrame(st.session_state.log)
                activity_summary = log_df['logged_by'].value_counts()
                
                for person, count in activity_summary.items():
                    st.write(f"**{person}:** {count} log entries")

    # Enhanced Export with weather and safety data
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
            
            # Safety and historical export
            export_col4, export_col5 = st.columns(2)
            
            with export_col4:
                # Safety checklist export
                safety_data = pd.DataFrame([{
                    "firing_id": firing_id,
                    "safety_completed": sum(st.session_state.safety_checklist.values()),
                    "safety_total": len([k for k in st.session_state.safety_checklist.keys() if k.startswith('safety_')]),
                    "emergency_contacts": len(st.session_state.emergency_contacts)
                }])
                st.download_button(
                    "⚠️ Safety Report",
                    safety_data.to_csv(index=False).encode('utf-8'),
                    f"{kiln_name}_{firing_id}_safety.csv",
                    "text/csv"
                )
            
            with export_col5:
                # Save current firing to historical database
                if st.button("💾 Save to Historical Database"):
                    historical_firing = {
                        "firing_id": firing_id,
                        "kiln": kiln_name,
                        "date_completed": datetime.now().strftime("%Y-%m-%d"),
                        "log_data": log_df.to_dict('records')
                    }
                    st.session_state.historical_firings.append(historical_firing)
                    st.success(f"✅ {firing_id} saved to historical database!")
            
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
            
            # Master summary export with weather data
            st.subheader("📋 Enhanced Firing Summary")
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
                "primary_kiln_master": log_df['logged_by'].mode().iloc[0] if not log_df.empty else active_user,
                "weather_impact_entries": len(log_df[log_df.get('weather_impact', 'none') != 'none']) if 'weather_impact' in log_df.columns else 0,
                "safety_checklist_completed": sum(st.session_state.safety_checklist.values()),
                "incidents_logged": len(log_df[log_df['entry_type'] == 'incident']) if 'entry_type' in log_df.columns else 0
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
        
        ### 🆕 **New Features in Enhanced Version**
        - **Weather Integration**: Real-time atmospheric conditions and impact analysis
        - **Historical Comparison**: Compare current firing to previous successful firings
        - **Mobile-First Design**: Quick mobile logging optimized for phones/tablets
        - **Safety Integration**: Pre-firing checklists, emergency contacts, incident logging
        """)
        
        st.markdown("---")
        
        st.subheader("📖 Feature Guide")
        
        # Enhanced feature documentation
        with st.expander("📝 **Firing Log** - Enhanced with Weather Integration"):
            st.markdown("""
            **Primary logging interface with real-time weather correlation**
            
            **Enhanced Features:**
            - **Weather Impact Assessment**: Track how conditions affect your firing
            - **Automatic Weather Data**: Real-time temperature, humidity, pressure, wind
            - **Historical Context**: Compare current conditions to previous firings
            - **Mobile Quick Entry**: Optimized for phone/tablet use at the kiln
            
            **Weather Integration Benefits:**
            - Understand how humidity affects draft
            - Correlate wind conditions with firing behavior
            - Track atmospheric pressure impacts on combustion
            - Document weather-related firing decisions
            """)
        
        with st.expander("⚠️ **Safety Integration** - Comprehensive Risk Management"):
            st.markdown("""
            **Complete safety system for wood firing operations**
            
            **Safety Features:**
            - **Pre-firing Checklist**: Standardized safety verification before lighting
            - **Emergency Contacts**: Quick access to fire department, medical, supervisors
            - **Incident Logging**: Document near-misses and safety issues
            - **Integration**: Safety events automatically logged to firing record
            
            **Best Practices:**
            - Complete safety checklist before every firing
            - Update emergency contacts regularly
            - Log all incidents, even minor ones
            - Review safety data during post-firing analysis
            """)
        
        with st.expander("📊 **Historical Comparison** - Learning from Experience"):
            st.markdown("""
            **Compare current firing to your firing database in real-time**
            
            **Historical Features:**
            - **Real-time Comparison**: See what you did at similar temperatures before
            - **Pattern Recognition**: Identify successful firing strategies
            - **Import Previous Data**: Upload CSV files from past firings
            - **Success Insights**: Learn from your best firings
            
            **How to Use:**
            1. Import previous firing CSV files into the system
            2. During current firing, check History tab for similar temperature points
            3. Review actions taken in previous successful firings
            4. Apply lessons learned while respecting current conditions
            """)
        
        with st.expander("📱 **Mobile Mode** - Optimized for Kiln-side Use"):
            st.markdown("""
            **Quick logging interface designed for phones and tablets**
            
            **Mobile Features:**
            - **Single-screen Entry**: All essential data in one form
            - **Voice-to-Text**: Use speech input for hands-free logging
            - **Quick Actions**: Streamlined interface for rapid entry
            - **Weather Auto-include**: Automatically capture weather conditions
            
            **Mobile Best Practices:**
            - Enable mobile mode when actively firing
            - Use voice input for notes while stoking
            - Keep phone/tablet in protective case near kiln
            - Switch back to desktop mode for detailed analysis
            """)
        
        st.markdown("---")
        
        st.subheader("🏺 **About the Development**")
        
        st.markdown("""
        **WoodFirePro Enhanced** builds on real handwritten wood firing logs from experienced ceramic artists. 
        The new features address the most critical gaps identified by working potters: weather correlation, 
        learning from experience, mobile accessibility, and comprehensive safety management.
        
        **Managed and created by Alford Wayman of Creek Road Pottery LLC with the help of Claude and ChatGPT coding.**
        
        **Enhanced Features Philosophy:**
        - **Weather matters**: Atmospheric conditions critically affect wood firing success
        - **Experience is wisdom**: Digital access to your firing knowledge base
        - **Safety first**: Comprehensive risk management without bureaucracy  
        - **Mobile reality**: Most pottery studios need mobile-friendly tools
        
        **Built with ❤️ for the wood firing community**
        
        ---
        *"The kiln master's senses and experience are irreplaceable. Technology should document the journey, not dictate the destination."*
        
        **© 2025 Creek Road Pottery LLC | WoodFirePro Enhanced**
        """)

# Footer with enhanced status
current_time = datetime.now().strftime("%H:%M:%S")
weather_status = f"Weather: {current_weather['temperature']:.0f}°F, {current_weather['humidity']}%" if current_weather else "Weather: N/A"

st.markdown("---")
st.caption(f"🔥 WoodFirePro Enhanced - Active User: **{active_user}** | {weather_status} | Phase: **{phase}** | Mode: {'📱 Mobile' if st.session_state.mobile_mode else '💻 Desktop'} | Time: {current_time}")
