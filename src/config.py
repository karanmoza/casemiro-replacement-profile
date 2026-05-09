"""Project configuration for the Casemiro Replacement Profile."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DATA_OUTPUT_DIR = DATA_DIR / "outputs"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
REPORT_DIR = PROJECT_ROOT / "reports"
CHART_DIR = REPORT_DIR / "charts"

SAMPLE_FBREF_PATH = RAW_DIR / "sample_fbref_player_stats.csv"

WEIGHTS = {
    "defensive_protection": 0.30,
    "transition_control": 0.25,
    "possession_security": 0.25,
    "progressive_value": 0.15,
    "age_availability": 0.05,
}

CATEGORY_LABELS = {
    "defensive_protection": "Defensive protection",
    "transition_control": "Transition control",
    "possession_security": "Possession security",
    "progressive_value": "Progressive value",
    "age_availability": "Age / availability",
}

CATEGORY_METRICS = {
    "defensive_protection": [
        "tackles_interceptions_per90",
        "dribblers_tackled_pct",
        "interceptions_per90",
        "blocks_per90",
        "aerial_win_pct",
        "def_mid_third_actions_per90",
    ],
    "transition_control": [
        "ball_recoveries_per90",
        "pressure_regains_per90",
        "fouls_committed_per90_inv",
        "cards_per90_inv",
        "miscontrols_per90_inv",
        "dispossessed_per90_inv",
        "defensive_actions_after_loss_per90",
    ],
    "possession_security": [
        "pass_completion_pct",
        "short_medium_pass_completion_pct",
        "passes_received_per90",
        "touches_per90",
        "dispossessed_per_touch_inv",
        "miscontrols_per_touch_inv",
        "turnover_rate_inv",
    ],
    "progressive_value": [
        "progressive_passes_per90",
        "progressive_carries_per90",
        "passes_into_final_third_per90",
        "carries_into_final_third_per90",
        "progressive_passing_distance_per90",
        "live_ball_sca_per90",
    ],
    "age_availability": ["age_score", "minutes_score",],
}

RAW_COUNT_COLUMNS = [
    "tackles_interceptions",
    "interceptions",
    "blocks",
    "def_mid_third_actions",
    "ball_recoveries",
    "pressure_regains",
    "fouls_committed",
    "cards",
    "miscontrols",
    "dispossessed",
    "defensive_actions_after_loss",
    "passes_received",
    "touches",
    "progressive_passes",
    "progressive_carries",
    "passes_into_final_third",
    "carries_into_final_third",
    "progressive_passing_distance",
    "live_ball_sca",
]

DIRECT_PERCENT_COLUMNS = [
    "dribblers_tackled_pct",
    "aerial_win_pct",
    "pass_completion_pct",
    "short_medium_pass_completion_pct",
]

INVERSE_RAW_METRICS = [
    "fouls_committed_per90",
    "cards_per90",
    "miscontrols_per90",
    "dispossessed_per90",
    "dispossessed_per_touch",
    "miscontrols_per_touch",
    "turnover_rate",
]

SHORTLIST_SIZE = 15
CASEMIRO_NAME = "Casemiro"
AS_OF_DATE = "2026-05-06"
CURRENT_AS_OF = "May 6, 2026"
MIN_CATEGORY_SCORE = 50
MIN_DEFENSIVE_PROTECTION_SCORE = 45
REQUIRE_ABOVE_MIN_EVERY_CATEGORY = False

ALLOWED_LEAGUES = {
    "Premier League",
    "La Liga",
    "Primeira Liga",
    "Bundesliga",
    "Ligue 1",
    "Serie A",
}

EXCLUDED_SQUADS = {
    "Arsenal",
    "Chelsea",
    "Liverpool",
    "Manchester City",
}
