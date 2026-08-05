import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


# ── UAC Dashboard Color Palette ──────────────────────────
# Primary purple:   #7209b7   (main accent, KPI highlights)
# Hot pink:         #f72585   (HHS care, stress, filling)
# Blue:             #4361ee   (total system load, 2025)
# Green:            #06d6a0   (draining, positive signals)
# Red:              #e63946   (stress zones, warnings)
# Light purple:     #c084fc   (daily raw values, background lines)
# Dark navy bg:     #0f1117   (matches backgroundColor in config)
# Card bg:          #1a1d2e   (matches secondaryBackgroundColor)
# ─────────────────────────────────────────────────────────


# ── Shared layout applied to every chart ─────────────────
LAYOUT_BASE = dict(
    paper_bgcolor = "#0f1117",
    plot_bgcolor  = "#0f1117",
    font          = dict(color="#e8e8f0", family="sans-serif"),
    margin        = dict(l=40, r=20, t=50, b=40),
    legend        = dict(
        bgcolor     = "#1a1d2e",
        bordercolor = "#2a2d3e",
        borderwidth = 1
    ),
    xaxis = dict(
        gridcolor    = "#2a2d3e",
        showgrid     = True,
        zeroline     = False,
        tickfont     = dict(color="#a0a0b8")
    ),
    yaxis = dict(
        gridcolor    = "#2a2d3e",
        showgrid     = True,
        zeroline     = False,
        tickfont     = dict(color="#a0a0b8")
    )
)


def apply_layout(fig, title, y_label="Number of Children", height=400):
    """
    Apply the shared dark theme layout to any figure.
    Call this at the end of every chart function.
    """
    layout = LAYOUT_BASE.copy()
    layout["title"] = dict(
        text    = title,
        font    = dict(size=15, color="#e8e8f0"),
        x       = 0,
        xanchor = "left"
    )
    layout["yaxis"]["title"] = y_label
    layout["height"] = height
    fig.update_layout(**layout)
    return fig



# SECTION 1 — OVERVIEW CHARTS


def chart_hhs_trend(df):
    """
    HHS care load over time with 7-day and 14-day rolling averages.
    Used in: views/overview.py
    """
    fig = go.Figure()

    # raw daily line — faint so it doesn't overpower the averages
    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = df["hhs_care"],
        name = "Daily HHS Care",
        line = dict(color="#c084fc", width=1),
        opacity = 0.4
    ))

    # 7-day rolling average — main trend line
    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = df["hhs_care_7day_avg"],
        name = "7-Day Avg",
        line = dict(color="#7209b7", width=2.5)
    ))

    # 14-day rolling average — longer trend
    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = df["hhs_care_14day_avg"],
        name = "14-Day Avg",
        line = dict(color="#f72585", width=2, dash="dash")
    ))

    return apply_layout(fig, "Children in HHS Care — Full Timeline")


