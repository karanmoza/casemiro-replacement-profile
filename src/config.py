"""Project configuration for the Casemiro Replacement Profile."""

from __future__ import annotations

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

CATEGORY_WEIGHTS = {
    "defensive_protection": 0.30,
    "transition_control": 0.25,
    "possession_security": 0.25,
    "progressive_value": 0.15,
    "age_availability": 0.05,
}

# Backwards-compatible alias used by older notebooks.
WEIGHTS = CATEGORY_WEIGHTS

CATEGORY_LABELS = {
    "defensive_protection": "Defensive protection",
    "transition_control": "Transition control",
    "possession_security": "Possession security",
    "progressive_value": "Progressive value",
    "age_availability": "Age / availability",
}

METRIC_GROUPS = {
    "defensive_protection": [
        {
            "metric": "tackles_interceptions_per90",
            "label": "Tackles + interceptions per 90",
            "higher_is_better": True,
            "explanation": "Captures ball-winning activity and defensive involvement.",
            "caveat": "Activity volume is role- and team-state dependent.",
        },
        {
            "metric": "interceptions_per90",
            "label": "Interceptions per 90",
            "higher_is_better": True,
            "explanation": "Captures anticipation and ability to cut passing lanes.",
            "caveat": "Can be inflated by teams defending deeper or without the ball.",
        },
        {
            "metric": "dribblers_tackled_pct",
            "label": "Dribblers tackled %",
            "higher_is_better": True,
            "explanation": "Captures one-v-one defensive reliability.",
            "caveat": "Does not show how often a player is isolated.",
        },
        {
            "metric": "blocks_per90",
            "label": "Blocks per 90",
            "higher_is_better": True,
            "explanation": "Captures defensive presence in lanes and around the box.",
            "caveat": "Blocks can reflect exposure as much as quality.",
        },
        {
            "metric": "aerial_duel_win_pct",
            "label": "Aerial duel win %",
            "higher_is_better": True,
            "explanation": "Captures physical defensive floor.",
            "caveat": "Aerial volume and opponent targeting are not captured here.",
        },
        {
            "metric": "def_mid_third_actions_per90",
            "label": "Defensive/middle-third actions per 90",
            "higher_is_better": True,
            "explanation": "Captures activity in zones relevant to a deeper midfielder.",
            "caveat": "Zone definitions vary across public providers.",
        },
    ],
    "transition_control": [
        {
            "metric": "ball_recoveries_per90",
            "label": "Ball recoveries per 90",
            "higher_is_better": True,
            "explanation": "Captures ability to regain loose balls and stabilize broken play.",
            "caveat": "Recoveries are partly created by team pressing structure.",
        },
        {
            "metric": "pressure_regains_per90",
            "label": "Pressure/counterpressure regains per 90",
            "higher_is_better": True,
            "explanation": "Captures whether the player helps stop counters early.",
            "caveat": "Public aggregate sources do not define pressure regains identically.",
        },
        {
            "metric": "def_actions_after_loss_per90",
            "label": "Defensive actions after possession loss",
            "higher_is_better": True,
            "explanation": "Captures reaction immediately after possession changes.",
            "caveat": "Best treated as a proxy without full event-sequence context.",
        },
        {
            "metric": "fouls_committed_per90",
            "label": "Fouls committed per 90",
            "higher_is_better": False,
            "explanation": "Lower is better; repeated fouling can indicate late control or transition stress.",
            "caveat": "Some tactical fouling is deliberate and context dependent.",
        },
        {
            "metric": "cards_per90",
            "label": "Cards per 90",
            "higher_is_better": False,
            "explanation": "Lower is better; discipline matters for a deeper midfielder.",
            "caveat": "Refereeing and league context affect card rates.",
        },
        {
            "metric": "miscontrols_per90",
            "label": "Miscontrols per 90",
            "higher_is_better": False,
            "explanation": "Lower is better; poor control can trigger transitions.",
            "caveat": "Miscontrol definitions vary by provider.",
        },
        {
            "metric": "dispossessed_per90",
            "label": "Dispossessed per 90",
            "higher_is_better": False,
            "explanation": "Lower is better; being dispossessed in midfield creates defensive exposure.",
            "caveat": "High-touch players face more opportunities to be dispossessed.",
        },
    ],
    "possession_security": [
        {
            "metric": "pass_completion_pct",
            "label": "Pass completion %",
            "higher_is_better": True,
            "explanation": "Captures basic reliability in possession.",
            "caveat": "Completion rate does not separate easy passes from pressured passes.",
        },
        {
            "metric": "short_medium_pass_completion_pct",
            "label": "Short/medium pass completion %",
            "higher_is_better": True,
            "explanation": "Captures security in circulation phases.",
            "caveat": "Can be boosted by low-risk team structures.",
        },
        {
            "metric": "passes_received_per90",
            "label": "Passes received per 90",
            "higher_is_better": True,
            "explanation": "Captures availability to receive and connect play.",
            "caveat": "Team possession share affects receiving volume.",
        },
        {
            "metric": "touches_per90",
            "label": "Touches per 90",
            "higher_is_better": True,
            "explanation": "Captures involvement and ability to stay connected to possession.",
            "caveat": "Volume should be paired with turnover safety.",
        },
        {
            "metric": "dispossessed_per_touch",
            "label": "Dispossessed per touch",
            "higher_is_better": False,
            "explanation": "Lower is better; captures ball security relative to involvement.",
            "caveat": "Does not identify pitch location of dispossessions.",
        },
        {
            "metric": "miscontrols_per_touch",
            "label": "Miscontrols per touch",
            "higher_is_better": False,
            "explanation": "Lower is better; captures technical security under involvement.",
            "caveat": "Does not distinguish pressure level.",
        },
        {
            "metric": "turnover_rate",
            "label": "Turnover rate",
            "higher_is_better": False,
            "explanation": "Lower is better; central midfield turnovers create transition risk.",
            "caveat": "Combines multiple public turnover proxies.",
        },
    ],
    "progressive_value": [
        {
            "metric": "progressive_passes_per90",
            "label": "Progressive passes per 90",
            "higher_is_better": True,
            "explanation": "Captures forward passing value.",
            "caveat": "Progressive pass definitions vary by source.",
        },
        {
            "metric": "progressive_carries_per90",
            "label": "Progressive carries per 90",
            "higher_is_better": True,
            "explanation": "Captures ability to move possession forward by carrying.",
            "caveat": "Carrying volume depends on role and team spacing.",
        },
        {
            "metric": "passes_into_final_third_per90",
            "label": "Passes into final third per 90",
            "higher_is_better": True,
            "explanation": "Captures territory-gaining passing.",
            "caveat": "Final-third entries do not measure pass difficulty.",
        },
        {
            "metric": "carries_into_final_third_per90",
            "label": "Carries into final third per 90",
            "higher_is_better": True,
            "explanation": "Captures territory-gaining carrying.",
            "caveat": "May favor players in more open transition systems.",
        },
        {
            "metric": "progressive_passing_distance_per90",
            "label": "Progressive passing distance per 90",
            "higher_is_better": True,
            "explanation": "Captures volume and distance of forward passing.",
            "caveat": "Long-distance progression is not always better than secure circulation.",
        },
        {
            "metric": "live_ball_sca_per90",
            "label": "Live-ball shot-creating actions per 90",
            "higher_is_better": True,
            "explanation": "Low-weight proxy for useful possession contribution near chance creation.",
            "caveat": "This is not a creator search; it is only a supporting signal.",
        },
    ],
    "age_availability": [
        {
            "metric": "age_score",
            "label": "Age score",
            "higher_is_better": True,
            "explanation": "Rewards players in a more useful squad-building age band.",
            "caveat": "Age is a proxy, not a medical or development projection.",
        },
        {
            "metric": "minutes_score",
            "label": "Minutes played score",
            "higher_is_better": True,
            "explanation": "Rewards players with enough recent minutes to make the signal more reliable.",
            "caveat": "Minutes do not replace injury-history or medical review.",
        },
    ],
}

