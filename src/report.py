"""Run the end-to-end project and generate portfolio outputs."""

from __future__ import annotations

from html import escape
from pathlib import Path
from textwrap import wrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages

from .config import (
    CATEGORY_LABELS,
    CATEGORY_METRICS,
    CHART_DIR,
    DATA_OUTPUT_DIR,
    OUTPUT_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
    REPORT_DIR,
    WEIGHTS,
    MIN_DEFENSIVE_PROTECTION_SCORE,
)
from .load_fbref import PLAYER_CONTEXT_MAY_2026, load_fbref_player_stats, write_sample_dataset
from .load_statsbomb import engineer_event_control_metrics, load_statsbomb_events
from .scoring import (
    build_scoring_table,
    filter_target_candidates,
    make_category_scores,
    make_filtered_out_watchlist,
    make_shortlist,
    sensitivity_analysis,
)
from .visualisations import (
    COLOR_ACCENT,
    COLOR_PRIMARY,
    save_category_heatmap,
    save_radar_chart,
    save_ranked_score_bar,
    save_security_defence_scatter,
    save_sensitivity_chart,
)


def ensure_directories() -> None:
    """Create project output directories."""

    for path in [PROCESSED_DIR, DATA_OUTPUT_DIR, OUTPUT_DIR, REPORT_DIR, CHART_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def generate_outputs(input_csv: str | Path | None = None) -> dict[str, Path]:
    """Run data loading, scoring, visualization, and report generation."""

    ensure_directories()
    write_sample_dataset()

    public_stats = load_fbref_player_stats(input_csv)
    event_data = load_statsbomb_events()
    event_metrics = engineer_event_control_metrics(event_data)
    if not event_metrics.empty:
        public_stats = public_stats.merge(event_metrics, on="player", how="left")

    scored = build_scoring_table(public_stats)
    shortlist = make_shortlist(scored)
    category_scores = make_category_scores(scored)
    sensitivity = sensitivity_analysis(scored)
    filtered_out = make_filtered_out_watchlist(scored)

    scored_path = PROCESSED_DIR / "scored_players.csv"
    shortlist_path = OUTPUT_DIR / "candidate_shortlist.csv"
    category_path = OUTPUT_DIR / "category_scores.csv"
    sensitivity_path = OUTPUT_DIR / "sensitivity_analysis.csv"
    context_path = OUTPUT_DIR / "player_context_sources.csv"
    filtered_out_path = OUTPUT_DIR / "filtered_out_watchlist.csv"
    methodology_path = OUTPUT_DIR / "scoring_methodology.csv"

    scored.to_csv(scored_path, index=False)
    shortlist.to_csv(shortlist_path, index=False)
    category_scores.to_csv(category_path, index=False)
    sensitivity.to_csv(sensitivity_path, index=False)
    filtered_out.to_csv(filtered_out_path, index=False)
    context_sources = pd.DataFrame.from_dict(PLAYER_CONTEXT_MAY_2026, orient="index").reset_index(
        names="player"
    )
    if "is_target_candidate" in context_sources.columns:
        context_sources["is_target_candidate"] = context_sources["is_target_candidate"].where(
            context_sources["is_target_candidate"].notna(), True
        )
    context_sources.to_csv(context_path, index=False)
    _make_scoring_methodology_table().to_csv(methodology_path, index=False)

    chart_paths = {
        "ranked_bar": save_ranked_score_bar(
            shortlist, CHART_DIR / "ranked_control_midfielder_score.png"
        ),
        "category_heatmap": save_category_heatmap(
            category_scores, CHART_DIR / "category_heatmap.png"
        ),
        "radar": save_radar_chart(scored, CHART_DIR / "casemiro_candidate_radar.png"),
        "scatter": save_security_defence_scatter(
            scored, CHART_DIR / "security_vs_defensive_floor.png"
        ),
        "sensitivity": save_sensitivity_chart(sensitivity, CHART_DIR / "sensitivity_analysis.png"),
    }

    pdf_path = REPORT_DIR / "casemiro_replacement_summary.pdf"
    save_recruitment_summary_pdf(scored, shortlist, category_scores, sensitivity, pdf_path)
    html_path = REPORT_DIR / "casemiro_replacement_report.html"
    save_html_report(
        scored, shortlist, category_scores, sensitivity, filtered_out, chart_paths, html_path
    )

    return {
        "scored_players": scored_path,
        "candidate_shortlist": shortlist_path,
        "category_scores": category_path,
        "sensitivity_analysis": sensitivity_path,
        "player_context_sources": context_path,
        "filtered_out_watchlist": filtered_out_path,
        "scoring_methodology": methodology_path,
        "summary_pdf": pdf_path,
        "html_report": html_path,
        **chart_paths,
    }


def save_html_report(
    scored: pd.DataFrame,
    shortlist: pd.DataFrame,
    category_scores: pd.DataFrame,
    sensitivity: pd.DataFrame,
    filtered_out: pd.DataFrame,
    chart_paths: dict[str, Path],
    path: str | Path,
) -> Path:
    """Create a polished static HTML report from generated outputs."""

    path = Path(path)
    candidates = filter_target_candidates(scored)
    references = scored[scored["player"].isin(["Casemiro", "Manuel Ugarte"])].copy()
    top = candidates.iloc[0]
    casemiro_def = references.loc[references["player"].eq("Casemiro"), "defensive_protection"].iloc[
        0
    ]
    high_security = candidates[candidates["possession_security"] >= 70]
    high_defence = candidates[
        (candidates["control_midfielder_score"] >= 50)
        & (candidates["defensive_protection"] >= casemiro_def)
    ]

    chart_rel = {
        name: rel_path(chart_path, path.parent) for name, chart_path in chart_paths.items()
    }
    shortlist_table = shortlist[
        [
            "rank",
            "player",
            "squad",
            "league",
            "age",
            "control_midfielder_score",
            "defensive_protection",
            "transition_control",
            "possession_security",
            "progressive_value",
            "age_availability",
        ]
    ].copy()
    shortlist_table.columns = [
        "#",
        "Player",
        "Club",
        "League",
        "Age",
        "Score",
        "Defence",
        "Transition",
        "Security",
        "Progression",
        "Age/Avail.",
    ]

    watchlist_table = filtered_out.head(8)[
        [
            "player",
            "squad",
            "control_midfielder_score",
            "defensive_protection",
            "lowest_category",
            "lowest_category_score",
        ]
    ].copy()
    watchlist_table.columns = ["Player", "Club", "Score", "Defence", "Main Risk", "Risk Score"]

    reference_table = references[
        [
            "player",
            "age",
            "defensive_protection",
            "transition_control",
            "possession_security",
            "progressive_value",
        ]
    ].copy()
    reference_table.columns = [
        "Reference",
        "Age",
        "Defence",
        "Transition",
        "Security",
        "Progression",
    ]

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Casemiro Replacement Profile</title>
  <style>
    :root {{
      --ink: #111827;
      --muted: #5b6472;
      --line: #d9dee7;
      --panel: #ffffff;
      --bg: #f3f4f6;
      --red: #b11226;
      --blue: #2563eb;
      --green: #0f766e;
      --gold: #b7791f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      line-height: 1.45;
    }}
    .hero {{
      background: #101827;
      color: white;
      border-left: 12px solid var(--red);
      padding: 44px 7vw 38px;
    }}
    .eyebrow {{
      color: #cfd6e1;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
      font-weight: 700;
    }}
    h1 {{
      margin: 10px 0 12px;
      font-size: clamp(32px, 5vw, 58px);
      line-height: 1.02;
      letter-spacing: 0;
    }}
    .hero p {{
      max-width: 980px;
      margin: 0;
      font-size: 18px;
      color: #e5e7eb;
    }}
    main {{ padding: 28px 7vw 64px; }}
    section {{
      margin: 26px 0;
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: 0 16px 35px rgba(17, 24, 39, .06);
    }}
    .section-head {{
      padding: 24px 26px 8px;
      border-bottom: 1px solid #edf0f5;
    }}
    h2 {{
      margin: 0 0 6px;
      font-size: 26px;
      letter-spacing: 0;
    }}
    .section-head p {{
      margin: 0 0 12px;
      color: var(--muted);
      max-width: 980px;
    }}
    .grid-3, .grid-2 {{
      display: grid;
      gap: 18px;
      padding: 24px 26px;
    }}
    .grid-3 {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .grid-2 {{ grid-template-columns: minmax(0, 1.2fr) minmax(320px, .8fr); }}
    .card {{
      border: 1px solid var(--line);
      background: #fff;
      padding: 18px;
    }}
    .kpi {{
      border-left: 6px solid var(--blue);
      min-height: 145px;
    }}
    .kpi.red {{ border-left-color: var(--red); }}
    .kpi.green {{ border-left-color: var(--green); }}
    .label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
      font-weight: 800;
    }}
    .value {{
      margin-top: 8px;
      font-size: 28px;
      font-weight: 800;
    }}
    .note {{
      color: var(--muted);
      margin-top: 10px;
      font-size: 14px;
    }}
    .callout {{
      background: #fff7ed;
      border-left: 6px solid var(--gold);
      padding: 18px 20px;
      margin: 0 26px 24px;
    }}
    .callout strong {{ color: #7c2d12; }}
    .chart-card {{
      padding: 16px;
      border: 1px solid var(--line);
      background: white;
    }}
    img.chart {{
      width: 100%;
      height: auto;
      display: block;
      background: white;
    }}
    .explainer {{
      border-left: 5px solid var(--red);
      background: #f9fafb;
      padding: 18px 20px;
    }}
    .explainer h3, .card h3 {{
      margin: 0 0 10px;
      font-size: 18px;
    }}
    .explainer ul {{
      margin: 0;
      padding-left: 18px;
      color: #273244;
    }}
    .explainer li {{ margin: 0 0 10px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th {{
      background: #111827;
      color: white;
      text-align: left;
      padding: 10px;
      white-space: nowrap;
    }}
    td {{
      border-bottom: 1px solid #e5e7eb;
      padding: 10px;
      vertical-align: top;
    }}
    tr:nth-child(even) td {{ background: #f9fafb; }}
    .pill {{
      display: inline-block;
      padding: 4px 9px;
      border-radius: 999px;
      background: #e8eefc;
      color: #1d4ed8;
      font-size: 12px;
      font-weight: 700;
      margin: 4px 6px 0 0;
    }}
    .method {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 12px;
      padding: 24px 26px;
    }}
    .method .card {{
      border-top: 5px solid var(--blue);
      min-height: 160px;
    }}
    .small {{ font-size: 12px; color: var(--muted); }}
    footer {{
      color: var(--muted);
      font-size: 12px;
      padding: 0 7vw 40px;
    }}
    @media (max-width: 980px) {{
      .grid-3, .grid-2, .method {{ grid-template-columns: 1fr; }}
      main {{ padding: 18px; }}
      .hero {{ padding: 34px 24px; }}
      table {{ font-size: 12px; }}
    }}
  </style>
</head>
<body>
  <header class="hero">
    <div class="eyebrow">Manchester United analytics portfolio | public data | May 6, 2026</div>
    <h1>Casemiro Replacement Profile</h1>
    <p>The next signing should not only win duels. It should prevent some of them from happening.</p>
  </header>
  <main>
    <section>
      <div class="section-head">
        <h2>Executive View</h2>
        <p>This is a recruitment screen, not a signing verdict. It translates United's need for control into a repeatable public-data framework.</p>
      </div>
      <div class="grid-3">
        <div class="card kpi red">
          <div class="label">Top weighted screen</div>
          <div class="value">{escape(str(top['player']))}</div>
          <div class="note">{escape(str(top['squad']))} | score {top['control_midfielder_score']:.1f} | age {int(top['age'])}</div>
        </div>
        <div class="card kpi">
          <div class="label">Published control profiles</div>
          <div class="value">{len(high_security)} players</div>
          <div class="note">Gated shortlist candidates with possession-security score of 70+. These profiles help United reduce repeat emergency defending.</div>
        </div>
        <div class="card kpi green">
          <div class="label">Defensive reference</div>
          <div class="value">{len(high_defence)} players</div>
          <div class="note">Priority candidates above Casemiro's defensive-protection reference score.</div>
        </div>
      </div>
      <div class="callout"><strong>Interpretation:</strong> Palacios should be read as the strongest possession-control candidate in the screen, not as the strongest like-for-like Casemiro replacement. He leads the screen subject to availability and injury-history review. Cardoso is the cleaner two-axis defensive/security fit.</div>
      <div style="padding: 0 26px 24px;">{df_to_html(reference_table, 'reference-table')}</div>
    </section>

    <section>
      <div class="section-head">
        <h2>How The Score Works</h2>
        <p>Each player receives five category scores. Those categories are weighted into a single Control Midfielder Score.</p>
      </div>
      <div class="method">
        {weight_cards()}
      </div>
      <div class="callout"><strong>Plain English:</strong> A 100 does not mean world class. It means the player is high relative to this screened public-data pool. Negative events such as fouls, cards, miscontrols, dispossessions, and turnover rate are inverted so safer players score better.</div>
    </section>

    <section>
      <div class="section-head">
        <h2>1. Ranked Shortlist</h2>
        <p>The published shortlist applies a light defensive-protection gate to remove pure control profiles with limited ball-winning evidence. The gate is intentionally low because the model is screening for complementary control midfielders, not only defensive destroyers.</p>
      </div>
      <div class="grid-2">
        <div class="chart-card"><img class="chart" src="{chart_rel['ranked_bar']}" alt="Ranked published shortlist"></div>
        <div class="explainer">
          <h3>How to read it</h3>
          <ul>
            <li>The bar length is the final weighted score, not a direct scouting grade.</li>
            <li>Palacios rises because possession security and progression matter heavily in the brief.</li>
            <li>Cardoso's lower total still matters because his defensive floor is much stronger.</li>
          </ul>
        </div>
      </div>
      <div style="padding: 0 26px 26px;">{df_to_html(shortlist_table, 'shortlist-table')}</div>
    </section>

    <section>
      <div class="section-head">
        <h2>2. Control Matrix</h2>
        <p>This chart shows the main football trade-off: can the player help United control possession without losing the defensive floor?</p>
      </div>
      <div class="grid-2">
        <div class="chart-card"><img class="chart" src="{chart_rel['scatter']}" alt="Possession security versus defensive protection"></div>
        <div class="explainer">
          <h3>Scout and fan read</h3>
          <ul>
            <li>Right side means safer possession: more secure receiving, passing, and turnover profile.</li>
            <li>Higher up means stronger defensive protection relative to the pool.</li>
            <li>Bigger bubbles add more progressive value: they help United move forward, not just recycle.</li>
          </ul>
        </div>
      </div>
    </section>

    <section>
      <div class="section-head">
        <h2>3. Category Heatmap</h2>
        <p>The heatmap explains why players with similar total scores can be very different midfielders.</p>
      </div>
      <div class="grid-2">
        <div class="chart-card"><img class="chart" src="{chart_rel['category_heatmap']}" alt="Category heatmap"></div>
        <div class="explainer">
          <h3>What the colors mean</h3>
          <ul>
            <li>Green means a strength relative to the screened public-data pool.</li>
            <li>Red does not automatically rule a player out; it tells the scout what to test on video.</li>
            <li>Florentino is a defensive specialist, while Palacios and Stiller are clearer control/pass profiles.</li>
          </ul>
        </div>
      </div>
    </section>

    <section>
      <div class="section-head">
        <h2>4. Casemiro and Ugarte References</h2>
        <p>United's current midfield references help explain the target brief: preserve the ball-winning base, but add more control and progression.</p>
      </div>
      <div class="grid-2">
        <div class="chart-card"><img class="chart" src="{chart_rel['radar']}" alt="Radar comparison"></div>
        <div class="explainer">
          <h3>Why this matters</h3>
          <ul>
            <li>Casemiro is the ageing reference point for defensive responsibility, not the statistical clone target.</li>
            <li>Ugarte already covers much of the defensive/security need.</li>
            <li>The next midfielder should complement that base by adding cleaner possession and progression.</li>
          </ul>
        </div>
      </div>
    </section>

    <section>
      <div class="section-head">
        <h2>5. Sensitivity and Practicality</h2>
        <p>A good screen should not collapse when reasonable category weights move.</p>
      </div>
      <div class="grid-2">
        <div class="chart-card"><img class="chart" src="{chart_rel['sensitivity']}" alt="Sensitivity analysis"></div>
        <div class="explainer">
          <h3>What to look for</h3>
          <ul>
            <li>Stable names are less dependent on one subjective weighting choice.</li>
            <li>Age, minutes, and market value are only practical context fields.</li>
            <li>Final decisions still need video, tactical role fit, medical, contract, and fee work.</li>
          </ul>
        </div>
      </div>
    </section>

    <section>
      <div class="section-head">
        <h2>Watchlist: Removed By Defensive Gate</h2>
        <p>These players remain analytically interesting, but they do not clear the light defensive-protection threshold used for the published shortlist.</p>
      </div>
      <div style="padding: 24px 26px;">{df_to_html(watchlist_table, 'watchlist-table')}</div>
    </section>

    <section>
      <div class="section-head">
        <h2>Limitations</h2>
        <p>The strongest version of this project is honest about what public data can and cannot prove.</p>
      </div>
      <div class="grid-2">
        <div class="card">
          <h3>What this does well</h3>
          <p>It turns an abstract United need, "more control", into measurable screening traits: defensive protection, transition control, possession security, progression, and age/availability.</p>
          <span class="pill">repeatable</span><span class="pill">transparent</span><span class="pill">portfolio-ready</span>
        </div>
        <div class="card">
          <h3>What it cannot do</h3>
          <p>It cannot replace club scouting. StatsBomb open data is limited to selected competitions, public aggregate stats are not proprietary club data, and public statsbombpy access should not be treated as 360 data access.</p>
        </div>
      </div>
    </section>
  </main>
  <footer>
    Built with pandas, matplotlib, public aggregate player statistics, and StatsBomb open-data concepts for event-data role design. This is a screening framework, not a final recruitment decision model.
  </footer>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
    return path


def rel_path(path: Path, base: Path) -> str:
    return escape(str(path.relative_to(base)))


def df_to_html(df: pd.DataFrame, table_id: str) -> str:
    display = df.copy()
    for col in display.columns:
        if pd.api.types.is_float_dtype(display[col]):
            display[col] = display[col].map(lambda value: f"{value:.2f}")
    return display.to_html(index=False, escape=True, classes=f"data-table {table_id}", border=0)


def weight_cards() -> str:
    cards = []
    for category, weight in WEIGHTS.items():
        label = CATEGORY_LABELS[category]
        metrics = CATEGORY_METRICS[category]
        cards.append(
            f"""
            <div class="card">
              <div class="label">{escape(label)}</div>
              <div class="value">{int(weight * 100)}%</div>
              <div class="note">{len(metrics)} input metrics. Category score is the average of percentile-style metric scores.</div>
            </div>
            """
        )
    return "\n".join(cards)


def save_recruitment_summary_pdf(
    scored: pd.DataFrame,
    shortlist: pd.DataFrame,
    category_scores: pd.DataFrame,
    sensitivity: pd.DataFrame,
    path: str | Path,
) -> Path:
    """Create a detailed consulting-style recruitment report PDF."""

    path = Path(path)
    candidates = filter_target_candidates(scored)
    references = scored[scored["player"].isin(["Casemiro", "Manuel Ugarte"])].copy()

    with PdfPages(path) as pdf:
        _add_executive_slide(pdf, candidates, references)
        _add_methodology_slide(pdf)
        _add_ranked_score_slide(pdf, candidates)
        _add_control_matrix_slide(pdf, candidates, references)
        _add_heatmap_slide(pdf, category_scores)
        _add_sensitivity_slide(pdf, candidates, sensitivity)
        _add_candidate_notes_slide(pdf, shortlist)

    return path


def _new_slide(title: str, subtitle: str = "") -> plt.Figure:
    fig = plt.figure(figsize=(13.33, 7.5))
    fig.patch.set_facecolor("#F3F4F6")
    fig.add_artist(
        plt.Rectangle((0, 0.885), 1, 0.115, transform=fig.transFigure, color="#111827", zorder=0)
    )
    fig.add_artist(
        plt.Rectangle(
            (0, 0.885), 0.018, 0.115, transform=fig.transFigure, color=COLOR_PRIMARY, zorder=1
        )
    )
    fig.text(0.045, 0.945, title, fontsize=20, weight="bold", color="white")
    if subtitle:
        fig.text(0.045, 0.908, subtitle, fontsize=10.3, color="#D1D5DB")
    fig.text(
        0.045,
        0.04,
        "Casemiro Replacement Profile | public-data screen | as of May 6, 2026",
        fontsize=7.5,
        color="#6B7280",
    )
    fig.text(0.865, 0.04, "Not proprietary scouting data", fontsize=7.5, color="#6B7280")
    return fig


def _make_scoring_methodology_table() -> pd.DataFrame:
    rows = []
    for category, metrics in CATEGORY_METRICS.items():
        for metric in metrics:
            direction = "lower is better" if metric.endswith("_inv") else "higher is better"
            rows.append(
                {
                    "category": CATEGORY_LABELS[category],
                    "category_weight": WEIGHTS[category],
                    "metric": metric,
                    "direction_after_engineering": direction,
                    "category_score_method": "mean of metric percentile-style scores",
                }
            )
    return pd.DataFrame(rows)


def _save_slide(pdf: PdfPages, fig: plt.Figure) -> None:
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _draw_kpi(ax: plt.Axes, title: str, value: str, note: str, color: str = COLOR_ACCENT) -> None:
    ax.axis("off")
    ax.add_patch(
        plt.Rectangle(
            (0, 0), 1, 1, transform=ax.transAxes, facecolor="white", edgecolor="#D8DEE6", lw=1.0
        )
    )
    ax.add_patch(
        plt.Rectangle(
            (0, 0), 0.018, 1, transform=ax.transAxes, facecolor=color, edgecolor=color, lw=0
        )
    )
    ax.text(
        0.07,
        0.82,
        title.upper(),
        transform=ax.transAxes,
        fontsize=8.2,
        weight="bold",
        color="#6B7280",
        va="center",
    )
    ax.text(0.07, 0.54, value, transform=ax.transAxes, fontsize=18, weight="bold", color="#111827")
    ax.text(
        0.07,
        0.25,
        "\n".join(wrap(note, 35)),
        transform=ax.transAxes,
        fontsize=8.2,
        color="#4B5563",
        va="top",
    )


def _add_explanation_box(
    fig: plt.Figure, xywh: list[float], title: str, bullets: list[str]
) -> None:
    ax = fig.add_axes(xywh)
    ax.axis("off")
    ax.add_patch(
        plt.Rectangle(
            (0, 0), 1, 1, transform=ax.transAxes, facecolor="white", edgecolor="#D8DEE6", lw=1.0
        )
    )
    ax.add_patch(
        plt.Rectangle(
            (0, 0.88),
            1,
            0.12,
            transform=ax.transAxes,
            facecolor="#F9FAFB",
            edgecolor="#D8DEE6",
            lw=0.8,
        )
    )
    ax.text(
        0.045,
        0.94,
        title,
        transform=ax.transAxes,
        fontsize=10.5,
        weight="bold",
        color="#111827",
        va="center",
    )
    y = 0.80
    for bullet in bullets:
        ax.text(
            0.06,
            y,
            "\n".join(wrap(f"- {bullet}", 42)),
            transform=ax.transAxes,
            fontsize=8.5,
            color="#1F2933",
            va="top",
            linespacing=1.25,
        )
        y -= 0.18 + 0.035 * max(0, len(wrap(bullet, 42)) - 2)


def _render_table(
    ax: plt.Axes, data: pd.DataFrame, col_widths: list[float] | None = None, font_size: float = 8.2
) -> None:
    ax.axis("off")
    table = ax.table(
        cellText=data.values,
        colLabels=data.columns,
        loc="center",
        cellLoc="left",
        colLoc="left",
        colWidths=col_widths,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, 1.35)
    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor("#D8DEE6")
        cell.set_linewidth(0.6)
        if row == 0:
            cell.set_text_props(weight="bold", color="white")
            cell.set_facecolor("#111827")
        else:
            cell.set_facecolor("#F8FAFC" if row % 2 == 0 else "white")


def _add_executive_slide(pdf: PdfPages, candidates: pd.DataFrame, references: pd.DataFrame) -> None:
    fig = _new_slide(
        "Executive View: Control Profile, Not Like-for-Like Replacement",
        "The published shortlist applies a light defensive-protection gate to remove pure control profiles with limited ball-winning evidence.",
    )
    top = candidates.iloc[0]
    casemiro_defensive = references.loc[
        references["player"].eq("Casemiro"), "defensive_protection"
    ].iloc[0]
    high_security = candidates[candidates["possession_security"] >= 70]
    high_defence = candidates[
        (candidates["control_midfielder_score"] >= 50)
        & (candidates["defensive_protection"] >= casemiro_defensive)
    ]

    _draw_kpi(
        fig.add_axes([0.055, 0.70, 0.27, 0.15]),
        "Top Weighted Screen",
        top["player"],
        f"{top['squad']} | score {top['control_midfielder_score']:.1f} | age {int(top['age'])}",
        COLOR_PRIMARY,
    )
    _draw_kpi(
        fig.add_axes([0.365, 0.70, 0.27, 0.15]),
        "Published Control Profiles",
        f"{len(high_security)} players",
        "Gated shortlist candidates with possession-security score of 70+; these profiles help avoid repeat emergency defending.",
        COLOR_ACCENT,
    )
    _draw_kpi(
        fig.add_axes([0.675, 0.70, 0.27, 0.15]),
        "Defensive Reference",
        f"{len(high_defence)} players",
        "Priority candidates above Casemiro's defensive-protection reference score.",
        "#0F766E",
    )

    ax_text = fig.add_axes([0.055, 0.255, 0.46, 0.39])
    ax_text.axis("off")
    bullets = [
        "Do not replace Casemiro by only maximizing duels; that risks recreating the original control problem.",
        "The strongest screen is a two-axis fit: secure receiving/circulation plus enough defensive protection to survive transition-heavy games.",
        "Palacios should be read as the strongest possession-control candidate in the screen, not as the strongest like-for-like Casemiro replacement.",
        "Palacios leads the screen subject to availability and injury-history review.",
        "Ugarte is a useful internal reference for defence and security; his low progression score explains why United may still need a complementary controller.",
    ]
    ax_text.text(0, 1, "Key implications", fontsize=13, weight="bold", color="#111827", va="top")
    y = 0.84
    for idx, bullet in enumerate(bullets):
        wrapped = wrap(bullet, 68)
        ax_text.text(
            0.02,
            y,
            f"{idx + 1}. " + "\n   ".join(wrapped),
            fontsize=8.5,
            color="#1F2933",
            va="top",
            linespacing=1.18,
        )
        y -= 0.105 + 0.035 * len(wrapped)

    ax_refs = fig.add_axes([0.55, 0.335, 0.38, 0.23])
    ref_cols = [
        "player",
        "squad",
        "age",
        "defensive_protection",
        "transition_control",
        "possession_security",
        "progressive_value",
    ]
    ref_table = references[ref_cols].copy()
    ref_table["squad"] = ref_table["squad"].replace({"Manchester United": "Man United"})
    ref_table.columns = ["Reference", "Club", "Age", "Def.", "Trans.", "Poss.", "Prog."]
    _render_table(ax_refs, ref_table, [0.19, 0.20, 0.08, 0.10, 0.10, 0.10, 0.10], 7.9)

    _add_explanation_box(
        fig,
        [0.55, 0.19, 0.38, 0.11],
        "Why Ugarte Is In The Report",
        [
            "He is not a target. He anchors the internal comparison: strong defensive/security profile, limited progressive value.",
        ],
    )

    fig.text(0.055, 0.17, "Core line", fontsize=10.5, weight="bold", color=COLOR_PRIMARY)
    fig.text(
        0.055,
        0.13,
        "The next signing should not only win duels. It should prevent some of them from happening.",
        fontsize=15,
        weight="bold",
        color="#111827",
    )
    _save_slide(pdf, fig)


def _add_methodology_slide(pdf: PdfPages) -> None:
    fig = _new_slide(
        "How Players Are Rated",
        "A transparent public-data screen: useful for narrowing video work, not a final recruitment verdict.",
    )
    ax_weights = fig.add_axes([0.065, 0.25, 0.34, 0.54])
    labels = [CATEGORY_LABELS[key] for key in WEIGHTS]
    values = [WEIGHTS[key] * 100 for key in WEIGHTS]
    colors = [COLOR_PRIMARY, COLOR_ACCENT, "#0F766E", "#F59E0B", "#6B7280"]
    ax_weights.barh(labels[::-1], values[::-1], color=colors[::-1])
    ax_weights.set_xlim(0, 35)
    ax_weights.set_xlabel("Weight in total score")
    ax_weights.set_title("Control Midfielder Score weights", fontsize=12, weight="bold")
    for idx, value in enumerate(values[::-1]):
        ax_weights.text(value + 0.7, idx, f"{value:.0f}%", va="center", fontsize=9)

    ax_text = fig.add_axes([0.46, 0.19, 0.45, 0.63])
    ax_text.axis("off")
    sections = [
        (
            "1. Candidate Pool",
            "EPL, La Liga, Primeira Liga, Bundesliga, Ligue 1, and Serie A only. United players are references, not targets. Arsenal, Chelsea, Liverpool, and Manchester City midfielders are excluded. The defensive gate is intentionally low because this is a complementary-control screen, not only a defensive-destroyer screen.",
        ),
        (
            "2. Metric Scoring",
            "Raw public stats are converted to per-90 rates where needed, then normalized to 0-100 percentile-style scores inside this screened pool. A 50 score is roughly middle-of-pool, not an absolute football truth.",
        ),
        (
            "3. Risk Metrics",
            "Fouls, cards, miscontrols, dispossessions, and turnover rates are inverted: lower risk receives the better score.",
        ),
        (
            "4. Data Caveat",
            "StatsBomb open data demonstrates event-data role logic; FBref-style/public aggregate statistics drive the broader screen, with supplements for non-Big-Five leagues such as Portugal.",
        ),
    ]
    y = 0.98
    for header, text in sections:
        ax_text.text(0, y, header, fontsize=10.8, weight="bold", color="#111827", va="top")
        y -= 0.055
        ax_text.text(
            0.02,
            y,
            "\n".join(wrap(text, 88)),
            fontsize=8.8,
            color="#1F2933",
            va="top",
            linespacing=1.28,
        )
        y -= 0.17
    _add_explanation_box(
        fig,
        [0.065, 0.095, 0.84, 0.095],
        "Plain-English Read",
        [
            "The model rewards players who can defend, calm transitions, keep the ball, and still move United up the pitch.",
            "The light defensive gate removes pure control profiles with limited ball-winning evidence while keeping complementary midfielders in the conversation.",
        ],
    )
    _save_slide(pdf, fig)


def _add_ranked_score_slide(pdf: PdfPages, candidates: pd.DataFrame) -> None:
    fig = _new_slide(
        "Shortlist Ranking and Score Drivers",
        "The left chart ranks players; the right chart shows why each score is high.",
    )
    top12 = candidates.head(12).sort_values("control_midfielder_score")
    ax_rank = fig.add_axes([0.06, 0.23, 0.37, 0.58])
    ax_rank.set_facecolor("white")
    ax_rank.barh(top12["player"], top12["control_midfielder_score"], color=COLOR_ACCENT)
    ax_rank.set_xlim(0, 100)
    ax_rank.set_xlabel("Control Midfielder Score")
    ax_rank.set_title("A. Ranked shortlist", fontsize=12, weight="bold")
    for idx, value in enumerate(top12["control_midfielder_score"]):
        ax_rank.text(value + 0.8, idx, f"{value:.1f}", va="center", fontsize=8.2)

    ax_stack = fig.add_axes([0.52, 0.23, 0.38, 0.58])
    ax_stack.set_facecolor("white")
    stack = candidates.head(8).set_index("player")[list(WEIGHTS.keys())]
    weighted = stack.copy()
    for col, weight in WEIGHTS.items():
        weighted[col] = weighted[col] * weight
    weighted.plot(
        kind="barh",
        stacked=True,
        ax=ax_stack,
        color=[COLOR_PRIMARY, COLOR_ACCENT, "#0F766E", "#F59E0B", "#6B7280"],
    )
    ax_stack.invert_yaxis()
    ax_stack.set_xlabel("Weighted score contribution")
    ax_stack.set_ylabel("")
    ax_stack.set_title("B. Score composition, top 8", fontsize=12, weight="bold")
    ax_stack.legend(
        [CATEGORY_LABELS[col] for col in weighted.columns],
        loc="lower right",
        fontsize=7,
        frameon=False,
    )
    _add_explanation_box(
        fig,
        [0.06, 0.095, 0.84, 0.105],
        "How To Read This Exhibit",
        [
            "A high total score is a weighted blend, not a claim that the player is elite at every trait.",
            "Palacios rates highly because security and progression drive the score; Cardoso is the stronger defensive-floor candidate.",
        ],
    )
    _save_slide(pdf, fig)


def _add_control_matrix_slide(
    pdf: PdfPages, candidates: pd.DataFrame, references: pd.DataFrame
) -> None:
    fig = _new_slide(
        "Control Matrix: Who Adds Security Without Losing the Defensive Floor?",
        "Possession security is the control axis; defensive protection is the floor. Bubble size reflects progressive value.",
    )
    ax = fig.add_axes([0.065, 0.17, 0.62, 0.66])
    ax.set_facecolor("white")
    data = candidates.head(16).copy()
    casemiro_defensive = references.loc[
        references["player"].eq("Casemiro"), "defensive_protection"
    ].iloc[0]
    control_line = 70
    ax.axvline(control_line, color="#9CA3AF", lw=1.1, ls="--")
    ax.axhline(casemiro_defensive, color="#9CA3AF", lw=1.1, ls="--")
    ax.fill_between([control_line, 105], casemiro_defensive, 105, color="#DCFCE7", alpha=0.42)
    ax.fill_between([0, control_line], casemiro_defensive, 105, color="#FEF3C7", alpha=0.45)
    ax.fill_between([control_line, 105], 0, casemiro_defensive, color="#DBEAFE", alpha=0.45)
    ax.scatter(
        data["possession_security"],
        data["defensive_protection"],
        s=70 + data["progressive_value"] * 5.3,
        color=COLOR_ACCENT,
        edgecolor="white",
        linewidth=1,
        alpha=0.82,
    )
    for _, row in data.iterrows():
        ha = "right" if row["possession_security"] > 82 else "left"
        xoff = -1.0 if ha == "right" else 0.8
        ax.text(
            row["possession_security"] + xoff,
            row["defensive_protection"] + 0.7,
            row["player"],
            fontsize=8.0,
            ha=ha,
        )

    for _, row in references.iterrows():
        ax.scatter(
            row["possession_security"],
            row["defensive_protection"],
            s=180,
            color=COLOR_PRIMARY,
            marker="D",
            edgecolor="white",
            linewidth=1.2,
        )
        ax.text(
            row["possession_security"] + 1,
            row["defensive_protection"] - 2,
            row["player"],
            fontsize=8.2,
            weight="bold",
            color=COLOR_PRIMARY,
        )

    ax.text(82, 98, "Control target zone", fontsize=10, weight="bold", color="#166534")
    ax.text(
        2, casemiro_defensive + 2.5, "Casemiro defensive reference", fontsize=8.5, color="#4B5563"
    )
    ax.text(5, 98, "Duel-heavy protectors", fontsize=9, color="#92400E")
    ax.text(70, 8, "Controllers needing cover", fontsize=9, color="#1D4ED8")
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 105)
    ax.set_xlabel("Possession security")
    ax.set_ylabel("Defensive protection")
    _add_explanation_box(
        fig,
        [0.72, 0.24, 0.22, 0.47],
        "Scout Read",
        [
            "Top-right is the ideal screen: secure enough to reduce chaos and defensive enough to survive when United lose the ball.",
            "Palacios is far right but not high enough to be a pure defensive successor; Cardoso is the cleanest two-axis fit.",
            "Bubble size indicates progressive value, so bigger bubbles add more forward movement.",
        ],
    )
    _save_slide(pdf, fig)


def _add_heatmap_slide(pdf: PdfPages, category_scores: pd.DataFrame) -> None:
    fig = _new_slide(
        "Category Heatmap: Where Each Candidate Actually Wins",
        f"Candidates shown have cleared the {MIN_DEFENSIVE_PROTECTION_SCORE}+ defensive-protection gate; category scores show the trade-offs.",
    )
    display_cols = list(CATEGORY_LABELS.values())
    heat = category_scores.head(12).set_index("player")[display_cols]
    ax = fig.add_axes([0.06, 0.18, 0.63, 0.66])
    sns.heatmap(
        heat,
        ax=ax,
        cmap="RdYlGn",
        vmin=0,
        vmax=100,
        annot=True,
        fmt=".0f",
        linewidths=0.4,
        linecolor="white",
        cbar_kws={"label": "Category score"},
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    _add_explanation_box(
        fig,
        [0.73, 0.25, 0.22, 0.42],
        "Fan-Friendly Translation",
        [
            "Green means the player is strong relative to this public-data pool; red means that category is a risk.",
            "The best United fit is not necessarily the greenest row. It is the row whose weaknesses United can live with tactically.",
            "Use this slide to decide what video questions to ask next.",
        ],
    )
    _save_slide(pdf, fig)


def _add_sensitivity_slide(
    pdf: PdfPages, candidates: pd.DataFrame, sensitivity: pd.DataFrame
) -> None:
    fig = _new_slide(
        "Sensitivity and Availability View",
        "A better shortlist is robust to reasonable weight changes and honest about cost/minutes context.",
    )
    stability = (
        sensitivity.groupby("player")["rank"]
        .agg(best_rank="min", worst_rank="max")
        .assign(rank_range=lambda df: df["worst_rank"] - df["best_rank"])
        .reset_index()
        .merge(
            candidates[
                ["player", "control_midfielder_score", "age", "minutes", "market_value_m_eur"]
            ],
            on="player",
            how="left",
        )
        .sort_values(["best_rank", "rank_range"])
        .head(12)
    )

    ax1 = fig.add_axes([0.06, 0.25, 0.34, 0.55])
    ax1.set_facecolor("white")
    plot_df = stability.sort_values("best_rank", ascending=False)
    ax1.hlines(
        plot_df["player"], plot_df["best_rank"], plot_df["worst_rank"], color="#9CA3AF", lw=5
    )
    ax1.scatter(plot_df["best_rank"], plot_df["player"], color="#0F766E", s=55, label="Best")
    ax1.scatter(plot_df["worst_rank"], plot_df["player"], color=COLOR_PRIMARY, s=55, label="Worst")
    ax1.set_xlabel("Rank across weight scenarios")
    ax1.set_title("A. Rank stability range", fontsize=12, weight="bold")
    ax1.invert_xaxis()
    ax1.legend(frameon=False, fontsize=8)

    ax2 = fig.add_axes([0.48, 0.25, 0.31, 0.55])
    ax2.set_facecolor("white")
    sizes = 60 + (stability["minutes"] / stability["minutes"].max()) * 520
    ax2.scatter(
        stability["age"],
        stability["market_value_m_eur"],
        s=sizes,
        color=COLOR_ACCENT,
        alpha=0.75,
        edgecolor="white",
        linewidth=1,
    )
    for _, row in stability.iterrows():
        ax2.text(row["age"] + 0.12, row["market_value_m_eur"] + 0.6, row["player"], fontsize=7.8)
    ax2.axvspan(21, 27, color="#DCFCE7", alpha=0.35)
    ax2.set_xlabel("Age as of May 6, 2026")
    ax2.set_ylabel("Manual market value proxy, EURm")
    ax2.set_title("B. Age / value / minutes proxy", fontsize=12, weight="bold")
    _add_explanation_box(
        fig,
        [0.82, 0.28, 0.15, 0.44],
        "Why It Matters",
        [
            "If a candidate jumps around when weights move, the recommendation is fragile.",
            "Age, minutes, and value are not scouting metrics; they are practical filters for recruitment realism.",
            "This is where football fit meets squad-building cost.",
        ],
    )
    _save_slide(pdf, fig)


def _add_candidate_notes_slide(pdf: PdfPages, shortlist: pd.DataFrame) -> None:
    fig = _new_slide(
        "Recruitment Read-Out",
        "Interpretation layer: what the shortlist suggests United should review next.",
    )
    table = shortlist.head(10)[
        [
            "rank",
            "player",
            "squad",
            "age",
            "control_midfielder_score",
            "defensive_protection",
            "possession_security",
            "progressive_value",
            "availability_note",
        ]
    ].copy()
    table.columns = [
        "#",
        "Player",
        "Club",
        "Age",
        "Score",
        "Def.",
        "Poss.",
        "Prog.",
        "Analyst note",
    ]
    table["Analyst note"] = table["Analyst note"].apply(
        lambda value: "\n".join(wrap(str(value), 34))
    )
    ax = fig.add_axes([0.04, 0.17, 0.92, 0.68])
    _render_table(ax, table, [0.04, 0.14, 0.15, 0.05, 0.07, 0.06, 0.06, 0.06, 0.31], 7.3)
    fig.text(
        0.055,
        0.095,
        "Recommended next step: run video review on the top two archetypes: (1) high-control circulators who prevent pressure, and (2) defensive-floor anchors who can survive United's transition volume.",
        fontsize=9.2,
        color="#111827",
        weight="bold",
    )
    _save_slide(pdf, fig)


def main() -> None:
    """CLI entry point."""

    outputs = generate_outputs()
    print("Generated Casemiro Replacement Profile outputs:")
    for name, path in outputs.items():
        print(f"- {name}: {path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
