import streamlit as st
from utils.data_loader import load_data, filter_by_date, get_kpi_snapshot, get_granularity
from components.kpi_cards import render_kpi_row, render_kpi_section_header
from components.charts import (
    chart_net_intake,
    chart_cumulative_backlog,
    chart_monthly_net_intake
)


def render(start_date, end_date, granularity):
    """
    Net Intake & Backlog page.
    Focuses on whether the system is filling up or draining,
    and how that imbalance accumulates into a long-term backlog.

    Parameters received from app.py sidebar:
        start_date  — user selected start date
        end_date    — user selected end date
        granularity — 'Daily', 'Weekly', or 'Monthly'
    """

    # ── Page Header ───────
    st.markdown("## 📦 Net Intake & Backlog")
    st.markdown(
        "Tracking whether more children are entering HHS than leaving, "
        "and whether that imbalance is building into a sustained backlog. "
        "Net Intake = Transfers into HHS − Discharges from HHS."
    )
    st.divider()

    # ── Load & Filter Data ─
    df      = load_data()
    df      = filter_by_date(df, start_date, end_date)
    df_gran = get_granularity(df, granularity)
    kpis    = get_kpi_snapshot(df)

    if df.empty:
        st.warning("No data found for the selected date range. Please adjust the filters.")
        return

    # ── KPI Cards Row ──────
    render_kpi_section_header(kpis["as_of_date"])
    render_kpi_row(kpis)

    st.divider()

    # ── Row 1: Period Summary Metrics ─────────────────────
    st.markdown("#### Net Intake Summary for Selected Period")

    filling_days  = int((df["net_daily_intake"] > 0).sum())
    draining_days = int((df["net_daily_intake"] <= 0).sum())
    total_days    = len(df)
    avg_net       = round(df["net_daily_intake"].mean(), 1)
    peak_fill     = int(df["net_daily_intake"].max())
    peak_drain    = int(df["net_daily_intake"].min())
    peak_backlog  = round(df["cumulative_net_intake"].max(), 0)
    current_backlog = round(df["cumulative_net_intake"].iloc[-1], 0)

    m1, m2, m3, m4, m5 = st.columns(5)

    m1.metric(
        label = "Filling Days",
        value = f"{filling_days}",
        delta = f"{filling_days / total_days * 100:.1f}% of period",
        delta_color = "inverse"   # more filling days = worse
    )
    m2.metric(
        label = "Draining Days",
        value = f"{draining_days}",
        delta = f"{draining_days / total_days * 100:.1f}% of period"
    )
    m3.metric(
        label = "Avg Net Intake/Day",
        value = f"{avg_net:+.1f}",
        delta = "filling" if avg_net > 0 else "draining",
        delta_color = "inverse" if avg_net > 0 else "normal"
    )
    m4.metric(
        label = "Peak Single-Day Fill",
        value = f"{peak_fill:+,}"
    )
    m5.metric(
        label = "Peak Single-Day Drain",
        value = f"{peak_drain:+,}"
    )

    st.divider()

    # ── Row 2: Daily Net Intake Bar Chart ─────────────────
    st.markdown("#### Daily Net Intake")
    st.caption(
        "Each bar is one reporting day. "
        "Red = more children came in than left. "
        "Green = more children left than came in. "
        "Purple line = 14-day rolling average trend."
    )
    fig_net = chart_net_intake(df_gran)
    st.plotly_chart(fig_net, use_container_width=True)

    # ── Row 3: Cumulative Backlog ──────────────────────────
    st.markdown("#### Cumulative Backlog Over Time")
    st.caption(
        "Running total of net intake. Rising = backlog building. "
        "Falling = backlog clearing. "
        "The peak of this line is when system pressure was at its worst."
    )
    fig_backlog = chart_cumulative_backlog(df)
    st.plotly_chart(fig_backlog, use_container_width=True)

    # ── Row 4: Monthly Net + Backlog Status side by side ──
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("#### Monthly Net Intake Totals")
        st.caption(
            "Red months added to the backlog overall. "
            "Green months relieved it. "
            "Consecutive red months = sustained system pressure."
        )
        fig_monthly = chart_monthly_net_intake(df)
        st.plotly_chart(fig_monthly, use_container_width=True)

    with col_right:
        st.markdown("#### Backlog Status")

        # peak backlog callout
        peak_date = df.loc[
            df["cumulative_net_intake"].idxmax(), "date"
        ].strftime("%B %d, %Y")

        st.markdown("**Peak Backlog**")
        st.markdown(f"- Value: **{peak_backlog:+,.0f}** children")
        st.markdown(f"- Date:  **{peak_date}**")

        st.markdown("---")

        # current backlog status
        st.markdown("**Current Backlog**")
        if current_backlog > 0:
            st.error(f"{current_backlog:+,.0f} — still above zero")
        else:
            st.success(f"{current_backlog:+,.0f} — fully cleared ✓")

        st.markdown("---")

        # how much of the backlog has been recovered
        if peak_backlog > 0:
            recovered_pct = ((peak_backlog - current_backlog) / peak_backlog * 100)
            st.markdown("**Recovery Progress**")
            st.progress(
                min(int(recovered_pct), 100),
                text=f"{recovered_pct:.1f}% of peak backlog cleared"
            )

        st.markdown("---")

        # backlog rate status from KPIs
        st.markdown("**Current Backlog Rate**")
        backlog_rate = kpis["backlog_rate"]
        if backlog_rate > 0:
            st.warning(f"{backlog_rate:+.2f} children/day — still growing")
        else:
            st.success(f"{backlog_rate:+.2f} children/day — shrinking ✓")

    # ── Row 5: Key Takeaway 
    st.divider()
    st.markdown("#### 📌 Key Takeaway")

    # find if backlog ever fully cleared in selected range
    cleared = df[df["cumulative_net_intake"] <= 0]

    if len(cleared) > 0:
        cleared_date = cleared["date"].iloc[0].strftime("%B %d, %Y")
        st.success(
            f"Within the selected period, the cumulative backlog peaked at "
            f"**{peak_backlog:+,.0f} children** on **{peak_date}**. "
            f"It fully cleared by **{cleared_date}**. "
            f"The system averaged **{avg_net:+.1f} net children/day** overall."
        )
    else:
        st.warning(
            f"Within the selected period, the cumulative backlog peaked at "
            f"**{peak_backlog:+,.0f} children** on **{peak_date}**. "
            f"The backlog has not fully cleared — currently at "
            f"**{current_backlog:+,.0f}**. "
            f"The system averaged **{avg_net:+.1f} net children/day** overall."
        )