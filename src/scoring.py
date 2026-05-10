"""Scoring framework for the Control Midfielder Score."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    ALLOWED_LEAGUES,
    CATEGORY_LABELS,
    CATEGORY_METRICS,
    CATEGORY_WEIGHTS,
    EXCLUDED_SQUADS,
    METRIC_ALIASES,
    METRIC_GROUPS,
    MIN_DEFENSIVE_PROTECTION_SCORE,
    MIN_CATEGORY_SCORE,
    REQUIRE_ABOVE_MIN_EVERY_CATEGORY,
    SENSITIVITY_SCENARIOS,
    SHORTLIST_SIZE,
)
from .metrics import (
    calculate_per90,
    add_age_availability_scores,
    add_canonical_metric_aliases,
    add_possession_risk_rates,
    prepare_metrics,
)


def calculate_per90_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Create per-90 metrics from raw counting fields."""

    return calculate_per90(df)


def calculate_rate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Create rate and per-touch metrics used by the score."""

    out = add_possession_risk_rates(df)
    out = add_age_availability_scores(out)
    return add_canonical_metric_aliases(out)


def percentile_score(series: pd.Series) -> pd.Series:
    """Convert a numeric series to a 0-100 percentile-style score."""

    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == 0:
        return pd.Series(50.0, index=series.index)
    filled = numeric.fillna(numeric.median())
    return filled.rank(pct=True, method="average") * 100


def inverse_percentile_score(series: pd.Series) -> pd.Series:
    """Convert a numeric series to a score where lower raw values are better."""

    return 100 - percentile_score(series) + (100 / max(len(series), 1))


def resolve_metric_column(df: pd.DataFrame, metric: str) -> str | None:
    """Return the available dataframe column for a canonical metric name."""

    if metric in df.columns:
        return metric
    alias = METRIC_ALIASES.get(metric)
    if alias in df.columns:
        return alias
    return None


def calculate_metric_percentiles(
    df: pd.DataFrame, metric_groups: dict[str, list[dict[str, object]]] | None = None,
) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    """Score every available input metric and record unavailable fields.

    Each input metric is first resolved to an available raw or engineered
    column. Higher-is-better metrics use ordinary percentiles; negative events
    use inverse percentiles.
    """

    metric_groups = metric_groups or METRIC_GROUPS
    out = df.copy()
    unavailable: list[dict[str, str]] = []

    for category, metrics in metric_groups.items():
        for metric_info in metrics:
            metric = str(metric_info["metric"])
            raw_col = resolve_metric_column(out, metric)
            score_col = f"{metric}_score"
            if raw_col is None:
                unavailable.append(
                    {
                        "category": category,
                        "input_metric": metric,
                        "reason": "No matching raw or engineered column in public dataset",
                    }
                )
                continue
            if bool(metric_info["higher_is_better"]):
                out[score_col] = percentile_score(out[raw_col])
            else:
                out[score_col] = inverse_percentile_score(out[raw_col])
    return out, unavailable


def calculate_category_scores(
    df: pd.DataFrame, metric_groups: dict[str, list[dict[str, object]]] | None = None,
) -> pd.DataFrame:
    """Average available input-metric scores into category scores."""

    metric_groups = metric_groups or METRIC_GROUPS
    out = df.copy()
    for category, metrics in metric_groups.items():
        score_cols = [
            f"{metric_info['metric']}_score"
            for metric_info in metrics
            if f"{metric_info['metric']}_score" in out.columns
        ]
        count_col = f"{category}_metric_count"
        out[count_col] = len(score_cols)
        if score_cols:
            out[category] = out[score_cols].mean(axis=1)
        else:
            out[category] = 50.0
    return out


def calculate_total_score(
    df: pd.DataFrame,
    category_weights: dict[str, float] | None = None,
    score_col: str = "control_midfielder_score",
) -> pd.DataFrame:
    """Calculate the weighted final score from category scores."""

    category_weights = category_weights or CATEGORY_WEIGHTS
    weight_sum = sum(category_weights.values())
    out = df.copy()
    out[score_col] = 0.0
    for category, weight in category_weights.items():
        out[score_col] += out[category] * (weight / weight_sum)
    out[score_col] = out[score_col].round(2)
    out["rank"] = out[score_col].rank(ascending=False, method="min").astype(int)
    return out.sort_values(score_col, ascending=False).reset_index(drop=True)


def apply_defensive_gate(
    df: pd.DataFrame, gate_threshold: float = MIN_DEFENSIVE_PROTECTION_SCORE,
) -> pd.DataFrame:
    """Add defensive-gate flags without deleting any player rows."""

    out = df.copy()
    out["passed_defensive_gate"] = out["defensive_protection"] >= gate_threshold
    out["gate_margin"] = (out["defensive_protection"] - gate_threshold).round(2)
    out["gate_status"] = np.select(
        [out["gate_margin"].between(-5, 5, inclusive="both"), out["passed_defensive_gate"],],
        ["Borderline / video review", "Passed gate"],
        default="Watchlist: below gate",
    )
    return out


def _base_target_pool(scored: pd.DataFrame) -> pd.DataFrame:
    """Apply league, club, and target-pool constraints except the defensive gate."""

    out = scored.copy()
    if "is_target_candidate" in out.columns:
        out = out[out["is_target_candidate"].astype(bool)]
    out = out[out["league"].isin(ALLOWED_LEAGUES)]
    out = out[~out["squad"].isin(EXCLUDED_SQUADS)]
    out = out[out["squad"].ne("Manchester United")]
    return out.copy()


def build_scoring_table(df: pd.DataFrame, weights: dict[str, float] | None = None,) -> pd.DataFrame:
    """Create the full scored player table from raw public stats."""

    engineered = prepare_metrics(df)
    metric_scored, unavailable = calculate_metric_percentiles(engineered)
    categorized = calculate_category_scores(metric_scored)
    scored = calculate_total_score(categorized, category_weights=weights)
    scored.attrs["unavailable_metrics"] = unavailable
    for category in CATEGORY_METRICS:
        scored[category] = scored[category].round(2)
    scored = apply_defensive_gate(scored)
    return scored


def filter_target_candidates(
    scored: pd.DataFrame, require_balanced_profile: bool = REQUIRE_ABOVE_MIN_EVERY_CATEGORY,
) -> pd.DataFrame:
    """Apply the May 2026 recruitment-pool constraints and defensive gate."""

    out = _base_target_pool(scored)
    out = out[out["defensive_protection"] >= MIN_DEFENSIVE_PROTECTION_SCORE]
    if require_balanced_profile:
        category_cols = list(CATEGORY_METRICS.keys())
        out = out[(out[category_cols] > MIN_CATEGORY_SCORE).all(axis=1)]
    out = out.sort_values("control_midfielder_score", ascending=False).reset_index(drop=True)
    out["rank"] = range(1, len(out) + 1)
    return out


def make_filtered_out_watchlist(scored: pd.DataFrame) -> pd.DataFrame:
    """Return otherwise eligible players removed by the defensive gate."""

    excluded = _base_target_pool(scored)
    excluded = excluded[excluded["defensive_protection"] < MIN_DEFENSIVE_PROTECTION_SCORE].copy()
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
        "passed_defensive_gate",
        "gate_margin",
        "gate_status",
        "lowest_category",
        "lowest_category_score",
        "availability_note",
    ]
    return excluded.loc[:, [col for col in columns if col in excluded.columns]]


def split_watchlists(watchlist: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split below-gate players into borderline and role-mismatch watchlists."""

    borderline = watchlist[watchlist["gate_margin"].between(-5, 0, inclusive="both")].copy()
    role_mismatch = watchlist[~watchlist["player"].isin(borderline["player"])].copy()
    return borderline, role_mismatch


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
        "passed_defensive_gate",
        "gate_margin",
        "gate_status",
        *[f"{category}_metric_count" for category in CATEGORY_METRICS],
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


