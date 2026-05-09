"""Visualization functions for the recruitment framework."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .config import CASEMIRO_NAME, CATEGORY_LABELS, CATEGORY_METRICS
from .scoring import filter_target_candidates


COLOR_PRIMARY = "#B11226"
COLOR_SECONDARY = "#1F2933"
COLOR_ACCENT = "#2F80ED"
COLOR_MUTED = "#E8ECEF"


def setup_style() -> None:
    """Apply a restrained portfolio-chart style."""

    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#CDD5DF",
            "axes.labelcolor": COLOR_SECONDARY,
            "xtick.color": COLOR_SECONDARY,
            "ytick.color": COLOR_SECONDARY,
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
        }
    )


def save_ranked_score_bar(shortlist: pd.DataFrame, path: str | Path) -> Path:
    """Save ranked Control Midfielder Score bar chart."""

    setup_style()
    path = Path(path)
    ordered = shortlist.sort_values("control_midfielder_score", ascending=True)
    fig, ax = plt.subplots(figsize=(11, 8))
    colors = [COLOR_PRIMARY if player == CASEMIRO_NAME else COLOR_ACCENT for player in ordered["player"]]
    ax.barh(ordered["player"], ordered["control_midfielder_score"], color=colors)
    ax.set_xlabel("Control Midfielder Score")
    ax.set_ylabel("")
    ax.set_title("Ranked Published Shortlist")
    ax.set_xlim(0, 100)
    for idx, value in enumerate(ordered["control_midfielder_score"]):
        ax.text(value + 0.8, idx, f"{value:.1f}", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path

def save_category_heatmap(category_scores: pd.DataFrame, path: str | Path, top_n: int = 15) -> Path:
    """Save category heatmap for shortlisted players."""

    setup_style()
    path = Path(path)
    display_cols = list(CATEGORY_LABELS.values())
    heat = category_scores.head(top_n).set_index("player")[display_cols]
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(
        heat,
        ax=ax,
        cmap="RdYlGn",
        vmin=0,
        vmax=100,
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Percentile-style category score"},
    )
    ax.set_title("Shortlist Category Profile")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def save_radar_chart(scored: pd.DataFrame, path: str | Path, candidate_count: int = 4) -> Path:
    """Save radar comparison of Casemiro and leading candidates."""

    setup_style()
    path = Path(path)
    category_cols = list(CATEGORY_METRICS.keys())
    labels = [CATEGORY_LABELS[col] for col in category_cols]

    references = scored[scored["player"].isin([CASEMIRO_NAME, "Manuel Ugarte"])]
    top_candidates = filter_target_candidates(scored).head(candidate_count)
    casemiro = references.sort_values("player")
    radar_df = pd.concat([casemiro, top_candidates], ignore_index=True)

    angles = np.linspace(0, 2 * np.pi, len(category_cols), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw={"polar": True})
    palette = [COLOR_PRIMARY, COLOR_ACCENT, "#0EAD69", "#F2A65A", "#5B5F97"]
    for idx, (_, row) in enumerate(radar_df.iterrows()):
        values = row[category_cols].astype(float).tolist()
        values += values[:1]
        ax.plot(angles, values, linewidth=2.2, label=row["player"], color=palette[idx % len(palette)])
        ax.fill(angles, values, alpha=0.08, color=palette[idx % len(palette)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_title("Casemiro vs Shortlisted Control Midfielders", pad=28)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.12), frameon=False, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def save_security_defence_scatter(scored: pd.DataFrame, path: str | Path, top_n: int = 18) -> Path:
    """Save scatter: possession security vs defensive protection."""

    setup_style()
    path = Path(path)
    data = filter_target_candidates(scored).head(top_n).copy()
    sizes = 80 + data["progressive_value"] * 5
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.scatter(
        data["possession_security"],
        data["defensive_protection"],
        s=sizes,
        c=np.where(data["player"].eq(CASEMIRO_NAME), COLOR_PRIMARY, COLOR_ACCENT),
        alpha=0.78,
        edgecolor="white",
        linewidth=1.2,
    )
    for _, row in data.iterrows():
        high_security = row["possession_security"] > 82
        x_offset = -1.0 if high_security else 0.8
        alignment = "right" if high_security else "left"
        ax.text(
            row["possession_security"] + x_offset,
            row["defensive_protection"] + 0.5,
            row["player"],
            fontsize=9,
            ha=alignment,
            clip_on=False,
        )
    ax.set_xlabel("Possession security")
    ax.set_ylabel("Defensive protection")
    ax.set_title("Control Lens: Security vs Defensive Floor")
    ax.set_xlim(-2, 108)
    ax.set_ylim(0, 104)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def save_sensitivity_chart(sensitivity: pd.DataFrame, path: str | Path) -> Path:
    """Save rank sensitivity chart for the top candidates."""

    setup_style()
    path = Path(path)
    pivot = sensitivity.pivot_table(index="player", columns="scenario", values="rank", aggfunc="min")
    pivot = pivot.loc[pivot.min(axis=1).sort_values().index]
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(
        pivot,
        ax=ax,
        cmap="viridis_r",
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Rank under scenario"},
    )
    ax.set_title("Sensitivity Analysis: Rank Stability Under Weight Changes")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path