def chart_total_system_load(df):
    """
    Total system load (CBP + HHS) as a filled area chart.
    Used in: views/overview.py
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = df["total_system_load"],
        name = "Total System Load",
        line = dict(color="#4361ee", width=2),
        fill = "tozeroy",
        fillcolor = "rgba(67, 97, 238, 0.15)"
    ))

    return apply_layout(fig, "Total System Load (CBP + HHS Combined)")


def chart_monthly_avg_hhs(df):
    """
    Monthly average HHS care as a bar chart, colored by year.
    Used in: views/overview.py
    """
    df = df.copy()
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    df["year"]       = df["date"].dt.year

    monthly = df.groupby(["year_month", "year"])["hhs_care"].mean().reset_index()

    year_colors = {2023: "#f72585", 2024: "#7209b7", 2025: "#4361ee"}

    fig = go.Figure()

    for year, color in year_colors.items():
        subset = monthly[monthly["year"] == year]
        fig.add_trace(go.Bar(
            x     = subset["year_month"],
            y     = subset["hhs_care"],
            name  = str(year),
            marker_color = color
        ))

    fig.update_layout(barmode="group")
    return apply_layout(fig, "Monthly Average HHS Care Load by Year",
                        height=350)



# SECTION 2 — CBP vs HHS CHARTS


def chart_transfers_vs_discharges(df):
    """
    Daily transfers into HHS vs discharges from HHS (7-day avg).
    Shaded gap shows which is winning.
    Used in: views/cbp_hhs.py
    """
    transfers_7day  = df["cbp_transferred"].rolling(7).mean()
    discharges_7day = df["hhs_discharged"].rolling(7).mean()

    fig = go.Figure()

    # transfers — the inflow
    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = transfers_7day,
        name = "Transfers into HHS (7-day avg)",
        line = dict(color="#f72585", width=2)
    ))

    # discharges — the outflow
    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = discharges_7day,
        name = "Discharges from HHS (7-day avg)",
        line = dict(color="#06d6a0", width=2)
    ))

    # shaded gap between the two lines
    fig.add_trace(go.Scatter(
        x         = pd.concat([df["date"], df["date"][::-1]]),
        y         = pd.concat([transfers_7day, discharges_7day[::-1]]),
        fill      = "toself",
        fillcolor = "rgba(230, 57, 70, 0.1)",
        line      = dict(color="rgba(0,0,0,0)"),
        name      = "Gap (inflow vs outflow)",
        showlegend = True
    ))

    return apply_layout(fig, "Transfers into HHS vs Discharges — 7-Day Avg")


def chart_discharge_offset_ratio(df):
    """
    30-day rolling discharge offset ratio over time.
    Above 1.0 = system draining. Below 1.0 = system filling.
    Used in: views/cbp_hhs.py
    """
    fig = go.Figure()

    # ratio line
    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = df["discharge_offset_30day"],
        name = "Discharge Offset Ratio (30-day)",
        line = dict(color="#7209b7", width=2)
    ))

    # balance line at 1.0
    fig.add_hline(
        y           = 1.0,
        line_dash   = "dash",
        line_color  = "#a0a0b8",
        annotation_text  = "Balance (1.0)",
        annotation_position = "top right"
    )

    # green fill above 1.0 — system draining (healthy)
    fig.add_trace(go.Scatter(
        x         = pd.concat([df["date"], df["date"][::-1]]),
        y         = pd.concat([
                        df["discharge_offset_30day"].clip(lower=1),
                        pd.Series([1.0] * len(df))
                    ]),
        fill      = "toself",
        fillcolor = "rgba(6, 214, 160, 0.1)",
        line      = dict(color="rgba(0,0,0,0)"),
        name      = "Draining zone",
        showlegend = True
    ))

    return apply_layout(fig, "Discharge Offset Ratio — Is HHS Keeping Up?",
                        y_label="Ratio (Discharges / Transfers)")


def chart_transfer_discharge_scatter(df):
    """
    Scatter plot — daily transfers vs discharges, colored by year.
    Shows whether high-transfer days also have high discharges.
    Used in: views/cbp_hhs.py
    """
    df = df.copy()
    df["year"] = df["date"].dt.year.astype(str)

    year_colors = {"2023": "#f72585", "2024": "#7209b7", "2025": "#4361ee"}

    fig = px.scatter(
        df,
        x     = "cbp_transferred",
        y     = "hhs_discharged",
        color = "year",
        color_discrete_map = year_colors,
        opacity = 0.5,
        labels  = {
            "cbp_transferred": "Daily Transfers into HHS",
            "hhs_discharged":  "Daily Discharges from HHS",
            "year":            "Year"
        }
    )

    # perfect balance diagonal
    max_val = max(df["cbp_transferred"].max(), df["hhs_discharged"].max())
    fig.add_trace(go.Scatter(
        x    = [0, max_val],
        y    = [0, max_val],
        mode = "lines",
        name = "Perfect Balance",
        line = dict(color="#a0a0b8", dash="dash", width=1)
    ))

    return apply_layout(fig, "Transfers vs Discharges — Each Dot = One Reporting Day",
                        y_label="Daily Discharges from HHS",
                        height=420)



# SECTION 3 — STRESS CHARTS

def chart_stress_zone(df):
    """
    HHS care load with the 90th percentile stress zone highlighted.
    Used in: views/overview.py and views/kpi_summary.py
    """
    stress_threshold = df["hhs_care"].quantile(0.90)

    fig = go.Figure()

    # raw daily values
    fig.add_trace(go.Scatter(
        x       = df["date"],
        y       = df["hhs_care"],
        name    = "Daily HHS Care",
        line    = dict(color="#c084fc", width=1),
        opacity = 0.4
    ))

    # 7-day avg
    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = df["hhs_care_7day_avg"],
        name = "7-Day Avg",
        line = dict(color="#7209b7", width=2.5)
    ))

    # stress zone — red fill above threshold
    stress_vals = df["hhs_care"].where(df["hhs_care"] >= stress_threshold)
    fig.add_trace(go.Scatter(
        x         = df["date"],
        y         = stress_vals,
        name      = f"Stress Zone (>{stress_threshold:,.0f})",
        fill      = "tozeroy",
        fillcolor = "rgba(230, 57, 70, 0.2)",
        line      = dict(color="rgba(0,0,0,0)")
    ))

    # threshold line
    fig.add_hline(
        y           = stress_threshold,
        line_dash   = "dash",
        line_color  = "#e63946",
        annotation_text  = f"90th Pct ({stress_threshold:,.0f})",
        annotation_position = "top right"
    )

    return apply_layout(fig, "HHS Care Load — Stress Periods Highlighted")


def chart_volatility(df):
    """
    14-day rolling standard deviation of HHS care load.
    Shows how stable or chaotic the system is over time.
    Used in: views/kpi_summary.py
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x         = df["date"],
        y         = df["volatility_14day"],
        name      = "14-Day Volatility",
        line      = dict(color="#f72585", width=2),
        fill      = "tozeroy",
        fillcolor = "rgba(247, 37, 133, 0.1)"
    ))

    return apply_layout(fig, "HHS Care Load Volatility — 14-Day Rolling Std Dev",
                        y_label="Standard Deviation")