def assign_archetype(row: pd.Series) -> str:
    """Auto-label player profiles from category scores."""

    defence = row["defensive_protection"]
    security = row["possession_security"]
    progression = row["progressive_value"]
    gate_margin = row.get("gate_margin", defence - MIN_DEFENSIVE_PROTECTION_SCORE)

    if defence < MIN_DEFENSIVE_PROTECTION_SCORE:
        return "Removed by defensive gate"
    if security >= 65 and defence >= 65:
        return "Two-axis defensive/security fit"
    if security >= 70 and defence < 65:
        return "Control profile"
    if defence >= 70 and security < 60:
        return "Defensive-floor anchor"
    if progression >= 70 and security >= 60:
        return "Progressive controller"
    if defence >= 65 and security < 40:
        return "Low-control defensive specialist"
    if abs(gate_margin) <= 5:
        return "Watchlist / role-context needed"
    return "Watchlist / role-context needed"


def make_analyst_note(row: pd.Series) -> str:
    """Create a short plain-English note for report tables."""

    strongest = row.get("strongest_football_category", row["strongest_category"]).replace("_", " ")
    weakest = row.get("weakest_football_category", row["weakest_category"]).replace("_", " ")
    if not bool(row["passed_defensive_gate"]):
        return (
            f"Below the light defensive gate by {abs(row['gate_margin']):.1f} points; "
            "keep for video/context review rather than treating as rejected."
        )
    if abs(row["gate_margin"]) <= 5:
        return (
            f"Borderline defensive-gate profile; strongest in {strongest}, weakest in {weakest}. "
            "Role and video review should test defensive translation."
        )
    return f"Strongest in {strongest}; weakest in {weakest}. Use video to test role fit."


