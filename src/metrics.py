"""Metric engineering and normalization utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DIRECT_PERCENT_COLUMNS, INVERSE_RAW_METRICS, RAW_COUNT_COLUMNS


def calculate_per90(
    df: pd.DataFrame, count_columns: list[str] | None = None, minutes_col: str = "minutes",
) -> pd.DataFrame:
    """Create per-90 columns for raw counting stats.

    Public aggregate providers often report season totals. The scoring model
    compares players with different playing time, so count metrics are first
    converted to per-90 rates using the available minutes column.
    """

    out = df.copy()
    count_columns = count_columns or RAW_COUNT_COLUMNS
    minutes = out[minutes_col].replace(0, np.nan)
    for col in count_columns:
        if col in out.columns:
            out[f"{col}_per90"] = out[col] / minutes * 90
    return out


def add_canonical_metric_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Add canonical names used in the explainability config.

    The underlying sample dataset predates the expanded methodology copy, so a
    few fields use shorter names. These aliases keep the model vocabulary
    readable without changing the raw data.
    """

    out = df.copy()
    if "aerial_win_pct" in out.columns and "aerial_duel_win_pct" not in out.columns:
        out["aerial_duel_win_pct"] = out["aerial_win_pct"]
    if (
        "defensive_actions_after_loss_per90" in out.columns
        and "def_actions_after_loss_per90" not in out.columns
    ):
        out["def_actions_after_loss_per90"] = out["defensive_actions_after_loss_per90"]
    return out


def percentile_normalize(series: pd.Series) -> pd.Series:
    """Convert a numeric series to 0-100 percentile scores where high is good.

    Missing values are filled with the median so that sparse public fields do
    not automatically push a player to the top or bottom of the screen.
    """

    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == 0:
        return pd.Series(50.0, index=series.index)
    filled = numeric.fillna(numeric.median())
    return filled.rank(pct=True, method="average") * 100


def inverse_percentile_normalize(series: pd.Series) -> pd.Series:
    """Convert a numeric series to 0-100 percentile scores where low is good.

    This is used for risk and discipline metrics such as cards, fouls,
    miscontrols, dispossessions, and turnover rates.
    """

    return 100 - percentile_normalize(series) + (100 / max(len(series), 1))


def add_age_availability_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Score age and minutes availability on public-data-friendly proxies."""

    out = df.copy()
    age = pd.to_numeric(out["age"], errors="coerce")

    age_score = np.where(
        age.between(21, 27, inclusive="both"), 100, np.maximum(0, 100 - np.abs(age - 24) * 12.5),
    )
    out["age_score"] = age_score
    out["minutes_score"] = percentile_normalize(out["minutes"])
    return out


def add_possession_risk_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer touch-adjusted possession security metrics.

    Raw turnovers can punish players who are simply more involved. Dividing
    by touches gives a cleaner public-data proxy for security under usage.
    """

    out = df.copy()
    touches = out["touches_per90"].replace(0, np.nan)
    out["dispossessed_per_touch"] = out["dispossessed_per90"] / touches
    out["miscontrols_per_touch"] = out["miscontrols_per90"] / touches
    out["turnover_rate"] = (out["dispossessed_per90"] + out["miscontrols_per90"]) / touches
    return out


def add_inverse_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Create inverse-percentile versions for risk and discipline metrics."""

    out = df.copy()
    for col in INVERSE_RAW_METRICS:
        if col in out.columns:
            out[f"{col}_inv"] = inverse_percentile_normalize(out[col])
    return out


def add_metric_percentiles(df: pd.DataFrame, metric_columns: list[str]) -> pd.DataFrame:
    """Append normalized percentile scores for requested metrics.

    The function is retained for notebook exploration and auditability; the
    production scoring path calls `_score_metric` inside `src.scoring`.
    """

    out = df.copy()
    for col in metric_columns:
        if col not in out.columns or col.endswith("_inv"):
            continue
        if col in DIRECT_PERCENT_COLUMNS:
            out[f"{col}_score"] = percentile_normalize(out[col])
        else:
            out[f"{col}_score"] = percentile_normalize(out[col])
    return out


def prepare_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Run all metric engineering needed before category scoring."""

    out = calculate_per90(df)
    out = add_possession_risk_rates(out)
    out = add_inverse_metrics(out)
    out = add_age_availability_scores(out)
    out = add_canonical_metric_aliases(out)
    return out
