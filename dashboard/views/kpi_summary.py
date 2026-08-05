import streamlit as st
import pandas as pd
from utils.data_loader import load_data, filter_by_date, get_kpi_snapshot
from components.kpi_cards import render_kpi_row, render_kpi_section_header
from components.charts import chart_kpi_timeline, chart_stress_zone, chart_volatility


def render(start_date, end_date, granularity):
    """
    KPI Summary page.
    Deep dive into all 5 KPIs — each shown with its full
    timeline, current value, peak, and plain-english interpretation.

    Parameters received from app.py sidebar:
        start_date  — user selected start date
        end_date    — user selected end date
        granularity — 'Daily', 'Weekly', or 'Monthly'
    """

    # ── Page Header 
    st.markdown("## 📈 KPI Summary")
    st.markdown(
        "Detailed view of all 5 Key Performance Indicators. "
        "Each KPI tracks a different dimension of system health — "
        "together they give a complete picture of care capacity."
    )
    st.divider()

    # ── Load & Filter Data ─
    df   = load_data()
    df   = filter_by_date(df, start_date, end_date)
    kpis = get_kpi_snapshot(df)

    if df.empty:
        st.warning("No data found for the selected date range. Please adjust the filters.")
        return

    # ── KPI Cards Row 
    render_kpi_section_header(kpis["as_of_date"])
    render_kpi_row(kpis)

    st.divider()

    # ── KPI 1 — Total Children Under Care 
    st.markdown("### KPI 1 — Total Children Under Care")

    col_left, col_right = st.columns([3, 1])

    with col_left:
        fig_k1 = chart_kpi_timeline(
            df         = df,
            kpi_col    = "total_system_load",
            title      = "Total Children Under Care (CBP + HHS)",
            color      = "#4361ee",
            y_label    = "Total Children"
        )
        st.plotly_chart(fig_k1, use_container_width=True)

    with col_right:
        st.markdown("**What it measures**")
        st.markdown(
            "Total system-wide responsibility — every child "
            "in either CBP custody or HHS care on a given day."
        )
        st.markdown("---")
        st.markdown("**Period Stats**")
        st.markdown(f"- Current: **{kpis['total_care']:,}**")
        st.markdown(f"- Peak:    **{int(df['total_system_load'].max()):,}**")
        st.markdown(f"- Average: **{int(df['total_system_load'].mean()):,}**")
        st.markdown("---")
        st.markdown("**Healthy signal**")
        st.markdown("Declining trend with no sharp upward spikes.")

    st.divider()

    # ── KPI 2 — Net Intake Pressure 
    st.markdown("### KPI 2 — Net Intake Pressure Score")

    col_left, col_right = st.columns([3, 1])

    with col_left:
        fig_k2 = chart_kpi_timeline(
            df             = df,
            kpi_col        = "net_intake_pressure",
            title          = "Net Intake Pressure (30-Day Rolling, % of HHS Load)",
            color          = "#f72585",
            y_label        = "Pressure (%)",
            reference_line = 0.0
        )
        st.plotly_chart(fig_k2, use_container_width=True)

    with col_right:
        st.markdown("**What it measures**")
        st.markdown(
            "30-day rolling net intake as a percentage of "
            "current HHS load. Positive = system filling, "
            "negative = system draining."
        )
        st.markdown("---")
        st.markdown("**Period Stats**")
        pressure = kpis["net_pressure"]
        st.markdown(f"- Current: **{pressure:+.2f}%**")
        st.markdown(f"- Peak:    **{df['net_intake_pressure'].max():+.2f}%**")
        st.markdown(f"- Min:     **{df['net_intake_pressure'].min():+.2f}%**")
        st.markdown("---")
        st.markdown("**Healthy signal**")
        st.markdown("Value at or below 0 — system draining or balanced.")
        if pressure <= 0:
            st.success("Currently healthy ✓")
        else:
            st.error("Currently under pressure ✗")

    st.divider()

    # ── KPI 3 — Care Load Volatility Index ──
    st.markdown("### KPI 3 — Care Load Volatility Index")

    col_left, col_right = st.columns([3, 1])

    with col_left:
        fig_k3 = chart_volatility(df)
        st.plotly_chart(fig_k3, use_container_width=True)

    with col_right:
        st.markdown("**What it measures**")
        st.markdown(
            "14-day rolling standard deviation of HHS care load. "
            "High volatility = unpredictable system = "
            "harder to staff and plan for."
        )
        st.markdown("---")
        st.markdown("**Period Stats**")
        vol = kpis["volatility"]
        st.markdown(f"- Current: **{vol:.2f}%**")
        st.markdown(f"- Peak:    **{df['volatility_14day'].max():,.0f}**")
        st.markdown(f"- Average: **{df['volatility_14day'].mean():,.0f}**")
        st.markdown("---")
        st.markdown("**Healthy signal**")
        st.markdown("Below 5% — small, predictable day-to-day changes.")
        if vol < 5:
            st.success("Currently stable ✓")
        elif vol < 10:
            st.warning("Moderate volatility ⚠")
        else:
            st.error("High volatility ✗")

    st.divider()

    # ── KPI 4 — Backlog Accumulation Rate 
    st.markdown("### KPI 4 — Backlog Accumulation Rate")

    col_left, col_right = st.columns([3, 1])

    with col_left:
        fig_k4 = chart_kpi_timeline(
            df             = df,
            kpi_col        = "backlog_rate",
            title          = "Backlog Accumulation Rate (30-Day Slope of Cumulative Intake)",
            color          = "#7209b7",
            y_label        = "Children/Day",
            reference_line = 0.0
        )
        st.plotly_chart(fig_k4, use_container_width=True)

    with col_right:
        st.markdown("**What it measures**")
        st.markdown(
            "How fast the cumulative backlog is growing or "
            "shrinking. Positive = backlog still building. "
            "Negative = backlog actively clearing."
        )
        st.markdown("---")
        st.markdown("**Period Stats**")
        backlog = kpis["backlog_rate"]
        st.markdown(f"- Current: **{backlog:+.2f}** children/day")
        st.markdown(f"- Peak:    **{df['backlog_rate'].max():+.2f}**")
        st.markdown(f"- Min:     **{df['backlog_rate'].min():+.2f}**")
        st.markdown("---")
        st.markdown("**Healthy signal**")
        st.markdown("Negative value — backlog shrinking each day.")
        if backlog <= 0:
            st.success("Backlog shrinking ✓")
        else:
            st.error("Backlog still growing ✗")

    st.divider()

    # ── KPI 5 — Discharge Offset Ratio ───
    st.markdown("### KPI 5 — Discharge Offset Ratio")

    col_left, col_right = st.columns([3, 1])

    with col_left:
        fig_k5 = chart_kpi_timeline(
            df             = df,
            kpi_col        = "discharge_offset_30day",
            title          = "Discharge Offset Ratio (30-Day Rolling: Discharges / Transfers)",
            color          = "#06d6a0",
            y_label        = "Ratio",
            reference_line = 1.0
        )
        st.plotly_chart(fig_k5, use_container_width=True)

    with col_right:
        st.markdown("**What it measures**")
        st.markdown(
            "30-day rolling ratio of discharges to transfers. "
            "Above 1.0 = discharges outpacing transfers. "
            "Below 1.0 = transfers outpacing discharges."
        )
        st.markdown("---")
        st.markdown("**Period Stats**")
        ratio = kpis["offset_ratio"]
        st.markdown(f"- Current: **{ratio:.3f}**")
        st.markdown(f"- Peak:    **{df['discharge_offset_30day'].max():.3f}**")
        st.markdown(f"- Average: **{df['discharge_offset_30day'].mean():.3f}**")
        st.markdown("---")
        st.markdown("**Healthy signal**")
        st.markdown("At or above 1.0 — discharges keeping up.")
        if ratio >= 1:
            st.success("Discharges keeping up ✓")
        else:
            st.error("Transfers outpacing discharges ✗")

    st.divider()

    # ── KPI Comparison Table 
    st.markdown("### KPI Comparison Table")
    st.caption("All 5 KPIs side by side — current value, period peak, and health status.")

    kpi_table = pd.DataFrame({
        "KPI": [
            "Total Under Care",
            "Net Intake Pressure",
            "Volatility Index",
            "Backlog Rate",
            "Discharge Offset"
        ],
        "Current Value": [
            f"{kpis['total_care']:,}",
            f"{kpis['net_pressure']:+.2f}%",
            f"{kpis['volatility']:.2f}%",
            f"{kpis['backlog_rate']:+.2f}",
            f"{kpis['offset_ratio']:.3f}"
        ],
        "Period Peak": [
            f"{int(df['total_system_load'].max()):,}",
            f"{df['net_intake_pressure'].max():+.2f}%",
            f"{df['volatility_14day'].max():,.0f}",
            f"{df['backlog_rate'].max():+.2f}",
            f"{df['discharge_offset_30day'].max():.3f}"
        ],
        "Period Average": [
            f"{int(df['total_system_load'].mean()):,}",
            f"{df['net_intake_pressure'].mean():+.2f}%",
            f"{df['volatility_14day'].mean():,.0f}",
            f"{df['backlog_rate'].mean():+.2f}",
            f"{df['discharge_offset_30day'].mean():.3f}"
        ],
        "Status": [
            "✓ Declining" if df["total_system_load"].iloc[-1] < df["total_system_load"].mean() else "⚠ Above Avg",
            "✓ Draining"  if kpis["net_pressure"]  <= 0  else "✗ Filling",
            "✓ Stable"    if kpis["volatility"]     < 5   else "⚠ Volatile",
            "✓ Shrinking" if kpis["backlog_rate"]   <= 0  else "✗ Growing",
            "✓ Keeping Up" if kpis["offset_ratio"]  >= 1  else "✗ Lagging"
        ]
    })

    st.dataframe(kpi_table, use_container_width=True, hide_index=True)

    # ── Overall Health Score 
    st.divider()
    st.markdown("#### 📌 Overall System Health")

    # count how many KPIs are in healthy state
    healthy_count = sum([
        df["total_system_load"].iloc[-1] < df["total_system_load"].mean(),
        kpis["net_pressure"]  <= 0,
        kpis["volatility"]     < 5,
        kpis["backlog_rate"]  <= 0,
        kpis["offset_ratio"]  >= 1
    ])

    health_pct = healthy_count / 5 * 100

    # progress bar as a simple health score
    st.progress(
        int(health_pct),
        text=f"System Health Score: {healthy_count}/5 KPIs in healthy state ({health_pct:.0f}%)"
    )

    if healthy_count == 5:
        st.success("All 5 KPIs are in a healthy state for the selected period.")
    elif healthy_count >= 3:
        st.warning(f"{5 - healthy_count} KPI(s) need attention. Review charts above.")
    else:
        st.error(f"{5 - healthy_count} KPIs are outside healthy ranges. Immediate review recommended.")