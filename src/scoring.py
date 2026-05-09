"""Scoring framework for the Control Midfielder Score."""

from __future__ import annotations

import pandas as pd

from .config import (
    ALLOWED_LEAGUES,
    CATEGORY_LABELS,
    CATEGORY_METRICS,
    EXCLUDED_SQUADS,
    MIN_DEFENSIVE_PROTECTION_SCORE,
    MIN_CATEGORY_SCORE,
    REQUIRE_ABOVE_MIN_EVERY_CATEGORY,
    SHORTLIST_SIZE,
    WEIGHTS,
)
from .metrics import percentile_normalize, prepare_metrics


def _score_metric(df: pd.DataFrame, metric: str) -> pd.Series:
    """Return a 0-100 score for one metric, respecting inverse columns."""

    if metric not in df.columns:
        return pd.Series(50.0, index=df.index)

    if metric.endswith("_inv") or metric in {"age_score", "minutes_score"}:
        return pd.to_numeric(df[metric], errors="coerce").fillna(50).clip(0, 100)
    return percentile_normalize(df[metric])


def calculate_category_scores(
    df: pd.DataFrame,
    category_metrics: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    """Calculate category scores as the mean of normalized metric scores."""

    category_metrics = category_metrics or CATEGORY_METRICS
    out = df.copy()
    for category, metrics in category_metrics.items():
        metric_scores = pd.concat([_score_metric(out, metric) for metric in metrics], axis=1)
        out[category] = metric_scores.mean(axis=1)
    return out


def calculate_weighted_score(
    df: pd.DataFrame,
    weights: dict[str, float] | None = None,
    score_col: str = "control_midfielder_score",
) -> pd.DataFrame:
    """Calculate weighted total Control Midfielder Score."""

    weights = weights or WEIGHTS
    normalized_weight_sum = sum(weights.values())
    out = df.copy()
    out[score_col] = 0.0
    for category, weight in weights.items():
        out[score_col] += out[category] * (weight / normalized_weight_sum)
    out[score_col] = out[score_col].round(2)
    out["rank"] = out[score_col].rank(ascending=False, method="min").astype(int)
    return out.sort_values(score_col, ascending=False).reset_index(drop=True)


def build_scoring_table(df: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Create the full scored player table from raw public stats."""

    engineered = prepare_metrics(df)
    categorized = calculate_category_scores(engineered)
    scored = calculate_weighted_score(categorized, weights=weights)
    for category in CATEGORY_METRICS:
        scored[category] = scored[category].round(2)
    return scored


def filter_target_candidates(
    scored: pd.DataFrame,
    require_balanced_profile: bool = REQUIRE_ABOVE_MIN_EVERY_CATEGORY,
) -> pd.DataFrame:
    """Apply the May 2026 recruitment-pool constraints."""

    out = scored.copy()
    if "is_target_candidate" in out.columns:
        out = out[out["is_target_candidate"].astype(bool)]
    out = out[out["league"].isin(ALLOWED_LEAGUES)]
    out = out[~out["squad"].isin(EXCLUDED_SQUADS)]
    out = out[out["squad"].ne("Manchester United")]
    out = out[out["defensive_protection"] >= MIN_DEFENSIVE_PROTECTION_SCORE]
    if require_balanced_profile:
        category_cols = list(CATEGORY_METRICS.keys())
        out = out[(out[category_cols] > MIN_CATEGORY_SCORE).all(axis=1)]
    out = out.sort_values("control_midfielder_score", ascending=False).reset_index(drop=True)
    out["rank"] = range(1, len(out) + 1)
    return out


def make_filtered_out_watchlist(scored: pd.DataFrame) -> pd.DataFrame:
    """Return otherwise eligible players removed by the defensive floor gate."""

    full_pool = scored.copy()
    if "is_target_candidate" in full_pool.columns:
        full_pool = full_pool[full_pool["is_target_candidate"].astype(bool)]
    full_pool = full_pool[full_pool["league"].isin(ALLOWED_LEAGUES)]
    full_pool = full_pool[~full_pool["squad"].isin(EXCLUDED_SQUADS)]
    full_pool = full_pool[full_pool["squad"].ne("Manchester United")]
    excluded = full_pool[full_pool["defensive_protection"] < MIN_DEFENSIVE_PROTECTION_SCORE].copy()
    category_cols = list(CATEGORY_METRICS.keys())
    excluded["lowest_category"] = excluded[category_cols].idxmin(axis=1)
    excluded["lowest_category_score"] = excluded[category_cols].min(axis=1).round(2)
    columns = [
        "rank",
        "player",
        "squad",
        "league",
        "age",
        "control_midfielder_score",
        *category_cols,
        "lowest_category",
        "lowest_category_score",
        "availability_note",
    ]
    return excluded.loc[:, [col for col in columns if col in excluded.columns]]


def make_shortlist(scored: pd.DataFrame, size: int = SHORTLIST_SIZE) -> pd.DataFrame:
    """Return top candidates with practical recruitment columns."""

    candidates = filter_target_candidates(scored)
    columns = [
        "rank",
        "player",
        "squad",
        "league",
        "date_of_birth",
        "age",
        "minutes",
        "market_value_m_eur",
        "availability_note",
        "context_source",
        "context_source_url",
        "control_midfielder_score",
        *CATEGORY_METRICS.keys(),
    ]
    return candidates.loc[:, [col for col in columns if col in candidates.columns]].head(size)


def make_category_scores(scored: pd.DataFrame, candidate_only: bool = True) -> pd.DataFrame:
    """Return a tidy category-score table for visualization and export."""

    if candidate_only:
        scored = filter_target_candidates(scored)
    cols = ["player", "squad", "league", "control_midfielder_score", *CATEGORY_METRICS.keys()]
    category_scores = scored.loc[:, cols].copy()
    category_scores = category_scores.rename(columns=CATEGORY_LABELS)
    return category_scores


def sensitivity_analysis(
    scored_input: pd.DataFrame,
    base_weights: dict[str, float] | None = None,
    swing: float = 0.10,
    top_n: int = SHORTLIST_SIZE,
) -> pd.DataFrame:
    """Test how top-candidate ranks move when category weights shift +/- swing."""

    base_weights = base_weights or WEIGHTS
    scenarios = [("Base weights", base_weights)]
    for category in base_weights:
        up = base_weights.copy()
        down = base_weights.copy()
        up[category] *= 1 + swing
        down[category] *= 1 - swing
        scenarios.append((f"{category} +{int(swing * 100)}%", up))
        scenarios.append((f"{category} -{int(swing * 100)}%", down))

    candidate_scored = filter_target_candidates(scored_input)
    candidate_pool = candidate_scored.head(top_n)["player"].tolist()
    rows = []
    for scenario_name, weights in scenarios:
        scenario_scores = calculate_weighted_score(scored_input.copy(), weights=weights)
        scenario_subset = filter_target_candidates(scenario_scores)
        scenario_subset = scenario_subset[scenario_subset["player"].isin(candidate_pool)]
        for _, row in scenario_subset.iterrows():
            rows.append(
                {
                    "scenario": scenario_name,
                    "player": row["player"],
                    "rank": int(row["rank"]),
                    "control_midfielder_score": row["control_midfielder_score"],
                }
            )
    return pd.DataFrame(rows)
