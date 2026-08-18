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
DEFAULT_START = date(2026, 1, 1)
DEFAULT_END = date.today()

def reset_filters():
    st.session_state.user_score = None
    st.session_state.date_range = (DEFAULT_START, DEFAULT_END)
    st.session_state.all_programs_check = True

# --- 3. SIDEBAR (CONFIGURATION) ---
st.sidebar.header("⚙️ Configuration")

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

# --- 4. STEP 1 FILTERING (DATE & PROGRAM) ---
mask_step1 = (
    (df['drawDate'].dt.date >= start_date) & 
    (df['drawDate'].dt.date <= end_date) &
    (df['drawName'].isin(selected_programs))
)
df_step1 = df[mask_step1]

# --- 5. DYNAMIC TOTALS FILTER ---
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Totals Filter")

if not df_step1.empty:
    stats = df_step1.groupby('drawName').agg(
        total_draws=('drawDate', 'count'),
        total_invites=('drawSize', 'sum')
    )
    max_draws = int(stats['total_draws'].max())
    max_invites = int(stats['total_invites'].max())
else:
    max_draws, max_invites = 1, 1

safe_max_draws = max(1, max_draws)
safe_max_invites = max(1, max_invites)
min_inv_val = 1 if safe_max_invites > 0 else 0

draws_range = st.sidebar.slider(
    "Cantidad de Draws:", 
    min_value=1, 
    max_value=safe_max_draws, 
    value=(1, safe_max_draws)
)

invites_range = st.sidebar.slider(
    "Cantidad de Invitaciones:", 
    min_value=min_inv_val, 
    max_value=safe_max_invites, 
    value=(min_inv_val, safe_max_invites)
)

# Apply totals filter
if not df_step1.empty:
    valid_programs = stats[
        (stats['total_draws'] >= draws_range[0]) & (stats['total_draws'] <= draws_range[1]) &
        (stats['total_invites'] >= invites_range[0]) & (stats['total_invites'] <= invites_range[1])
    ].index.tolist()
    df_filtered = df_step1[df_step1['drawName'].isin(valid_programs)]
else:
    df_filtered = pd.DataFrame()


# --- 6. DASHBOARD ---
st.title("🍁 Analysis: CRS Score vs. Invitation Volume")

if df_filtered.empty:
    st.warning("No data available for these filter settings.")
    st.stop()

def create_dual_axis_chart(data, title, score_benchmark):
    data = data.copy().sort_values('drawDate')
    data['CRS_Trend'] = data['drawCRS'].rolling(window=5, min_periods=1).mean()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=data['drawDate'], 
            y=data['drawSize'], 
            name="Invitations",
            marker_color='rgba(135, 206, 250, 0.4)',
            hoverinfo="y+x"
        ),
        secondary_y=True
    )

    fig.add_trace(
        go.Scatter(
            x=data['drawDate'], 
            y=data['CRS_Trend'], 
            name="Trend (MA 5)",
            mode='lines',
            line=dict(color='rgba(255, 127, 14, 0.8)', width=2, dash='dot'),
            hoverinfo="skip"
        ),
        secondary_y=False
    )

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

    if score_benchmark is not None:
        fig.add_hline(
            y=score_benchmark, 
            line_dash="dot", 
            line_color="red", 
            secondary_y=False,
            annotation_text="You", 
            annotation_position="top left"
        )
        all_scores = list(data['drawCRS']) + [score_benchmark]
        min_y, max_y = min(all_scores), max(all_scores)
        fig.update_yaxes(range=[min_y - 20, max_y + 20], secondary_y=False)

    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        title=dict(text=f"CRS vs Volume", font=dict(size=12), x=0.5),
        hovermode="x unified"
    )
    
    # Formato abreviado mes-año
    fig.update_xaxes(type='date', tickformat="%b-%Y")
    fig.update_yaxes(title_text=None, secondary_y=False)
    fig.update_yaxes(showgrid=False, tickformat="s", secondary_y=True)

    return fig

# --- GRID LOGIC (3 COLUMNS) ---
programs_list = []
for name, group in df_filtered.groupby('drawName'):
    if not group.empty:
        programs_list.append((name, group.sort_values('drawDate')))

programs_list.sort(key=lambda x: x[1]['drawDate'].max(), reverse=True)

def chunked(iterable, n):
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]

for batch in chunked(programs_list, 3):
    cols = st.columns(3)
    
    for i, (program_name, group_data) in enumerate(batch):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{program_name}**")
                
                total_draws = len(group_data)
                total_invites = group_data['drawSize'].sum()
                st.caption(f"📊 Draws: {total_draws}")
                st.caption(f"✉️ Invitaciones: {total_invites:,.0f}")
                
                last_row = group_data.iloc[-1]
                last_date_obj = last_row['drawDate'].date()
                last_date = last_date_obj.strftime("%Y-%m-%d")
                
                today = date.today()
                days_diff = (today - last_date_obj).days

                if days_diff == 0:
                    st.error(f"📅 Last Draw: {last_date}")
                elif 0 < days_diff <= 5:
                    st.success(f"📅 Last Draw: {last_date}")
                else:
                    st.info(f"📅 Last Draw: {last_date}")

                fig = create_dual_axis_chart(group_data, program_name, user_score)
                st.plotly_chart(fig, use_container_width=True)

with st.expander("📂 View Data Table"):
    st.dataframe(df_filtered[['drawDate', 'drawName', 'drawCRS', 'drawSize']], use_container_width=True)
