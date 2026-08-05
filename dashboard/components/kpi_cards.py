import streamlit as st

def render_card(title, value, subtitle, color, icon):
    """
    Renders a single styled KPI card using HTML inside st.markdown.
    
    title    — KPI name shown at the top of the card
    value    — the main number displayed large and bold
    subtitle — interpretation text shown below the value
    color    — left border accent color (from palette above)
    icon     — emoji shown next to the title
    """
    st.markdown(
        f"""
        <div style="
            background-color: #1a1d2e;
            border-left: 5px solid {color};
            border-radius: 10px;
            padding: 18px 20px;
            margin-bottom: 8px;
        ">
            <div style="
                font-size: 12px;
                color: #a0a0b8;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 6px;
            ">
                {icon} {title}
            </div>
            <div style="
                font-size: 28px;
                font-weight: 700;
                color: #e8e8f0;
                margin-bottom: 4px;
            ">
                {value}
            </div>
            <div style="
                font-size: 12px;
                color: #a0a0b8;
            ">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_kpi_row(kpis):
    """
    Renders all 5 KPI cards in a single horizontal row.
    kpis — dict returned by get_kpi_snapshot() from data_loader.py

    Call this at the top of any view that needs KPI cards.
    Example:
        from components.kpi_cards import render_kpi_row
        render_kpi_row(kpis)
    """

    # guard — if snapshot is empty, show a warning instead of crashing
    if not kpis:
        st.warning("No data available for the selected date range.")
        return

    # 5 equal columns — one card per column
    col1, col2, col3, col4, col5 = st.columns(5)

    # ── KPI 1 — Total Children Under Care ──
    with col1:
        render_card(
            title    = "Total Under Care",
            value    = f"{kpis['total_care']:,}",
            subtitle = f"As of {kpis['as_of_date']}",
            color    = "#4361ee",
            icon     = "👥"
        )

    # ── KPI 2 — Net Intake Pressure ──
    with col2:
        # positive pressure = filling (bad), negative = draining (good)
        pressure_val    = kpis["net_pressure"]
        pressure_color  = "#e63946" if pressure_val > 0 else "#06d6a0"
        pressure_status = "System filling ▲" if pressure_val > 0 else "System draining ▼"

        render_card(
            title    = "Net Intake Pressure",
            value    = f"{pressure_val:+.2f}%",
            subtitle = pressure_status,
            color    = pressure_color,
            icon     = "📥"
        )

    # ── KPI 3 — Care Load Volatility ──
    with col3:
        vol_val   = kpis["volatility"]
        # below 5% = stable, 5-10% = moderate, above 10% = high volatility
        vol_color = "#06d6a0" if vol_val < 5 else "#f72585" if vol_val > 10 else "#f4a261"
        vol_label = "Stable" if vol_val < 5 else "High" if vol_val > 10 else "Moderate"

        render_card(
            title    = "Volatility Index",
            value    = f"{vol_val:.2f}%",
            subtitle = f"{vol_label} day-to-day swings",
            color    = vol_color,
            icon     = "📊"
        )

    # ── KPI 4 — Backlog Accumulation Rate ──
    with col4:
        backlog_val    = kpis["backlog_rate"]
        backlog_color  = "#e63946" if backlog_val > 0 else "#06d6a0"
        backlog_status = "Backlog growing ▲" if backlog_val > 0 else "Backlog shrinking ▼"

        render_card(
            title    = "Backlog Rate",
            value    = f"{backlog_val:+.2f}",
            subtitle = backlog_status,
            color    = backlog_color,
            icon     = "📦"
        )

    # ── KPI 5 — Discharge Offset Ratio ──
    with col5:
        ratio_val    = kpis["offset_ratio"]
        # above 1.0 = discharges outpacing transfers (healthy)
        ratio_color  = "#06d6a0" if ratio_val >= 1 else "#e63946"
        ratio_status = "Discharges keeping up ✓" if ratio_val >= 1 else "Transfers outpacing ✗"

        render_card(
            title    = "Discharge Offset",
            value    = f"{ratio_val:.3f}",
            subtitle = ratio_status,
            color    = ratio_color,
            icon     = "🔄"
        )


def render_kpi_section_header(as_of_date):
    """
    Small header above the KPI row showing the date context.
    """
    st.markdown(
        f"""
        <div style="
            font-size: 11px;
            color: #a0a0b8;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        ">
            KPI Snapshot — values reflect end of selected date range ({as_of_date})
        </div>
        """,
        unsafe_allow_html=True
    )