def make_player_score_explanation(scored: pd.DataFrame) -> pd.DataFrame:
    """Create player-level explainability output for analysts and recruiters."""

    out = scored.copy()
    category_cols = list(CATEGORY_METRICS.keys())
    for category in category_cols:
        out[f"{category}_rank"] = out[category].rank(ascending=False, method="min").astype(int)
    out["strongest_category"] = out[category_cols].idxmax(axis=1)
    out["weakest_category"] = out[category_cols].idxmin(axis=1)
    football_category_cols = [col for col in category_cols if col != "age_availability"]
    out["strongest_football_category"] = out[football_category_cols].idxmax(axis=1)
    out["weakest_football_category"] = out[football_category_cols].idxmin(axis=1)
    out["archetype_label"] = out.apply(assign_archetype, axis=1)
    out["analyst_note"] = out.apply(make_analyst_note, axis=1)
    cols = [
        "player",
        "squad",
        "league",
        "age",
        "control_midfielder_score",
        *category_cols,
        *[f"{category}_rank" for category in category_cols],
        "strongest_category",
        "weakest_category",
        "strongest_football_category",
        "weakest_football_category",
        "passed_defensive_gate",
        "gate_margin",
        "archetype_label",
        "analyst_note",
    ]
    explanation = out.loc[:, cols].rename(
        columns={"squad": "club", "control_midfielder_score": "final_score",}
    )
    return explanation


def make_metric_dictionary(
    scored: pd.DataFrame, metric_groups: dict[str, list[dict[str, object]]] | None = None,
) -> pd.DataFrame:
    """Create an auditable data dictionary for every configured input metric."""

    metric_groups = metric_groups or METRIC_GROUPS
    rows = []
    for category, metrics in metric_groups.items():
        for metric_info in metrics:
            metric = str(metric_info["metric"])
            raw_col = resolve_metric_column(scored, metric)
            rows.append(
                {
                    "category": category,
                    "input_metric": metric,
                    "raw_column_used": raw_col or "",
                    "transformation": "Percentile score"
                    if bool(metric_info["higher_is_better"])
                    else "Inverse percentile score",
                    "higher_is_better": bool(metric_info["higher_is_better"]),
                    "explanation": metric_info.get("explanation", ""),
                    "caveat": metric_info.get("caveat", ""),
                }
            )
    return pd.DataFrame(rows)


def calculate_weighted_score(
    df: pd.DataFrame,
    weights: dict[str, float] | None = None,
    score_col: str = "control_midfielder_score",
) -> pd.DataFrame:
    """Backwards-compatible wrapper for older notebooks."""

    return calculate_total_score(df, category_weights=weights, score_col=score_col)


def run_sensitivity_analysis(
    scored_input: pd.DataFrame,
    scenarios: dict[str, dict[str, float]] | None = None,
    top_n: int = SHORTLIST_SIZE,
) -> pd.DataFrame:
    """Calculate rank stability across defined weighting scenarios."""

    scenarios = scenarios or SENSITIVITY_SCENARIOS
    base_pool = filter_target_candidates(scored_input).head(top_n)
    player_pool = base_pool["player"].tolist()

    scenario_frames = []
    for scenario_name, weights in scenarios.items():
        scenario_scores = calculate_total_score(scored_input.copy(), category_weights=weights)
        scenario_subset = filter_target_candidates(scenario_scores)
        scenario_subset = scenario_subset[scenario_subset["player"].isin(player_pool)]
        scenario_subset = scenario_subset[["player", "rank", "control_midfielder_score"]].copy()
        scenario_subset["scenario"] = scenario_name
        scenario_frames.append(scenario_subset)

    long = pd.concat(scenario_frames, ignore_index=True)
    rank_pivot = long.pivot_table(index="player", columns="scenario", values="rank", aggfunc="min")
    for scenario in scenarios:
        if scenario not in rank_pivot.columns:
            rank_pivot[scenario] = np.nan
    rank_pivot = rank_pivot[list(scenarios.keys())]
    rank_pivot = rank_pivot.rename(columns={name: f"rank_{name}" for name in rank_pivot.columns})
    rank_cols = list(rank_pivot.columns)
    rank_pivot["best_rank"] = rank_pivot[rank_cols].min(axis=1)
    rank_pivot["worst_rank"] = rank_pivot[rank_cols].max(axis=1)
    rank_pivot["rank_range"] = rank_pivot["worst_rank"] - rank_pivot["best_rank"]
    rank_pivot["average_rank"] = rank_pivot[rank_cols].mean(axis=1).round(2)
    max_range = rank_pivot["rank_range"].max()
    if pd.isna(max_range) or max_range == 0:
        rank_pivot["rank_volatility_score"] = 0.0
    else:
        rank_pivot["rank_volatility_score"] = (rank_pivot["rank_range"] / max_range * 100).round(2)
    rank_pivot = rank_pivot.reset_index()
    return rank_pivot.sort_values(["average_rank", "rank_base"]).reset_index(drop=True)


def sensitivity_analysis(
    scored_input: pd.DataFrame,
    base_weights: dict[str, float] | None = None,
    swing: float = 0.10,
    top_n: int = SHORTLIST_SIZE,
) -> pd.DataFrame:
    """Backwards-compatible sensitivity wrapper.

    The new output is wide and includes rank stability; `base_weights` and
    `swing` are accepted for older notebook calls but no longer drive the
    scenario set.
    """

    _ = base_weights, swing
    return run_sensitivity_analysis(scored_input, top_n=top_n)
