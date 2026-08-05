import streamlit as st
from datetime import date
from utils.data_loader import load_data, get_date_bounds
from views import overview, cbp_hhs, net_intake, kpi_summary


# ── Page Configuration 
# must be the first streamlit call in the file
st.set_page_config(
    page_title = "UAC System Analytics",
    page_icon  = "👥",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)


# ── Hide default streamlit chrome 
# removes the hamburger menu and footer for a cleaner look
st.markdown("""
    <style>
        #MainMenu  {visibility: hidden;}
        footer     {visibility: hidden;}
        header     {visibility: hidden;}

        /* tighten up top padding */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1rem;
        }

        /* style the sidebar navigation buttons */
        div[data-testid="stSidebarContent"] .stButton button {
            width: 100%;
            text-align: left;
            background-color: transparent;
            border: none;
            color: #e8e8f0;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
        }
        div[data-testid="stSidebarContent"] .stButton button:hover {
            background-color: #2a2d3e;
        }
    </style>
""", unsafe_allow_html=True)


# ── Sidebar ──
with st.sidebar:

    # dashboard title and subtitle
    st.markdown("""
        <div style="padding: 0 0 16px 0;">
            <div style="font-size: 20px; font-weight: 700; color: #e8e8f0;">
                👥 UAC Analytics
            </div>
            <div style="font-size: 11px; color: #a0a0b8; margin-top: 4px;">
                System Capacity & Care Load
            </div>
            <div style="font-size: 10px; color: #a0a0b8;">
                U.S. Dept of Health & Human Services
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Date Range Filter 
    st.markdown("#### 📅 Date Range")

    # load data once to get the real min/max dates
    df_full = load_data()
    data_min, data_max = get_date_bounds(df_full)

    # default to full range on first load
    start_date = st.date_input(
        label     = "Start Date",
        value     = data_min,
        min_value = data_min,
        max_value = data_max
    )

    end_date = st.date_input(
        label     = "End Date",
        value     = data_max,
        min_value = data_min,
        max_value = data_max
    )

    # guard against invalid range
    if start_date > end_date:
        st.error("Start date must be before end date.")
        st.stop()

    st.divider()

    # ── Granularity Toggle ───────
    st.markdown("#### 🔍 Time Granularity")

    granularity = st.radio(
        label      = "Aggregate data by",
        options    = ["Daily", "Weekly", "Monthly"],
        index      = 0,           # default to Daily
        horizontal = False
    )

    st.divider()

    # ── Page Navigation ──
    st.markdown("#### 🗂 Navigation")

    # use session state to remember which page is active
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Overview"

    pages = {
        "📊 Overview":      "Overview",
        "🔄 CBP vs HHS":    "CBP vs HHS",
        "📦 Net Intake":    "Net Intake",
        "📈 KPI Summary":   "KPI Summary"
    }

    for label, page_name in pages.items():
        # highlight the active page button
        is_active = st.session_state.active_page == page_name
        if st.button(
            label,
            key      = page_name,
            type     = "primary" if is_active else "secondary"
        ):
            st.session_state.active_page = page_name
            st.rerun()

    st.divider()

    # ── Data Info ─────
    st.markdown("#### ℹ️ Data Info")

    # show how many rows fall in the selected range
    df_filtered = df_full[
        (df_full["date"].dt.date >= start_date) &
        (df_full["date"].dt.date <= end_date)
    ]

    st.markdown(f"""
        <div style="font-size: 12px; color: #a0a0b8; line-height: 1.8;">
            <b>Source:</b> HHS UAC Program<br>
            <b>Full range:</b> {data_min} → {data_max}<br>
            <b>Selected days:</b> {len(df_filtered):,}<br>
            <b>Total days:</b> {len(df_full):,}
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Footer 
    st.markdown("""
        <div style="font-size: 10px; color: #555; text-align: center; padding-top: 8px;">
            Built for HHS UAC Program Analytics<br>
            Data: 2023 – 2025
        </div>
    """, unsafe_allow_html=True)


# ── Main Content — Route to Active Page ───
active = st.session_state.active_page

if active == "Overview":
    overview.render(start_date, end_date, granularity)

elif active == "CBP vs HHS":
    cbp_hhs.render(start_date, end_date, granularity)

elif active == "Net Intake":
    net_intake.render(start_date, end_date, granularity)

elif active == "KPI Summary":
    kpi_summary.render(start_date, end_date, granularity)