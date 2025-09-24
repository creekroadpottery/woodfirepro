# WoodFirePro 🔥

**Professional Wood Firing Toolkit for Ceramic Artists**

A comprehensive digital logging and analysis system designed specifically for wood firing ceramic artists. Built by analyzing real handwritten firing logs from experienced potters to create tools that enhance traditional knowledge rather than replace it.

## Features

### 📝 Comprehensive Firing Documentation
- **Multi-sensor temperature tracking** (front, middle, back spy holes + stack)
- **Atmosphere control monitoring** (damper position, air intake, atmosphere type)
- **Visual observation logging** (flame character, spy hole colors, draft sounds)
- **Action tracking** (document every decision and intervention)
- **Entry categorization** (observations, stokes, damper changes, problems, milestones)

### 🪵 Real-time Wood Consumption Tracking
- Log wood usage as it happens during firing
- Track species, sizes, quantities, and firebox locations  
- Analyze consumption patterns across firing phases
- Separate from inventory - tracks actual usage

### 🎯 Interactive Kiln Cone Mapping
- Visual 6x8 grid representation of kiln interior
- Click-to-update cone status tracking
- Color-coded progression indicators
- Multiple cones per position with timestamps

### 👥 Team Collaboration Tools
- Role-based crew management (Kiln Master, Stokers, Spotters, etc.)
- User attribution for all log entries
- Shift tracking and handoff documentation
- Activity summaries by team member

### 📊 Data Analysis & Visualization
- Temperature progression charts across all sensors
- Atmosphere control tracking over time
- Wood consumption rate analysis
- Firing statistics and duration tracking
- Export capabilities for long-term comparison

### ⏲️ Phase-Aware Timing System
- Smart timer with firing phase suggestions
- Visual progress tracking and alerts
- Customizable intervals based on firing stage

## Philosophy

**WoodFirePro** operates on the principle that **the kiln master's expertise is irreplaceable**. This tool provides no automatic suggestions or algorithmic interference - it exists purely to document the journey and support team collaboration while leaving all firing decisions to experienced potters.

## Installation & Usage

### Requirements
- Python 3.7+
- Streamlit
- Pandas

### Quick Start
```bash
git clone https://github.com/yourusername/woodfirepro.git
cd woodfirepro
pip install -r requirements.txt
streamlit run woodfirepro.py
