import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

# Wide page configuration
st.set_page_config(layout="wide", page_title="Express Entry Dashboard")

# --- 1. DATA LOADING ---
@st.cache_data(ttl=3600)
def load_data():
    url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and 'rounds' in data:
            df = pd.DataFrame(data['rounds'])
        else:
            return pd.DataFrame()

        # Cleaning and conversion
        df['drawDate'] = pd.to_datetime(df['drawDate'], errors='coerce')
        df['drawCRS'] = pd.to_numeric(df['drawCRS'], errors='coerce')
        df['drawSize'] = df['drawSize'].astype(str).str.replace(',', '', regex=False)
        df['drawSize'] = pd.to_numeric(df['drawSize'], errors='coerce')
        df['drawName'] = df['drawName'].fillna('General / Unspecified')
        
        # Remove rows without valid date
        df = df.dropna(subset=['drawDate'])
        
        return df.sort_values(by='drawDate', ascending=False)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.stop()

# --- 2. RESET LOGIC ---
# Define default values
DEFAULT_START = date(2025, 1, 1)
DEFAULT_END = date.today()

def reset_filters():
    st.session_state.user_score = None
    st.session_state.date_range = (DEFAULT_START, DEFAULT_END)
    st.session_state.all_programs_check = True

# --- 3. SIDEBAR (CONFIGURATION) ---
st.sidebar.header("⚙️ Configuration")

# Reset Button
if st.sidebar.button("🔄 Reset Filters", type="primary"):
    reset_filters()

st.sidebar.markdown("---")

# A. SCORE INPUT
st.sidebar.subheader("🎯 Your Profile")
user_score = st.sidebar.number_input(
    "Your CRS Score:", 
    min_value=0, 
    max_value=1200, 
    value=None, 
    placeholder="Ex: 481",
    step=1,
    key='user_score' 
)

st.sidebar.markdown("---")

# B. DATE FILTER
st.sidebar.subheader("📅 Date Range")

if 'date_range' not in st.session_state:
    st.session_state.date_range = (DEFAULT_START, DEFAULT_END)

date_range_input = st.sidebar.date_input(
    "Time Period:",
    value=st.session_state.date_range, 
    min_value=df['drawDate'].min().date(),
    max_value=date.today(),
    format="DD/MM/YYYY",
    key='date_range'
)

# Tuple validation
if len(date_range_input) == 2:
    start_date, end_date = date_range_input
else:
    start_date, end_date = DEFAULT_START, DEFAULT_END

st.sidebar.markdown("---")

# C. PROGRAM FILTER
st.sidebar.subheader("📋 Draw Types")
unique_programs = sorted(df['drawName'].unique())

with st.sidebar.expander("Select Programs", expanded=False):
    if 'all_programs_check' not in st.session_state:
        st.session_state.all_programs_check = True
        
    all_selected = st.checkbox("Select All", value=True, key='all_programs_check')
    
    if all_selected:
        selected_programs = unique_programs
    else:
        selected_programs = st.multiselect("Programs:", unique_programs, default=unique_programs)

# --- 4. FILTERING ---
mask = (
    (df['drawDate'].dt.date >= start_date) & 
    (df['drawDate'].dt.date <= end_date) &
    (df['drawName'].isin(selected_programs))
)
df_filtered = df[mask]

# --- 5. DASHBOARD ---
st.title("🍁 Analysis: CRS Score vs. Invitation Volume")

if df_filtered.empty:
    st.warning("No data available for this date range.")
    st.stop()

# Function to create dual-axis chart
def create_dual_axis_chart(data, title, score_benchmark):
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Bars (Invitations) -> Secondary Axis (Right)
    fig.add_trace(
        go.Bar(
            x=data['drawDate'], 
            y=data['drawSize'], 
            name="Invitations",
            marker_color='rgba(135, 206, 250, 0.4)', # Light blue transparent
            hoverinfo="y+x"
        ),
        secondary_y=True
    )

    # 2. Line (CRS Score) -> Primary Axis (Left)
    fig.add_trace(
        go.Scatter(
            x=data['drawDate'], 
            y=data['drawCRS'], 
            name="CRS Score",
            mode='lines+markers',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ),
        secondary_y=False
    )

    # 3. User Line (If exists)
    if score_benchmark is not None:
        fig.add_hline(
            y=score_benchmark, 
            line_dash="dot", 
            line_color="red", 
            secondary_y=False,
            annotation_text="You", 
            annotation_position="top left"
        )
        # Adjust Y range
        all_scores = list(data['drawCRS']) + [score_benchmark]
        min_y, max_y = min(all_scores), max(all_scores)
        fig.update_yaxes(range=[min_y - 20, max_y + 20], secondary_y=False)

    # Clean Visual Config
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        title=dict(text=f"CRS vs Volume", font=dict(size=12), x=0.5),
        hovermode="x unified"
    )
    
    # Axes
    fig.update_yaxes(title_text=None, secondary_y=False) # Left
    fig.update_yaxes(showgrid=False, secondary_y=True)   # Right

    return fig

# --- GRID LOGIC (4 COLUMNS) ---
programs_list = []
for name, group in df_filtered.groupby('drawName'):
    if not group.empty:
        programs_list.append((name, group.sort_values('drawDate')))

def chunked(iterable, n):
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]

# Iterate in batches of 4
for batch in chunked(programs_list, 4):
    cols = st.columns(4)
    
    for i, (program_name, group_data) in enumerate(batch):
        with cols[i]:
            with st.container(border=True):
                # Program Title
                st.markdown(f"**{program_name}**")
                
                # Get last data
                last_row = group_data.iloc[-1]
                last_crs = last_row['drawCRS']
                last_date = last_row['drawDate'].strftime("%Y-%m-%d")
                
                # WARNING 1: DATE
                st.info(f"📅 Last Draw: {last_date}")

                # WARNING 2: COMPARISON
                if user_score is not None and user_score > 0:
                    diff = user_score - last_crs
                    if diff >= 0:
                        st.success(f"✅ Eligible (+{diff:.0f})")
                    else:
                        st.error(f"❌ Short by {abs(diff):.0f} pts")
                else:
                    st.warning("➖ Comparison: --")

                # CHART
                fig = create_dual_axis_chart(group_data, program_name, user_score)
                st.plotly_chart(fig, use_container_width=True)

# Table at the bottom
with st.expander("📂 View Data Table"):
    st.dataframe(df_filtered[['drawDate', 'drawName', 'drawCRS', 'drawSize']], use_container_width=True)