# SECTION 4 — NET INTAKE & BACKLOG CHARTS


def chart_net_intake(df):
    """
    Daily net intake as a bar chart — red for filling, green for draining.
    Includes a 14-day rolling average trend line.
    Used in: views/net_intake.py
    """
    fig = go.Figure()

    # color each bar by sign
    bar_colors = ["#e63946" if v > 0 else "#06d6a0"
                  for v in df["net_daily_intake"]]

    fig.add_trace(go.Bar(
        x              = df["date"],
        y              = df["net_daily_intake"],
        name           = "Net Daily Intake",
        marker_color   = bar_colors,
        opacity        = 0.8
    ))

    # 14-day rolling avg on top
    net_14day = df["net_daily_intake"].rolling(14).mean()
    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = net_14day,
        name = "14-Day Avg",
        line = dict(color="#7209b7", width=2)
    ))

    # zero line
    fig.add_hline(y=0, line_color="#a0a0b8", line_width=1)

    return apply_layout(fig, "Daily Net Intake — Red: Filling | Green: Draining",
                        y_label="Net Children/Day")


def chart_cumulative_backlog(df):
    """
    Cumulative net intake over time — shows backlog buildup and clearance.
    Used in: views/net_intake.py
    """
    fig = go.Figure()

    # fill red when above zero (backlog building)
    fig.add_trace(go.Scatter(
        x         = df["date"],
        y         = df["cumulative_net_intake"].clip(lower=0),
        name      = "Backlog Building",
        fill      = "tozeroy",
        fillcolor = "rgba(230, 57, 70, 0.2)",
        line      = dict(color="rgba(0,0,0,0)")
    ))

    # fill green when below zero (backlog clearing)
    fig.add_trace(go.Scatter(
        x         = df["date"],
        y         = df["cumulative_net_intake"].clip(upper=0),
        name      = "Backlog Clearing",
        fill      = "tozeroy",
        fillcolor = "rgba(6, 214, 160, 0.2)",
        line      = dict(color="rgba(0,0,0,0)")
    ))

    # main cumulative line
    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = df["cumulative_net_intake"],
        name = "Cumulative Net Intake",
        line = dict(color="#4361ee", width=2)
    ))

    fig.add_hline(y=0, line_color="#a0a0b8", line_width=1)

    return apply_layout(fig, "Cumulative Net Intake — Backlog Buildup Over Time",
                        y_label="Cumulative Net Children")


def chart_monthly_net_intake(df):
    """
    Monthly total net intake — red months added pressure, green months relieved it.
    Used in: views/net_intake.py
    """
    df = df.copy()
    df["year_month"] = df["date"].dt.to_period("M").astype(str)

    monthly = df.groupby("year_month")["net_daily_intake"].sum().reset_index()

    bar_colors = ["#e63946" if v > 0 else "#06d6a0"
                  for v in monthly["net_daily_intake"]]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x            = monthly["year_month"],
        y            = monthly["net_daily_intake"],
        marker_color = bar_colors,
        name         = "Monthly Net Intake"
    ))

    fig.add_hline(y=0, line_color="#a0a0b8", line_width=1)

    return apply_layout(fig, "Monthly Net Intake — Red: Added Pressure | Green: Relieved",
                        y_label="Net Children (Month Total)",
                        height=350)



# SECTION 5 — KPI TIMELINE CHARTS


def chart_kpi_timeline(df, kpi_col, title, color, y_label, reference_line=None):
    """
    Generic KPI timeline chart — one function handles all 5 KPIs.
    
    kpi_col        — column name in df to plot
    title          — chart title
    color          — line color from palette
    y_label        — y-axis label
    reference_line — optional float value to draw a horizontal dashed line
    
    Used in: views/kpi_summary.py
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x         = df["date"],
        y         = df[kpi_col],
        name      = title,
        line      = dict(color=color, width=2),
        fill      = "tozeroy",
        fillcolor = f"rgba{tuple(list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}"
    ))

    # optional reference line (e.g. 0 for pressure, 1.0 for offset ratio)
    if reference_line is not None:
        fig.add_hline(
            y          = reference_line,
            line_dash  = "dash",
            line_color = "#a0a0b8",
            line_width = 1
        )

    return apply_layout(fig, title, y_label=y_label, height=280)