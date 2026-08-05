from pathlib import Path

import pandas as pd
import streamlit as st

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


# path to the enriched dataset — resolved from this file's location so it
# works regardless of the process's working directory (e.g. Streamlit
# Community Cloud runs the app from the repo root, not from dashboard/)
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "uac_enriched.csv"


@st.cache_data
def load_data():
    """
    Load the enriched UAC dataset.
    st.cache_data means this only runs once — subsequent calls
    return the cached result instantly. No re-reading the file
    every time a user changes a filter.
    """
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def filter_by_date(df, start_date, end_date):
    """
    Filter the dataframe to only include rows between
    start_date and end_date (inclusive).
    Every view calls this after load_data().
    """
    mask = (df["date"] >= pd.Timestamp(start_date)) & \
           (df["date"] <= pd.Timestamp(end_date))
    return df[mask].reset_index(drop=True)


def get_date_bounds(df):
    """
    Return the min and max dates in the dataset.
    Used by the sidebar to set the date range slider limits.
    """
    return df["date"].min().date(), df["date"].max().date()


def get_kpi_snapshot(df):
    """
    Compute current KPI values from the filtered dataframe.
    Always uses the last row of the filtered date range
    so the KPI cards update when the user changes the date filter.
    """

    # guard against empty dataframe after filtering
    if df.empty:
        return {}

    last_row = df.iloc[-1]

    # total children the system is responsible for right now
    total_care = int(last_row["total_system_load"])

    # net intake pressure — is the system filling or draining?
    net_pressure = round(float(last_row["net_intake_pressure"]), 2) \
        if "net_intake_pressure" in df.columns else None

    # how unstable is the day-to-day load?
    volatility = round(float(last_row["volatility_index"]), 2) \
        if "volatility_index" in df.columns else None

    # is the backlog growing or shrinking?
    backlog_rate = round(float(last_row["backlog_rate"]), 2) \
        if "backlog_rate" in df.columns else None

    # are discharges keeping up with transfers?
    offset_ratio = round(float(last_row["discharge_offset_30day"]), 3) \
        if "discharge_offset_30day" in df.columns else None

    return {
        "total_care":    total_care,
        "net_pressure":  net_pressure,
        "volatility":    volatility,
        "backlog_rate":  backlog_rate,
        "offset_ratio":  offset_ratio,
        "as_of_date":    str(last_row["date"].date())
    }


def get_stress_alert(df):
    """
    Early-warning check: compares the most recent 7-day average care load
    against 80% of the all-time 90th-percentile stress threshold. This is
    the leading indicator recommended in the project's executive summary
    (R3) — meant to give planners 1-2 weeks of lead time before a
    sustained stress period, rather than only reporting stress after it's
    already underway.

    The threshold is computed from the full, unfiltered dataset (a fixed
    historical benchmark), while the current value respects whatever date
    range is selected, so the alert reflects the most recent data in view.
    """
    if df.empty or "hhs_care_7day_avg" not in df.columns:
        return None

    current_avg = df["hhs_care_7day_avg"].dropna()
    if current_avg.empty:
        return None
    current_avg = current_avg.iloc[-1]

    full_df = load_data()
    stress_threshold = full_df["hhs_care"].quantile(0.90)
    warning_line = 0.8 * stress_threshold

    return {
        "current_avg": current_avg,
        "stress_threshold": stress_threshold,
        "pct_of_threshold": current_avg / stress_threshold * 100,
        "is_approaching": current_avg >= warning_line,
    }


def get_granularity(df, granularity):
    """
    Resample the dataframe by day, week, or month.
    Used by the granularity toggle in the sidebar.
    granularity options: 'Daily', 'Weekly', 'Monthly'
    """

    # columns that should be summed (flow counts)
    sum_cols = [
        "cbp_apprehended", "cbp_transferred",
        "hhs_discharged", "net_daily_intake"
    ]

    # columns that should be averaged (stock/level counts)
    mean_cols = [
        "cbp_custody", "hhs_care", "total_system_load",
        "hhs_care_7day_avg", "hhs_care_14day_avg",
        "net_intake_pressure", "volatility_index", "volatility_14day",
        "backlog_rate", "discharge_offset_30day",
        "discharge_offset_ratio", "cumulative_net_intake"
    ]

    # map user-friendly label to pandas resample frequency
    freq_map = {
        "Daily":   "D",
        "Weekly":  "W",
        "Monthly": "ME"
    }

    freq = freq_map.get(granularity, "D")

    # if daily, just return as-is — no resampling needed
    if freq == "D":
        return df

    df_indexed = df.set_index("date")

    # resample sum and mean columns separately then join
    available_sum  = [c for c in sum_cols  if c in df_indexed.columns]
    available_mean = [c for c in mean_cols if c in df_indexed.columns]

    resampled_sum  = df_indexed[available_sum].resample(freq).sum()
    resampled_mean = df_indexed[available_mean].resample(freq).mean()

    combined = pd.concat([resampled_sum, resampled_mean], axis=1)
    combined = combined.reset_index()

    return combined