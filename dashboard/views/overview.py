import streamlit as st
from utils.data_loader import load_data, filter_by_date, get_kpi_snapshot, get_granularity
from components.kpi_cards import render_kpi_row, render_kpi_section_header
from components.charts import (
    chart_hhs_trend,
    chart_total_system_load,
    chart_stress_zone,
    chart_monthly_avg_hhs
)


def render(start_date, end_date, granularity):
    """
    System Load Overview page.
    Shows the big picture — how the entire care system has
    changed across the 2023-2025 timeline.

    Parameters received from app.py sidebar:
        start_date  — user selected start date
        end_date    — user selected end date
        granularity — 'Daily', 'Weekly', or 'Monthly'
    """

    # ── Page Header ──────────────────────────────────────
    st.markdown("## 📊 System Load Overview")
    st.markdown(
        "High-level view of total care load, HHS trends, "
        "and system stress across the full timeline."
    )
    st.divider()

    # ── Load & Filter Data ────────────────────────────────
    df      = load_data()
    df      = filter_by_date(df, start_date, end_date)
    df_gran = get_granularity(df, granularity)
    kpis    = get_kpi_snapshot(df)   # KPIs always use daily data, not resampled

    # guard — nothing to show if date range returns empty
    if df.empty:
        st.warning("No data found for the selected date range. Please adjust the filters.")
        return

    # ── KPI Cards Row ─────────────────────────────────────
    render_kpi_section_header(kpis["as_of_date"])
    render_kpi_row(kpis)

    st.divider()

    # ── Row 1: HHS Care Trend ─────────────────────────────
    st.markdown("#### Children in HHS Care Over Time")
    st.caption(
        "Daily care load with 7-day and 14-day rolling averages. "
        "Faint line is raw daily count — solid lines show the real trend."
    )
    fig_hhs = chart_hhs_trend(df_gran)
    st.plotly_chart(fig_hhs, use_container_width=True)

    # ── Row 2: Two charts side by side ───────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Total System Load (CBP + HHS)")
        st.caption(
            "Combined count of all children the system is responsible "
            "for on any given day."
        )
        fig_load = chart_total_system_load(df_gran)
        st.plotly_chart(fig_load, use_container_width=True)

    with col_right:
        st.markdown("#### Stress Periods — 90th Percentile Zone")
        st.caption(
            "Red shaded area = days where HHS care load crossed the "
            "top 10% threshold. These are high-pressure periods."
        )
        fig_stress = chart_stress_zone(df)  # stress uses daily data for threshold accuracy
        st.plotly_chart(fig_stress, use_container_width=True)

    # ── Row 3: Monthly Average Bar ────────────────────────
    st.markdown("#### Monthly Average HHS Care — By Year")
    st.caption(
        "Each bar is the average care load for that month. "
        "Color = year, making year-over-year comparison easy."
    )
    fig_monthly = chart_monthly_avg_hhs(df)
    st.plotly_chart(fig_monthly, use_container_width=True)

    # ── Row 4: Key Takeaway Box ───────────────────────────
    st.divider()

    # compute the headline numbers for the callout
    peak_val  = int(df["hhs_care"].max())
    peak_date = df.loc[df["hhs_care"].idxmax(), "date"].strftime("%B %d, %Y")
    latest    = int(df["hhs_care"].iloc[-1])
    pct_drop  = abs((latest - peak_val) / peak_val * 100)

    st.markdown("#### 📌 Key Takeaway")
    st.info(
        f"Within the selected date range, HHS care load peaked at "
        f"**{peak_val:,} children** on **{peak_date}**. "
        f"By the end of the period it had fallen to **{latest:,}** — "
        f"a **{pct_drop:.1f}% decline** from peak. "
        f"The system is currently in a **{'low-pressure' if latest < df['hhs_care'].quantile(0.5) else 'high-pressure'}** state."
    )