CATEGORY_METRICS = {
    category: [metric["metric"] for metric in metrics]
    for category, metrics in METRIC_GROUPS.items()
}

METRIC_ALIASES = {
    "aerial_duel_win_pct": "aerial_win_pct",
    "def_actions_after_loss_per90": "defensive_actions_after_loss_per90",
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
    "aerial_duel_win_pct",
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

SENSITIVITY_SCENARIOS = {
    "base": CATEGORY_WEIGHTS,
    "defensive_heavy": {
        "defensive_protection": 0.40,
        "transition_control": 0.25,
        "possession_security": 0.20,
        "progressive_value": 0.10,
        "age_availability": 0.05,
    },
    "possession_heavy": {
        "defensive_protection": 0.25,
        "transition_control": 0.20,
        "possession_security": 0.35,
        "progressive_value": 0.15,
        "age_availability": 0.05,
    },
    "transition_heavy": {
        "defensive_protection": 0.25,
        "transition_control": 0.35,
        "possession_security": 0.20,
        "progressive_value": 0.15,
        "age_availability": 0.05,
    },
    "progression_heavy": {
        "defensive_protection": 0.25,
        "transition_control": 0.20,
        "possession_security": 0.20,
        "progressive_value": 0.30,
        "age_availability": 0.05,
    },
    "equal_weight": {
        "defensive_protection": 0.25,
        "transition_control": 0.25,
        "possession_security": 0.25,
        "progressive_value": 0.20,
        "age_availability": 0.05,
    },
}

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
