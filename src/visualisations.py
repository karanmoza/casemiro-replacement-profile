"""Visualization functions for the recruitment framework."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .config import CASEMIRO_NAME, CATEGORY_LABELS, CATEGORY_METRICS, MIN_DEFENSIVE_PROTECTION_SCORE
from .scoring import filter_target_candidates


# Matched to the Ole counterfactual project's restrained palette.
COLOR_PRIMARY = "#9f1d20"
COLOR_SECONDARY = "#16324f"
COLOR_ACCENT = "#d86a6d"
COLOR_GRAY = "#5b6573"
COLOR_LIGHT = "#f5f1eb"
COLOR_GREEN = "#2e8b57"
COLOR_GOLD = "#b88a1b"
COLOR_MUTED = "#d9dee5"


def setup_style() -> None:
    """Apply a restrained portfolio-chart style."""

    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": COLOR_MUTED,
            "axes.labelcolor": COLOR_SECONDARY,
            "xtick.color": COLOR_SECONDARY,
            "ytick.color": COLOR_SECONDARY,
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.titlesize": 17,
            "axes.labelsize": 11,
            "grid.color": COLOR_MUTED,
            "grid.alpha": 0.55,
        }
    )


def _save(fig: plt.Figure, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return path


def _metric_score_cols(metrics: list[str], scored: pd.DataFrame) -> list[str]:
    return [f"{metric}_score" for metric in metrics if f"{metric}_score" in scored.columns]


def _selected(scored: pd.DataFrame, players: list[str]) -> pd.DataFrame:
    return scored[scored["player"].isin(players)].copy()


def save_ranked_score_bar(shortlist: pd.DataFrame, path: str | Path) -> Path:
    """Save ranked Control Midfielder Score bar chart."""

    setup_style()
    ordered = shortlist.sort_values("control_midfielder_score", ascending=True)
    fig, ax = plt.subplots(figsize=(11, 8))
    colors = [
        COLOR_PRIMARY if idx < 3 else COLOR_SECONDARY for idx, _ in enumerate(ordered["player"])
    ]
    ax.barh(ordered["player"], ordered["control_midfielder_score"], color=colors)
    ax.set_xlabel("Final weighted Control Midfielder Score")
    ax.set_ylabel("")
    ax.set_title("Ranked Published Shortlist", loc="left", pad=20)
    ax.text(
        0,
        1.01,
        "Bar length is the final weighted score, not a direct scouting grade.",
        transform=ax.transAxes,
        fontsize=10,
        color=COLOR_GRAY,
    )
    ax.set_xlim(0, 100)
    for idx, value in enumerate(ordered["control_midfielder_score"]):
        ax.text(value + 0.8, idx, f"{value:.1f}", va="center", fontsize=9, color=COLOR_GRAY)
    return _save(fig, path)


def save_category_heatmap(category_scores: pd.DataFrame, path: str | Path, top_n: int = 15) -> Path:
    """Save category heatmap for shortlisted players."""

    setup_style()
    display_cols = list(CATEGORY_LABELS.values())
    heat = category_scores.head(top_n).set_index("player")[display_cols]
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(
        heat,
        ax=ax,
        cmap=sns.diverging_palette(10, 130, as_cmap=True),
        vmin=0,
        vmax=100,
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Category score"},
    )
    ax.set_title("Shortlist Category Profile", loc="left", pad=18)
    ax.set_xlabel("")
    ax.set_ylabel("")
    return _save(fig, path)


def save_radar_chart(scored: pd.DataFrame, path: str | Path, candidate_count: int = 3) -> Path:
    """Save radar comparison of Casemiro, Ugarte, and leading candidates."""

    setup_style()
    category_cols = list(CATEGORY_METRICS.keys())
    labels = [CATEGORY_LABELS[col] for col in category_cols]

    references = scored[scored["player"].isin([CASEMIRO_NAME, "Manuel Ugarte"])]
    top_candidates = filter_target_candidates(scored).head(candidate_count)
    radar_df = pd.concat([references, top_candidates], ignore_index=True).drop_duplicates("player")

    angles = np.linspace(0, 2 * np.pi, len(category_cols), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw={"polar": True})
    palette = [COLOR_PRIMARY, COLOR_SECONDARY, COLOR_GREEN, COLOR_GOLD, COLOR_ACCENT]
    for idx, (_, row) in enumerate(radar_df.iterrows()):
        values = row[category_cols].astype(float).tolist()
        values += values[:1]
        ax.plot(
            angles, values, linewidth=2.2, label=row["player"], color=palette[idx % len(palette)]
        )
        ax.fill(angles, values, alpha=0.08, color=palette[idx % len(palette)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_title("Casemiro and Ugarte References", pad=28)
    ax.legend(loc="upper right", bbox_to_anchor=(1.34, 1.12), frameon=False, fontsize=9)
    return _save(fig, path)


def save_security_defence_scatter(scored: pd.DataFrame, path: str | Path, top_n: int = 18) -> Path:
    """Save control matrix: possession security vs defensive protection."""

    setup_style()
    data = filter_target_candidates(scored).head(top_n).copy()
    references = scored[scored["player"].isin([CASEMIRO_NAME, "Manuel Ugarte"])]
    data = pd.concat([data, references], ignore_index=True).drop_duplicates("player")
    sizes = 90 + data["progressive_value"] * 4.8
    colors = np.where(data["passed_defensive_gate"], COLOR_SECONDARY, COLOR_ACCENT)
    fig, ax = plt.subplots(figsize=(11.5, 8))
    ax.scatter(
        data["possession_security"],
        data["defensive_protection"],
        s=sizes,
        c=colors,
        alpha=0.78,
        edgecolor="white",
        linewidth=1.2,
    )
    ax.axvline(70, color=COLOR_GREEN, linestyle="--", linewidth=1.2)
    ax.axhline(MIN_DEFENSIVE_PROTECTION_SCORE, color=COLOR_PRIMARY, linestyle="--", linewidth=1.2)
    ax.fill_betweenx([MIN_DEFENSIVE_PROTECTION_SCORE, 100], 70, 100, color=COLOR_GREEN, alpha=0.08)
    ax.text(71, 94, "Control target zone", fontsize=10, color=COLOR_GREEN, weight="bold")
    for _, row in data.iterrows():
        if row["player"] in {
            "Exequiel Palacios",
            "Johnny Cardoso",
            "Morten Hjulmand",
            "Elliot Anderson",
            "Casemiro",
            "Manuel Ugarte",
            "Florentino Luís",
        }:
            ax.text(
                row["possession_security"] + 0.8,
                row["defensive_protection"] + 0.6,
                row["player"],
                fontsize=9,
                clip_on=False,
            )
    ax.set_xlabel("Possession security category score")
    ax.set_ylabel("Defensive protection category score")
    ax.set_title("Control Matrix: Security vs Defensive Floor", loc="left", pad=20)
    ax.text(
        0,
        1.01,
        "Who adds possession security without losing the minimum defensive base?",
        transform=ax.transAxes,
        fontsize=10,
        color=COLOR_GRAY,
    )
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 105)
    return _save(fig, path)


def save_defensive_gate_diagnostic(scored: pd.DataFrame, path: str | Path) -> Path:
    """Save heatmap of defensive input metric scores for selected players."""

    setup_style()
    players = [
        "Exequiel Palacios",
        "Elliot Anderson",
        "Johnny Cardoso",
        "Casemiro",
        "Manuel Ugarte",
        "Florentino Luís",
    ]
    metrics = [
        "tackles_interceptions_per90",
        "interceptions_per90",
        "dribblers_tackled_pct",
        "blocks_per90",
        "aerial_duel_win_pct",
        "def_mid_third_actions_per90",
    ]
    cols = _metric_score_cols(metrics, scored)
    data = _selected(scored, players).set_index("player")[cols]
    data.columns = [
        col.replace("_score", "").replace("_per90", "/90").replace("_", " ") for col in cols
    ]
    fig, ax = plt.subplots(figsize=(12.5, 6.5))
    sns.heatmap(
        data,
        ax=ax,
        cmap=sns.light_palette(COLOR_PRIMARY, as_cmap=True),
        vmin=0,
        vmax=100,
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Input metric percentile"},
    )
    ax.set_title("Defensive Gate Diagnostic", loc="left", pad=18)
    ax.set_xlabel("")
    ax.set_ylabel("")
    return _save(fig, path)


def save_possession_security_breakdown(scored: pd.DataFrame, path: str | Path) -> Path:
    """Save heatmap of possession-security input metric scores."""

    setup_style()
    players = [
        "Exequiel Palacios",
        "Johnny Cardoso",
        "Angelo Stiller",
        "Aleix García",
        "Adam Wharton",
        "Manuel Ugarte",
        "Casemiro",
    ]
    metrics = [
        "pass_completion_pct",
        "short_medium_pass_completion_pct",
        "passes_received_per90",
        "touches_per90",
        "dispossessed_per_touch",
        "miscontrols_per_touch",
        "turnover_rate",
    ]
    cols = _metric_score_cols(metrics, scored)
    data = _selected(scored, players).set_index("player")[cols]
    data.columns = [
        col.replace("_score", "").replace("_per90", "/90").replace("_", " ") for col in cols
    ]
    fig, ax = plt.subplots(figsize=(13, 7))
    sns.heatmap(
        data,
        ax=ax,
        cmap=sns.light_palette(COLOR_SECONDARY, as_cmap=True),
        vmin=0,
        vmax=100,
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Input metric percentile"},
    )
    ax.set_title("Possession Security Breakdown", loc="left", pad=18)
    ax.set_xlabel("")
    ax.set_ylabel("")
    return _save(fig, path)


def save_transition_chaos_map(scored: pd.DataFrame, path: str | Path) -> Path:
    """Save scatter showing transition activity, discipline, and turnover safety."""

    setup_style()
    data = filter_target_candidates(scored).head(12).copy()
    watch = scored[
        scored["player"].isin(["Elliot Anderson", "Angelo Stiller", "Manuel Ugarte", "Casemiro"])
    ]
    data = pd.concat([data, watch], ignore_index=True).drop_duplicates("player")
    recovery_cols = _metric_score_cols(["ball_recoveries_per90", "pressure_regains_per90"], data)
    discipline_cols = _metric_score_cols(["fouls_committed_per90", "cards_per90"], data)
    turnover_cols = _metric_score_cols(
        ["miscontrols_per90", "dispossessed_per90", "turnover_rate"], data
    )
    data["recovery_regain_score"] = data[recovery_cols].mean(axis=1)
    data["discipline_safety_score"] = data[discipline_cols].mean(axis=1)
    data["turnover_safety_score"] = data[turnover_cols].mean(axis=1)
    fig, ax = plt.subplots(figsize=(11.5, 8))
    colors = np.where(data["passed_defensive_gate"], COLOR_GREEN, COLOR_ACCENT)
    ax.scatter(
        data["recovery_regain_score"],
        data["discipline_safety_score"],
        s=80 + data["turnover_safety_score"] * 4,
        c=colors,
        alpha=0.78,
        edgecolor="white",
        linewidth=1.2,
    )
    ax.axvline(50, color=COLOR_MUTED, linestyle="--", linewidth=1)
    ax.axhline(50, color=COLOR_MUTED, linestyle="--", linewidth=1)
    ax.text(68, 89, "Clean transition stabilizers", color=COLOR_GREEN, fontsize=10, weight="bold")
    ax.text(66, 12, "Active but risky", color=COLOR_PRIMARY, fontsize=10, weight="bold")
    ax.text(5, 88, "Safe but passive", color=COLOR_GRAY, fontsize=10, weight="bold")
    ax.text(6, 12, "Transition concern", color=COLOR_ACCENT, fontsize=10, weight="bold")
    for _, row in data.iterrows():
        if row["player"] in {
            "Exequiel Palacios",
            "Johnny Cardoso",
            "Morten Hjulmand",
            "Elliot Anderson",
            "Manuel Ugarte",
            "Casemiro",
        }:
            ax.text(
                row["recovery_regain_score"] + 0.8,
                row["discipline_safety_score"] + 0.8,
                row["player"],
                fontsize=9,
            )
    ax.set_xlabel("Recovery / pressure-regain score")
    ax.set_ylabel("Discipline / safety score")
    ax.set_title("Transition Chaos Map", loc="left", pad=20)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 105)
    return _save(fig, path)


def save_progression_type_chart(scored: pd.DataFrame, path: str | Path) -> Path:
    """Save scatter distinguishing passing and carrying progression types."""

    setup_style()
    data = filter_target_candidates(scored).head(12).copy()
    refs = scored[scored["player"].isin(["Manuel Ugarte", "Casemiro", "Elliot Anderson"])]
    data = pd.concat([data, refs], ignore_index=True).drop_duplicates("player")
    size_cols = _metric_score_cols(
        ["passes_into_final_third_per90", "carries_into_final_third_per90"], data
    )
    data["territory_entry_score"] = data[size_cols].mean(axis=1)
    fig, ax = plt.subplots(figsize=(11.5, 8))
    ax.scatter(
        data["progressive_passes_per90_score"],
        data["progressive_carries_per90_score"],
        s=90 + data["territory_entry_score"] * 4.8,
        c=COLOR_SECONDARY,
        alpha=0.76,
        edgecolor="white",
        linewidth=1.2,
    )
    ax.axvline(50, color=COLOR_MUTED, linestyle="--", linewidth=1)
    ax.axhline(50, color=COLOR_MUTED, linestyle="--", linewidth=1)
    ax.text(68, 90, "Balanced progressors", color=COLOR_GREEN, fontsize=10, weight="bold")
    ax.text(69, 10, "Pass progressors", color=COLOR_SECONDARY, fontsize=10, weight="bold")
    ax.text(8, 89, "Carry progressors", color=COLOR_GOLD, fontsize=10, weight="bold")
    ax.text(8, 10, "Low-progression anchors", color=COLOR_GRAY, fontsize=10, weight="bold")
    for _, row in data.iterrows():
        if row["player"] in {
            "Exequiel Palacios",
            "Johnny Cardoso",
            "Morten Hjulmand",
            "Elliot Anderson",
            "Florentino Luís",
            "Manuel Ugarte",
            "Casemiro",
        }:
            ax.text(
                row["progressive_passes_per90_score"] + 0.8,
                row["progressive_carries_per90_score"] + 0.8,
                row["player"],
                fontsize=9,
            )
    ax.set_xlabel("Progressive passes percentile")
    ax.set_ylabel("Progressive carries percentile")
    ax.set_title("Progression Type Chart", loc="left", pad=20)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 105)
    return _save(fig, path)


def save_sensitivity_rank_stability(sensitivity: pd.DataFrame, path: str | Path) -> Path:
    """Save dumbbell chart of best-to-worst rank across scenarios."""

    setup_style()
    data = sensitivity.sort_values("average_rank").head(12).copy()
    fig, ax = plt.subplots(figsize=(11, 8))
    y = np.arange(len(data))
    ax.hlines(y, data["best_rank"], data["worst_rank"], color=COLOR_MUTED, linewidth=4)
    ax.scatter(data["best_rank"], y, color=COLOR_GREEN, s=90, label="Best rank")
    ax.scatter(data["worst_rank"], y, color=COLOR_ACCENT, s=90, label="Worst rank")
    ax.scatter(data["rank_base"], y, color=COLOR_PRIMARY, s=80, zorder=3, label="Base rank")
    ax.set_yticks(y)
    ax.set_yticklabels(data["player"])
    ax.invert_yaxis()
    ax.invert_xaxis()
    ax.set_xlabel("Rank across sensitivity scenarios")
    ax.set_title("Sensitivity Rank Volatility", loc="left", pad=20)
    ax.legend(frameon=False, loc="lower right")
    return _save(fig, path)


def save_sensitivity_chart(sensitivity: pd.DataFrame, path: str | Path) -> Path:
    """Save heatmap for scenario ranks."""

    setup_style()
    rank_cols = [
        "rank_base",
        "rank_defensive_heavy",
        "rank_possession_heavy",
        "rank_transition_heavy",
        "rank_progression_heavy",
        "rank_equal_weight",
    ]
    data = sensitivity.set_index("player")[rank_cols].head(12)
    data.columns = [col.replace("rank_", "").replace("_", " ").title() for col in data.columns]
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(
        data,
        ax=ax,
        cmap="viridis_r",
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Rank under scenario"},
    )
    ax.set_title("Sensitivity Analysis: Scenario Ranks", loc="left", pad=18)
    ax.set_xlabel("")
    ax.set_ylabel("")
    return _save(fig, path)


def save_archetype_summary(explanation: pd.DataFrame, path: str | Path) -> Path:
    """Save a compact table-like archetype summary."""

    setup_style()
    display = explanation.head(12)[
        [
            "player",
            "archetype_label",
            "strongest_football_category",
            "weakest_football_category",
            "gate_margin",
        ]
    ].copy()
    display["strongest_football_category"] = (
        display["strongest_football_category"].str.replace("_", " ").str.title()
    )
    display["weakest_football_category"] = (
        display["weakest_football_category"].str.replace("_", " ").str.title()
    )
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.axis("off")
    table = ax.table(
        cellText=display.values,
        colLabels=["Player", "Archetype", "Strongest", "Weakest", "Gate margin"],
        loc="center",
        cellLoc="left",
        colLoc="left",
        colWidths=[0.18, 0.32, 0.18, 0.18, 0.12],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("white")
        if row == 0:
            cell.set_facecolor(COLOR_SECONDARY)
            cell.get_text().set_color("white")
            cell.get_text().set_weight("bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f8fafc")
    ax.set_title("Archetype Summary", loc="left", pad=18, fontsize=17, weight="bold")
    return _save(fig, path)
