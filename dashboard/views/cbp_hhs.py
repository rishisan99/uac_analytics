import streamlit as st
from utils.data_loader import load_data, filter_by_date, get_kpi_snapshot, get_granularity
from components.kpi_cards import render_kpi_row, render_kpi_section_header
from components.charts import (
    chart_transfers_vs_discharges,
    chart_discharge_offset_ratio,
    chart_transfer_discharge_scatter
)


def render(start_date, end_date, granularity):
    """
    CBP vs HHS Comparison page.
    Focuses on the flow between the two systems —
    are transfers and discharges staying in balance?

    Parameters received from app.py sidebar:
        start_date  — user selected start date
        end_date    — user selected end date
        granularity — 'Daily', 'Weekly', or 'Monthly'
    """

    # ── Page Header 
    st.markdown("## 🔄 CBP vs HHS Comparison")
    st.markdown(
        "Analyzing the flow of children between CBP custody and HHS care. "
        "When transfers outpace discharges, the system fills up. "
        "When discharges outpace transfers, the system relieves pressure."
    )
    st.divider()

    # ── Load & Filter Data 
    df      = load_data()
    df      = filter_by_date(df, start_date, end_date)
    df_gran = get_granularity(df, granularity)
    kpis    = get_kpi_snapshot(df)

    if df.empty:
        st.warning("No data found for the selected date range. Please adjust the filters.")
        return

    # ── KPI Cards Row 
    render_kpi_section_header(kpis["as_of_date"])
    render_kpi_row(kpis)

    st.divider()

    # ── Row 1: Flow Summary Metrics 
    # quick numbers at a glance before the charts
    st.markdown("#### Flow Summary for Selected Period")

    total_transferred = int(df["cbp_transferred"].sum())
    total_discharged  = int(df["hhs_discharged"].sum())
    net_flow          = total_transferred - total_discharged
    avg_daily_trans   = round(df["cbp_transferred"].mean(), 1)
    avg_daily_disc    = round(df["hhs_discharged"].mean(), 1)
    days_draining     = int((df["discharge_offset_ratio"] >= 1).sum())
    days_filling      = int((df["discharge_offset_ratio"] < 1).sum())

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        label = "Total Transferred to HHS",
        value = f"{total_transferred:,}"
    )
    m2.metric(
        label = "Total Discharged from HHS",
        value = f"{total_discharged:,}",
        delta = f"{total_discharged - total_transferred:+,} vs transfers"
    )
    m3.metric(
        label = "Days System Was Draining",
        value = f"{days_draining}",
        delta = f"{days_draining / len(df) * 100:.1f}% of period"
    )
    m4.metric(
        label = "Days System Was Filling",
        value = f"{days_filling}",
        delta = f"{days_filling / len(df) * 100:.1f}% of period",
        delta_color = "inverse"   # red for filling days — higher is worse
    )

    st.divider()

    # ── Row 2: Transfers vs Discharges Over Time 
    st.markdown("#### Transfers into HHS vs Discharges from HHS")
    st.caption(
        "7-day rolling averages. Pink = transfers in, green = discharges out. "
        "Shaded gap shows which side is winning on any given stretch."
    )
    fig_flow = chart_transfers_vs_discharges(df_gran)
    st.plotly_chart(fig_flow, use_container_width=True)

    # ── Row 3: Offset Ratio 
    st.markdown("#### Discharge Offset Ratio (30-Day Rolling)")
    st.caption(
        "Above 1.0 = HHS is discharging faster than it receives — system relieving. "
        "Below 1.0 = transfers outpacing discharges — system under pressure."
    )
    fig_ratio = chart_discharge_offset_ratio(df)
    st.plotly_chart(fig_ratio, use_container_width=True)

    # ── Row 4: Scatter + Insight side by side 
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("#### Transfers vs Discharges — Day-Level Scatter")
        st.caption(
            "Each dot is one reporting day. Dots above the diagonal = "
            "more discharged than transferred that day. "
            "Colored by year to show how the relationship shifted."
        )
        fig_scatter = chart_transfer_discharge_scatter(df)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_right:
        st.markdown("#### Period Interpretation")

        # color code the net flow callout
        if net_flow > 0:
            flow_status = "🔴 Net Inflow"
            flow_msg    = (
                f"Over this period, **{net_flow:,} more children** entered HHS "
                f"than were discharged. The system absorbed more than it released."
            )
        else:
            flow_status = "🟢 Net Outflow"
            flow_msg    = (
                f"Over this period, **{abs(net_flow):,} more children** were "
                f"discharged than transferred in. The system relieved pressure."
            )

        st.markdown(f"**{flow_status}**")
        st.markdown(flow_msg)

        st.markdown("---")

        # avg daily comparison
        st.markdown("**Daily Averages**")
        st.markdown(f"- Avg daily transfers: **{avg_daily_trans:.0f}** children")
        st.markdown(f"- Avg daily discharges: **{avg_daily_disc:.0f}** children")
        st.markdown(f"- Avg net per day: **{avg_daily_trans - avg_daily_disc:+.1f}**")

        st.markdown("---")

        # offset ratio interpretation
        current_ratio = kpis["offset_ratio"]
        st.markdown("**Current Offset Ratio**")
        if current_ratio >= 1:
            st.success(f"{current_ratio:.3f} — Discharges keeping up ✓")
        else:
            st.error(f"{current_ratio:.3f} — Transfers outpacing discharges ✗")

    # ── Row 5: Key Takeaway 
    st.divider()
    st.markdown("#### 📌 Key Takeaway")

    corr = round(df["cbp_transferred"].corr(df["hhs_discharged"]), 3)

    st.info(
        f"Transfer-discharge correlation: **{corr}** — "
        f"{'strong' if corr > 0.7 else 'moderate' if corr > 0.4 else 'weak'} alignment "
        f"between inflow and outflow. "
        f"The system was **draining on {days_draining} of {len(df)} days** "
        f"({days_draining / len(df) * 100:.1f}%) within the selected period."
    )