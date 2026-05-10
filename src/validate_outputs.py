"""Validation checks for generated Casemiro Replacement Profile outputs."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .config import (
    CATEGORY_METRICS,
    CATEGORY_WEIGHTS,
    CHART_DIR,
    MIN_DEFENSIVE_PROTECTION_SCORE,
    OUTPUT_DIR,
    REPORT_DIR,
)


REQUIRED_OUTPUTS = [
    OUTPUT_DIR / "candidate_shortlist.csv",
    OUTPUT_DIR / "watchlist_removed_by_gate.csv",
    OUTPUT_DIR / "borderline_watchlist.csv",
    OUTPUT_DIR / "role_mismatch_watchlist.csv",
    OUTPUT_DIR / "category_scores.csv",
    OUTPUT_DIR / "player_score_explanation.csv",
    OUTPUT_DIR / "metric_dictionary.csv",
    OUTPUT_DIR / "substack_methodology_table.csv",
    OUTPUT_DIR / "sensitivity_analysis.csv",
    REPORT_DIR / "casemiro_replacement_report.html",
    REPORT_DIR / "casemiro_replacement_report.pdf",
]

REQUIRED_CHARTS = [
    CHART_DIR / "ranked_control_midfielder_score.png",
    CHART_DIR / "security_vs_defensive_floor.png",
    CHART_DIR / "category_heatmap.png",
    CHART_DIR / "casemiro_candidate_radar.png",
    CHART_DIR / "defensive_gate_diagnostic.png",
    CHART_DIR / "possession_security_breakdown.png",
    CHART_DIR / "transition_chaos_map.png",
    CHART_DIR / "progression_type_chart.png",
    CHART_DIR / "sensitivity_rank_stability.png",
    CHART_DIR / "archetype_summary.png",
]

REQUIRED_SENSITIVITY_COLUMNS = {
    "rank_base",
    "rank_defensive_heavy",
    "rank_possession_heavy",
    "rank_transition_heavy",
    "rank_progression_heavy",
    "rank_equal_weight",
    "best_rank",
    "worst_rank",
    "rank_range",
    "average_rank",
    "rank_volatility_score",
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_required_files() -> None:
    for path in REQUIRED_OUTPUTS + REQUIRED_CHARTS:
        _assert(path.exists(), f"Missing required output: {path}")
        _assert(path.stat().st_size > 0, f"Output is empty: {path}")


def validate_scores() -> None:
    shortlist = pd.read_csv(OUTPUT_DIR / "candidate_shortlist.csv")
    explanation = pd.read_csv(OUTPUT_DIR / "player_score_explanation.csv")
    watchlist = pd.read_csv(OUTPUT_DIR / "watchlist_removed_by_gate.csv")
    borderline = pd.read_csv(OUTPUT_DIR / "borderline_watchlist.csv")
    role_mismatch = pd.read_csv(OUTPUT_DIR / "role_mismatch_watchlist.csv")

    _assert(abs(sum(CATEGORY_WEIGHTS.values()) - 1.0) < 1e-9, "Category weights must sum to 1")
    _assert(shortlist["player"].notna().all(), "Shortlist has missing player names")
    _assert(watchlist["player"].notna().all(), "Watchlist has missing player names")
    _assert(explanation["player"].notna().all(), "Score explanation has missing player names")
    _assert(explanation["final_score"].between(0, 100).all(), "Final scores outside 0-100")

    for category in CATEGORY_METRICS:
        _assert(
            explanation[category].between(0, 100).all(), f"{category} scores outside 0-100",
        )

    overlap = set(shortlist["player"]) & set(watchlist["player"])
    _assert(not overlap, f"Players appear in both shortlist and watchlist: {sorted(overlap)}")
    split_overlap = set(borderline["player"]) & set(role_mismatch["player"])
    _assert(
        not split_overlap, f"Players appear in both watchlist splits: {sorted(split_overlap)}",
    )
    split_players = set(borderline["player"]) | set(role_mismatch["player"])
    _assert(
        split_players == set(watchlist["player"]),
        "Borderline and role-mismatch watchlists must cover the full below-gate watchlist",
    )
    _assert(
        (shortlist["defensive_protection"] >= MIN_DEFENSIVE_PROTECTION_SCORE).all(),
        "Shortlist includes a player below the defensive gate",
    )
    _assert(
        (watchlist["defensive_protection"] < MIN_DEFENSIVE_PROTECTION_SCORE).all(),
        "Watchlist includes a player above the defensive gate",
    )
    if not borderline.empty:
        _assert(
            borderline["gate_margin"].between(-5, 0, inclusive="both").all(),
            "Borderline watchlist includes a player outside the -5 to 0 gate-margin band",
        )
    if not role_mismatch.empty:
        _assert(
            ~role_mismatch["gate_margin"].between(-5, 0, inclusive="both").any(),
            "Role-mismatch watchlist includes a borderline player",
        )


def validate_sensitivity() -> None:
    sensitivity = pd.read_csv(OUTPUT_DIR / "sensitivity_analysis.csv")
    missing = REQUIRED_SENSITIVITY_COLUMNS - set(sensitivity.columns)
    _assert(not missing, f"Missing sensitivity columns: {sorted(missing)}")
    _assert(
        sensitivity["rank_volatility_score"].between(0, 100).all(),
        "Rank volatility score outside 0-100",
    )


def validate_html_chart_references() -> None:
    html_path = REPORT_DIR / "casemiro_replacement_report.html"
    html = html_path.read_text(encoding="utf-8")
    referenced = re.findall(r'src="([^"]+\.png)"', html)
    _assert(referenced, "HTML does not reference any chart files")
    for src in referenced:
        chart_path = (html_path.parent / src).resolve()
        _assert(chart_path.exists(), f"HTML references missing chart: {src}")


def main() -> None:
    validate_required_files()
    validate_scores()
    validate_sensitivity()
    validate_html_chart_references()
    print("Validation passed.")


if __name__ == "__main__":
    main()
