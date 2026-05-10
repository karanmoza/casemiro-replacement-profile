"""Run the end-to-end project and generate portfolio outputs."""

from __future__ import annotations

from html import escape
from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from .config import (
    CATEGORY_LABELS,
    CATEGORY_METRICS,
    CATEGORY_WEIGHTS,
    CHART_DIR,
    DATA_OUTPUT_DIR,
    METRIC_GROUPS,
    MIN_DEFENSIVE_PROTECTION_SCORE,
    OUTPUT_DIR,
    PROCESSED_DIR,
    REPORT_DIR,
)
from .load_fbref import PLAYER_CONTEXT_MAY_2026, load_fbref_player_stats, write_sample_dataset
from .load_statsbomb import engineer_event_control_metrics, load_statsbomb_events
from .scoring import (
    build_scoring_table,
    filter_target_candidates,
    make_category_scores,
    make_filtered_out_watchlist,
    make_metric_dictionary,
    make_player_score_explanation,
    make_shortlist,
    run_sensitivity_analysis,
    split_watchlists,
)
from .visualisations import (
    COLOR_GRAY,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    save_archetype_summary,
    save_category_heatmap,
    save_defensive_gate_diagnostic,
    save_possession_security_breakdown,
    save_progression_type_chart,
    save_radar_chart,
    save_ranked_score_bar,
    save_security_defence_scatter,
    save_sensitivity_chart,
    save_sensitivity_rank_stability,
    save_transition_chaos_map,
)


def ensure_directories() -> None:
    """Create project output directories."""

    for path in [PROCESSED_DIR, DATA_OUTPUT_DIR, OUTPUT_DIR, REPORT_DIR, CHART_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def generate_outputs(input_csv: str | Path | None = None) -> dict[str, Path]:
    """Run data loading, scoring, visualization, reports, and validation-ready exports."""

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
    watchlist = make_filtered_out_watchlist(scored)
    borderline_watchlist, role_mismatch_watchlist = split_watchlists(watchlist)
    score_explanation = make_player_score_explanation(scored)
    sensitivity = run_sensitivity_analysis(scored)
    metric_dictionary = make_metric_dictionary(scored)

    paths = {
        "scored_players": PROCESSED_DIR / "scored_players.csv",
        "candidate_shortlist": OUTPUT_DIR / "candidate_shortlist.csv",
        "category_scores": OUTPUT_DIR / "category_scores.csv",
        "watchlist_removed_by_gate": OUTPUT_DIR / "watchlist_removed_by_gate.csv",
        "borderline_watchlist": OUTPUT_DIR / "borderline_watchlist.csv",
        "role_mismatch_watchlist": OUTPUT_DIR / "role_mismatch_watchlist.csv",
        "filtered_out_watchlist": OUTPUT_DIR / "filtered_out_watchlist.csv",
        "player_score_explanation": OUTPUT_DIR / "player_score_explanation.csv",
        "metric_dictionary": OUTPUT_DIR / "metric_dictionary.csv",
        "sensitivity_analysis": OUTPUT_DIR / "sensitivity_analysis.csv",
        "player_context_sources": OUTPUT_DIR / "player_context_sources.csv",
        "scoring_methodology": OUTPUT_DIR / "scoring_methodology.csv",
    }

    scored.to_csv(paths["scored_players"], index=False)
    shortlist.to_csv(paths["candidate_shortlist"], index=False)
    category_scores.to_csv(paths["category_scores"], index=False)
    watchlist.to_csv(paths["watchlist_removed_by_gate"], index=False)
    borderline_watchlist.to_csv(paths["borderline_watchlist"], index=False)
    role_mismatch_watchlist.to_csv(paths["role_mismatch_watchlist"], index=False)
    watchlist.to_csv(paths["filtered_out_watchlist"], index=False)
    score_explanation.to_csv(paths["player_score_explanation"], index=False)
    metric_dictionary.to_csv(paths["metric_dictionary"], index=False)
    sensitivity.to_csv(paths["sensitivity_analysis"], index=False)
    _make_context_sources().to_csv(paths["player_context_sources"], index=False)
    _make_scoring_methodology_table(metric_dictionary).to_csv(
        paths["scoring_methodology"], index=False
    )

    chart_paths = {
        "ranked_bar": save_ranked_score_bar(
            shortlist, CHART_DIR / "ranked_control_midfielder_score.png"
        ),
        "control_matrix": save_security_defence_scatter(
            scored, CHART_DIR / "security_vs_defensive_floor.png"
        ),
        "category_heatmap": save_category_heatmap(
            category_scores, CHART_DIR / "category_heatmap.png"
        ),
        "radar": save_radar_chart(scored, CHART_DIR / "casemiro_candidate_radar.png"),
        "defensive_gate": save_defensive_gate_diagnostic(
            scored, CHART_DIR / "defensive_gate_diagnostic.png"
        ),
        "possession_breakdown": save_possession_security_breakdown(
            scored, CHART_DIR / "possession_security_breakdown.png"
        ),
        "transition_map": save_transition_chaos_map(scored, CHART_DIR / "transition_chaos_map.png"),
        "progression_type": save_progression_type_chart(
            scored, CHART_DIR / "progression_type_chart.png"
        ),
        "sensitivity_heatmap": save_sensitivity_chart(
            sensitivity, CHART_DIR / "sensitivity_analysis.png"
        ),
        "sensitivity_stability": save_sensitivity_rank_stability(
            sensitivity, CHART_DIR / "sensitivity_rank_stability.png"
        ),
        "archetype_summary": save_archetype_summary(
            score_explanation, CHART_DIR / "archetype_summary.png"
        ),
    }

    html_path = REPORT_DIR / "casemiro_replacement_report.html"
    pdf_path = REPORT_DIR / "casemiro_replacement_report.pdf"
    summary_pdf_path = REPORT_DIR / "casemiro_replacement_summary.pdf"
    save_html_report(
        scored=scored,
        shortlist=shortlist,
        category_scores=category_scores,
        watchlist=watchlist,
        borderline_watchlist=borderline_watchlist,
        role_mismatch_watchlist=role_mismatch_watchlist,
        score_explanation=score_explanation,
        sensitivity=sensitivity,
        metric_dictionary=metric_dictionary,
        chart_paths=chart_paths,
        path=html_path,
    )
    save_pdf_report(
        scored=scored,
        shortlist=shortlist,
        watchlist=watchlist,
        borderline_watchlist=borderline_watchlist,
        role_mismatch_watchlist=role_mismatch_watchlist,
        score_explanation=score_explanation,
        sensitivity=sensitivity,
        chart_paths=chart_paths,
        path=pdf_path,
    )
    save_pdf_report(
        scored=scored,
        shortlist=shortlist,
        watchlist=watchlist,
        borderline_watchlist=borderline_watchlist,
        role_mismatch_watchlist=role_mismatch_watchlist,
        score_explanation=score_explanation,
        sensitivity=sensitivity,
        chart_paths=chart_paths,
        path=summary_pdf_path,
    )

    return {
        **paths,
        "html_report": html_path,
        "report_pdf": pdf_path,
        "summary_pdf": summary_pdf_path,
        **chart_paths,
    }


def _make_context_sources() -> pd.DataFrame:
    context_sources = (
        pd.DataFrame.from_dict(PLAYER_CONTEXT_MAY_2026, orient="index")
        .reset_index()
        .rename(columns={"index": "player"})
    )
    if "is_target_candidate" in context_sources.columns:
        context_sources["is_target_candidate"] = context_sources["is_target_candidate"].where(
            context_sources["is_target_candidate"].notna(), True
        )
    return context_sources


def _make_scoring_methodology_table(metric_dictionary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for category, weight in CATEGORY_WEIGHTS.items():
        metrics = metric_dictionary.loc[metric_dictionary["category"].eq(category), "input_metric"]
        rows.append(
            {
                "category": category,
                "category_label": CATEGORY_LABELS[category],
                "weight": weight,
                "input_metrics": ", ".join(metrics),
                "score_calculation": "Average of available input-metric percentile scores",
            }
        )
    return pd.DataFrame(rows)


def rel_path(path: str | Path, start: str | Path) -> str:
    return Path(path).resolve().relative_to(Path(start).resolve()).as_posix()


def table_html(df: pd.DataFrame, max_rows: int | None = None) -> str:
    display = df.copy()
    display.columns.name = None
    display.index.name = None
    if max_rows is not None:
        display = display.head(max_rows)
    for col in display.select_dtypes(include="number").columns:
        display[col] = display[col].round(2)
    return display.to_html(index=False, escape=True, classes="data-table")


def metrics_table_for_html(metric_dictionary: pd.DataFrame) -> pd.DataFrame:
    """Return an explicit metric dictionary table for report readers."""

    display = metric_dictionary.copy()
    display["Category"] = display["category"].map(CATEGORY_LABELS)
    display["Input metric"] = display["input_metric"].str.replace("_", " ").str.title()
    display["Raw column"] = display["raw_column_used"].replace("", "Unavailable / skipped")
    display["Direction"] = display["higher_is_better"].map(
        {
            True: "Positive input: higher raw value scores better",
            False: "Inverted input: lower raw value scores better",
        }
    )
    display["Transformation"] = display["transformation"]
    display["Football meaning"] = display["explanation"]
    display["Caveat"] = display["caveat"].fillna("")
    return display[
        [
            "Category",
            "Input metric",
            "Raw column",
            "Direction",
            "Transformation",
            "Football meaning",
            "Caveat",
        ]
    ]


def save_html_report(
    scored: pd.DataFrame,
    shortlist: pd.DataFrame,
    category_scores: pd.DataFrame,
    watchlist: pd.DataFrame,
    borderline_watchlist: pd.DataFrame,
    role_mismatch_watchlist: pd.DataFrame,
    score_explanation: pd.DataFrame,
    sensitivity: pd.DataFrame,
    metric_dictionary: pd.DataFrame,
    chart_paths: dict[str, Path],
    path: str | Path,
) -> Path:
    """Create the expanded explainability-first static HTML report."""

    path = Path(path)
    candidates = filter_target_candidates(scored)
    top = candidates.iloc[0]
    cardoso = scored.loc[scored["player"].eq("Johnny Cardoso")].iloc[0]
    casemiro = scored.loc[scored["player"].eq("Casemiro")].iloc[0]
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
            "gate_margin",
        ]
    ].rename(
        columns={
            "rank": "#",
            "player": "Player",
            "squad": "Club",
            "league": "League",
            "age": "Age",
            "control_midfielder_score": "Score",
            "defensive_protection": "Defence",
            "transition_control": "Transition",
            "possession_security": "Security",
            "progressive_value": "Progression",
            "age_availability": "Age / availability",
            "gate_margin": "Gate margin",
        }
    )
    explanation_table = (
        score_explanation[
            [
                "player",
                "club",
                "final_score",
                "archetype_label",
                "strongest_football_category",
                "weakest_football_category",
                "gate_margin",
                "analyst_note",
            ]
        ]
        .rename(
            columns={
                "player": "Player",
                "club": "Club",
                "final_score": "Score",
                "archetype_label": "Archetype",
                "strongest_football_category": "Strongest football category",
                "weakest_football_category": "Weakest football category",
                "gate_margin": "Gate margin",
                "analyst_note": "Analyst note",
            }
        )
        .head(12)
    )

    def make_watchlist_table(source: pd.DataFrame) -> pd.DataFrame:
        if source.empty:
            return pd.DataFrame(
                columns=[
                    "Player",
                    "Club",
                    "Score",
                    "Defence",
                    "Security",
                    "Progression",
                    "Gate margin",
                    "Context note",
                ]
            )
        return source[
            [
                "player",
                "squad",
                "control_midfielder_score",
                "defensive_protection",
                "possession_security",
                "progressive_value",
                "gate_margin",
                "availability_note",
            ]
        ].rename(
            columns={
                "player": "Player",
                "squad": "Club",
                "control_midfielder_score": "Score",
                "defensive_protection": "Defence",
                "possession_security": "Security",
                "progressive_value": "Progression",
                "gate_margin": "Gate margin",
                "availability_note": "Context note",
            }
        )

    borderline_watchlist_table = make_watchlist_table(borderline_watchlist)
    role_mismatch_watchlist_table = make_watchlist_table(role_mismatch_watchlist)
    sensitivity_table = (
        sensitivity[
            [
                "player",
                "rank_base",
                "rank_defensive_heavy",
                "rank_possession_heavy",
                "rank_transition_heavy",
                "rank_progression_heavy",
                "rank_equal_weight",
                "average_rank",
                "rank_range",
                "rank_volatility_score",
            ]
        ]
        .rename(
            columns={
                "player": "Player",
                "rank_base": "Base",
                "rank_defensive_heavy": "Def-heavy",
                "rank_possession_heavy": "Poss-heavy",
                "rank_transition_heavy": "Trans-heavy",
                "rank_progression_heavy": "Prog-heavy",
                "rank_equal_weight": "Equal football",
                "average_rank": "Average rank",
                "rank_range": "Rank range",
                "rank_volatility_score": "Rank volatility (lower = stabler)",
            }
        )
        .head(12)
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Casemiro Replacement Profile</title>
  <style>
    :root {{
      --ink: #111827;
      --muted: #5b6573;
      --line: #d9dee5;
      --bg: #f5f1eb;
      --panel: #ffffff;
      --red: #9f1d20;
      --navy: #16324f;
      --green: #2e8b57;
      --gold: #b88a1b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      line-height: 1.48;
    }}
    .hero {{
      background: var(--navy);
      color: white;
      padding: 44px 7vw 38px;
      border-left: 12px solid var(--red);
    }}
    .eyebrow {{
      color: #cfd6e1;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
      font-weight: 800;
    }}
    h1 {{ margin: 10px 0 12px; font-size: clamp(34px, 5vw, 58px); line-height: 1.02; }}
    .hero p {{ max-width: 980px; margin: 0; font-size: 18px; color: #eef2f6; }}
    main {{ padding: 28px 7vw 64px; }}
    section {{ margin: 26px 0; background: var(--panel); border: 1px solid var(--line); }}
    .section-head {{ padding: 24px 26px 10px; border-bottom: 1px solid #edf0f5; }}
    h2 {{ margin: 0 0 8px; font-size: 26px; }}
    h3 {{ margin: 0 0 10px; font-size: 18px; }}
    .section-head p {{ margin: 0 0 12px; color: var(--muted); max-width: 980px; }}
    .grid-3, .grid-2 {{ display: grid; gap: 18px; padding: 24px 26px; }}
    .grid-3 {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .grid-2 {{ grid-template-columns: minmax(0, 1.1fr) minmax(320px, .9fr); }}
    .card {{ border: 1px solid var(--line); padding: 18px; background: #fff; }}
    .kpi {{ border-left: 6px solid var(--navy); min-height: 148px; }}
    .kpi.red {{ border-left-color: var(--red); }}
    .kpi.green {{ border-left-color: var(--green); }}
    .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; font-weight: 800; }}
    .value {{ margin-top: 8px; font-size: 28px; font-weight: 800; }}
    .note {{ color: var(--muted); margin-top: 10px; font-size: 14px; }}
    .copy {{ padding: 24px 26px; max-width: 1120px; }}
    .copy p {{ margin-top: 0; }}
    .callout {{ margin: 0 26px 24px; padding: 18px 20px; background: #fff7ed; border-left: 6px solid var(--gold); }}
    .chart-card {{ padding: 16px 26px 24px; }}
    img.chart {{ width: 100%; max-width: 1180px; height: auto; display: block; background: white; }}
    .data-table {{ width: 100%; border-collapse: collapse; font-size: 13px; table-layout: fixed; }}
    .data-table th {{ background: var(--navy); color: white; text-align: left; padding: 9px; }}
    .data-table td {{ border-bottom: 1px solid var(--line); padding: 8px; vertical-align: top; overflow-wrap: anywhere; }}
    .data-table tr:nth-child(even) td {{ background: #f8fafc; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 8px; }}
    footer {{ padding: 24px 7vw 42px; color: var(--muted); font-size: 13px; }}
    @media (max-width: 900px) {{ .grid-3, .grid-2 {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header class="hero">
    <div class="eyebrow">Manchester United public-data recruitment screen</div>
    <h1>Casemiro Replacement Profile</h1>
    <p><strong>The next signing should not only win duels. It should prevent some of them from happening.</strong><br>
    This is a public-data recruitment framework, not proprietary scouting data or a signing verdict.</p>
  </header>
  <main>
    <section>
      <div class="section-head">
        <h2>Executive View</h2>
        <p>Palacios is the strongest possession-control candidate in the screen, not the strongest like-for-like Casemiro replacement. Cardoso is the cleaner two-axis defensive/security fit.</p>
      </div>
      <div class="grid-3">
        <div class="card kpi red"><div class="label">Top weighted screen</div><div class="value">{escape(top['player'])}</div><div class="note">Score {top['control_midfielder_score']:.1f}. Leads through control and progression, subject to defensive translation and availability review.</div></div>
        <div class="card kpi green"><div class="label">Two-axis fit</div><div class="value">Johnny Cardoso</div><div class="note">Defence {cardoso['defensive_protection']:.1f}, possession {cardoso['possession_security']:.1f}. More balanced defensive/security profile.</div></div>
        <div class="card kpi"><div class="label">Defensive reference</div><div class="value">{casemiro['defensive_protection']:.1f}</div><div class="note">Casemiro is a defensive responsibility reference, not the clone target.</div></div>
      </div>
      <div class="callout"><strong>Interpretation:</strong> The model starts the scouting conversation. It does not replace video, medical review, contract work, fee analysis, or tactical role evaluation.</div>
    </section>

    <section>
      <div class="section-head"><h2>What This Model Is — and Is Not</h2></div>
      <div class="copy">
        <p>This is a recruitment screen, not a signing verdict. It converts United's abstract need for midfield control into a transparent, auditable public-data framework.</p>
        <p>It is designed to focus scouting/video discussion. It does not replace club scouting, medical review, contract work, fee analysis, or tactical video.</p>
      </div>
    </section>

    <section>
      <div class="section-head"><h2>How the Score Works</h2></div>
      <div class="copy">
        <p><strong>Formula:</strong> 30% defensive protection + 25% transition control + 25% possession security + 15% progressive value + 5% age / availability.</p>
        <p>Each input metric is first converted into a comparable rate, percentage, or per-touch measure. It is then normalized into a 0-100 percentile-style score within the screened player pool. For negative events such as fouls, cards, miscontrols, dispossessions, and turnover rate, the score is inverted so that safer players receive higher values. Category scores are calculated as the average of available input-metric scores. The final Control Midfielder Score is a weighted average of the five category scores.</p>
        <p>A 100 means the player is at the top of this public screened pool for that metric or category. It does not mean perfect football ability.</p>
      </div>
    </section>

    <section>
      <div class="section-head"><h2>Why These Weights?</h2></div>
      <div class="copy">
        <p>The weighting scheme reflects Manchester United's specific midfield-control problem. This is not a search for the best pure ball-winner. It is a search for a midfielder who can preserve enough defensive protection while improving control.</p>
        <ul>
          <li><strong>Defensive protection receives 30%</strong>, the highest single weight, because any Casemiro replacement profile must still protect the back line, defend central spaces, and survive defensive responsibility.</li>
          <li><strong>Transition control receives 25%</strong> because United's issue is not only settled defending; it is also the number of chaotic moments created after possession breaks.</li>
          <li><strong>Possession security receives 25%</strong> because the deeper thesis is that United need control. A midfielder who loses possession too often will recreate the same emergency-defending problem even if he wins duels.</li>
          <li><strong>Progressive value receives 15%</strong> because United still need the player to move the ball forward, but this role should not become a pure creator search.</li>
          <li><strong>Age / availability receives 5%</strong> because practical squad-building context matters, but it should not overpower the football profile.</li>
        </ul>
        <p>The weighting scheme is designed to reward midfielders who can defend first, stabilize transitions second, secure possession third, and progress the ball without turning the role into a high-risk creator profile.</p>
        <p>These weights are subjective but transparent. That is why the report includes sensitivity analysis to test whether the shortlist collapses when reasonable weighting assumptions change.</p>
      </div>
    </section>

    <section>
      <div class="section-head"><h2>Why Use a Defensive Gate?</h2></div>
      <div class="copy">
        <p>A weight ranks players. A gate enforces a minimum requirement.</p>
        <p>Even though defensive protection has the highest single weight, a player can still score highly overall if he is elite in possession security and progression. For a Casemiro replacement profile, that creates a risk: the model could surface elegant possession players who do not have enough defensive evidence to survive United's midfield environment.</p>
        <p>The defensive gate should be read as a minimum-evidence filter, not as a final judgment on defensive ability. Palacios clears the defensive gate narrowly, so he should not be treated as a pure defensive replacement. Elliot Anderson falls just below the gate, so he should remain a watchlist player rather than be treated as definitively rejected.</p>
        <p>This is why the report separates the published shortlist, borderline watchlist, and role-mismatch watchlist rather than deleting below-gate players entirely. Borderline differences around the gate should be tested with video, tactical role context, league translation, and team style.</p>
      </div>
    </section>

    <section>
      <div class="section-head"><h2>From Input Metrics to Category Scores</h2></div>
      <div class="copy">
        <p>Positive inputs reward higher raw values. Inverted inputs reward lower raw values, which matters for events like fouls, cards, miscontrols, dispossessions, and turnover rate. The table below shows the exact raw column, direction, and transformation used for every configured input.</p>
        {table_html(metrics_table_for_html(metric_dictionary))}
      </div>
    </section>

    <section>
      <div class="section-head"><h2>Ranked Published Shortlist</h2><p>The final score uses all five categories.</p></div>
      <div class="chart-card"><img class="chart" src="{chart_rel['ranked_bar']}" alt="Ranked shortlist"></div>
      <div class="copy">{table_html(shortlist_table)}</div>
    </section>

    <section>
      <div class="section-head"><h2>Control Matrix</h2><p>Who adds possession security without losing the defensive floor?</p></div>
      <div class="chart-card"><img class="chart" src="{chart_rel['control_matrix']}" alt="Control matrix"></div>
    </section>

    <section>
      <div class="section-head"><h2>Defensive Gate Diagnostic</h2></div>
      <div class="copy"><p>The gate is useful as a screen, but the Palacios-Anderson gap shows why borderline cases should not be treated as definitive scouting judgments.</p></div>
      <div class="chart-card"><img class="chart" src="{chart_rel['defensive_gate']}" alt="Defensive gate diagnostic"></div>
    </section>

    <section>
      <div class="section-head"><h2>Possession Security Breakdown</h2></div>
      <div class="copy"><p>This plot separates players who simply pass safely from players who are actively available, involved, and secure under volume.</p></div>
      <div class="chart-card"><img class="chart" src="{chart_rel['possession_breakdown']}" alt="Possession security breakdown"></div>
    </section>

    <section>
      <div class="section-head"><h2>Transition Chaos Map</h2></div>
      <div class="copy"><p>United's issue is not only ball-winning. It is the number of unstable moments after possession breaks. This chart highlights players who regain or stabilize play without creating new problems.</p></div>
      <div class="chart-card"><img class="chart" src="{chart_rel['transition_map']}" alt="Transition chaos map"></div>
    </section>

    <section>
      <div class="section-head"><h2>Progression Type</h2></div>
      <div class="copy"><p>Progression is not one skill. Some midfielders move the ball through passing, others through carrying. United should know which type they are buying.</p></div>
      <div class="chart-card"><img class="chart" src="{chart_rel['progression_type']}" alt="Progression type chart"></div>
    </section>

    <section>
      <div class="section-head"><h2>Reference Profiles: Casemiro and Ugarte</h2></div>
      <div class="copy"><p>Casemiro and Ugarte are reference players, not targets in this screen. Casemiro is an ageing defensive responsibility reference, not the clone target. Ugarte already covers much of the defence/security base, but his low progression score suggests United may still need a complementary midfielder who can add control without limiting progression.</p></div>
      <div class="chart-card"><img class="chart" src="{chart_rel['radar']}" alt="Radar comparison"></div>
    </section>

    <section>
      <div class="section-head"><h2>Sensitivity and Practicality</h2></div>
      <div class="copy">
        <p>Sensitivity analysis tests whether the shortlist depends too heavily on one subjective weighting choice. A robust candidate remains near the top under several reasonable versions of the model. A fragile candidate ranks highly only when the model favors one specific trait.</p>
        <p>Sensitivity analysis is used because the category weights are transparent but still subjective. If a candidate only ranks well under one weighting scheme, the model is telling us that the recommendation is fragile. If a candidate stays high across multiple schemes, the player is a more robust scouting priority.</p>
        <p>Lower rank volatility means the player's rank is more stable across weighting scenarios. Average rank should be read alongside volatility, because a player can be stable but still consistently lower-ranked.</p>
        <p>If Palacios drops in defensive-heavy scenarios, that confirms he is a control candidate whose defensive translation needs review. If Cardoso stays high across base, defensive-heavy, and possession-heavy scenarios, that supports his two-axis fit. If a player rises only in progression-heavy scenarios, he may be more of a progression specialist than a Casemiro replacement profile. If a player ranks well defensively but poorly in possession-heavy scenarios, he may recreate the original control problem.</p>
      </div>
      <div class="chart-card"><img class="chart" src="{chart_rel['sensitivity_stability']}" alt="Sensitivity rank volatility"></div>
      <div class="copy">{table_html(sensitivity_table)}</div>
    </section>

    <section>
      <div class="section-head"><h2>Archetype Summary</h2><p>The model gives the answer. The diagnostic charts explain the answer.</p></div>
      <div class="chart-card"><img class="chart" src="{chart_rel['archetype_summary']}" alt="Archetype summary"></div>
      <div class="copy">{table_html(explanation_table, max_rows=12)}</div>
    </section>

    <section>
      <div class="section-head"><h2>Borderline Watchlist</h2></div>
      <div class="copy">
        <p>These players sit within five points below the defensive gate. They are not rejected; they are the names where video, tactical role context, and league translation matter most.</p>
        {table_html(borderline_watchlist_table)}
      </div>
    </section>

    <section>
      <div class="section-head"><h2>Role-Mismatch Watchlist</h2></div>
      <div class="copy">
        <p>These players remain analytically interesting, but their public-data defensive evidence sits further away from the minimum-evidence filter for this role profile. They may be better fits for different midfield briefs.</p>
        {table_html(role_mismatch_watchlist_table)}
      </div>
    </section>

    <section>
      <div class="section-head"><h2>Limitations</h2></div>
      <div class="copy">
        <ul>
          <li>Public data cannot replace club scouting.</li>
          <li>Aggregate stats lose role, possession, pressure, and team-context detail.</li>
          <li>StatsBomb open data is limited to selected competitions.</li>
          <li>Public statsbombpy access should not be treated as full 360 data access.</li>
          <li>League strength and team style affect metrics.</li>
          <li>Injury history and transfer feasibility require separate work.</li>
          <li>The defensive gate is a screen, not a verdict.</li>
        </ul>
      </div>
    </section>

    <section>
      <div class="section-head"><h2>What the Screen Actually Suggests</h2></div>
      <div class="copy">
        <p>The screen does not produce one obvious answer. It produces three useful archetypes. Palacios is the control/progression leader but needs defensive translation and availability review. Cardoso is the cleaner two-axis defensive/security fit. Hjulmand, Florentino Luís, and Wieffer preserve more defensive floor but raise different possession or progression questions.</p>
        <p>That is the value of the model: it narrows the next scouting conversation rather than pretending to finish it.</p>
      </div>
    </section>

    <section>
      <div class="section-head"><h2>Recommended Next Scouting Questions</h2></div>
      <div class="copy">
        <ul>
          <li><strong>Palacios:</strong> Can his defensive work translate to United's transition-heavy environment? Is his availability/injury history acceptable? Does he receive under pressure in central zones or mainly in cleaner structures?</li>
          <li><strong>Cardoso:</strong> Does his defensive range hold against Premier League tempo? Can he progress play enough to avoid becoming too conservative?</li>
          <li><strong>Hjulmand:</strong> Is he clean enough under pressure to solve United's control issue?</li>
          <li><strong>Florentino Luís:</strong> Is the possession limitation too severe for a control brief?</li>
          <li><strong>Wieffer:</strong> Does he offer enough mobility and transition coverage?</li>
        </ul>
      </div>
    </section>
  </main>
  <footer>Built with pandas, matplotlib, public aggregate player statistics, and StatsBomb open-data concepts for event-data role design. This is a screening framework, not a final recruitment decision model.</footer>
</body>
</html>"""

    path.write_text(html, encoding="utf-8")
    return path


def _pdf_text_page(
    pdf: PdfPages, title: str, paragraphs: list[str], bullets: list[str] | None = None
) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.08, 0.08, 0.84, 0.84])
    ax.axis("off")
    fig.text(0.08, 0.94, title, fontsize=21, weight="bold", color=COLOR_SECONDARY)
    y = 0.88
    for paragraph in paragraphs:
        wrapped = fill(paragraph, width=92)
        ax.text(0, y, wrapped, fontsize=10.5, color="#111827", va="top", linespacing=1.35)
        y -= 0.055 * (wrapped.count("\n") + 1) + 0.018
    if bullets:
        for bullet in bullets:
            wrapped = fill(f"- {bullet}", width=88)
            ax.text(0.02, y, wrapped, fontsize=10, color="#111827", va="top", linespacing=1.35)
            y -= 0.045 * (wrapped.count("\n") + 1) + 0.012
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _pdf_chart_page(pdf: PdfPages, title: str, chart_path: Path, note: str) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    fig.text(0.05, 0.94, title, fontsize=19, weight="bold", color=COLOR_SECONDARY)
    fig.text(0.05, 0.89, fill(note, width=130), fontsize=10, color=COLOR_GRAY)
    image = plt.imread(chart_path)
    ax = fig.add_axes([0.05, 0.06, 0.9, 0.78])
    ax.imshow(image)
    ax.axis("off")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _pdf_table_page(pdf: PdfPages, title: str, df: pd.DataFrame, note: str) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.04, 0.05, 0.92, 0.78])
    ax.axis("off")
    fig.text(0.04, 0.94, title, fontsize=19, weight="bold", color=COLOR_SECONDARY)
    fig.text(0.04, 0.89, fill(note, width=135), fontsize=10, color=COLOR_GRAY)
    display = df.copy()
    for col in display.select_dtypes(include="number").columns:
        display[col] = display[col].round(1)
    table = ax.table(
        cellText=display.values,
        colLabels=display.columns,
        loc="center",
        cellLoc="left",
        colLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.2)
    table.scale(1, 1.28)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("white")
        if row == 0:
            cell.set_facecolor(COLOR_SECONDARY)
            cell.get_text().set_color("white")
            cell.get_text().set_weight("bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f8fafc")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def save_pdf_report(
    scored: pd.DataFrame,
    shortlist: pd.DataFrame,
    watchlist: pd.DataFrame,
    borderline_watchlist: pd.DataFrame,
    role_mismatch_watchlist: pd.DataFrame,
    score_explanation: pd.DataFrame,
    sensitivity: pd.DataFrame,
    chart_paths: dict[str, Path],
    path: str | Path,
) -> Path:
    """Create a PDF report with constrained charts and non-overflowing tables."""

    path = Path(path)
    with PdfPages(path) as pdf:
        _pdf_text_page(
            pdf,
            "Casemiro Replacement Profile",
            [
                "The next signing should not only win duels. It should prevent some of them from happening.",
                "This is a public-data recruitment screen for Manchester United's midfield-control problem. It is not proprietary scouting data and it is not a signing verdict.",
                "Palacios leads the weighted screen as a possession-control candidate. Cardoso is the cleaner two-axis defensive/security fit. Borderline names should be reviewed through video, tactical role context, league translation, and availability work.",
            ],
        )
        _pdf_chart_page(
            pdf,
            "Ranked Published Shortlist",
            chart_paths["ranked_bar"],
            "The bar length is the final weighted score, not a direct scouting grade.",
        )
        _pdf_chart_page(
            pdf,
            "Control Matrix",
            chart_paths["control_matrix"],
            "This shows the main trade-off: who adds possession security without losing the minimum defensive base?",
        )
        _pdf_chart_page(
            pdf,
            "Defensive Gate Diagnostic",
            chart_paths["defensive_gate"],
            "The Palacios-Anderson gap is narrow enough that borderline cases should be video-tested rather than treated as definitive.",
        )
        _pdf_chart_page(
            pdf,
            "Possession Security Breakdown",
            chart_paths["possession_breakdown"],
            "This separates safe passers from players who are available, involved, and secure under volume.",
        )
        _pdf_chart_page(
            pdf,
            "Transition Chaos Map",
            chart_paths["transition_map"],
            "United's issue is not only ball-winning; it is the number of unstable moments after possession breaks.",
        )
        _pdf_chart_page(
            pdf,
            "Progression Type Chart",
            chart_paths["progression_type"],
            "Progression is not one skill: some players progress through passing, others through carrying.",
        )
        _pdf_chart_page(
            pdf,
            "Sensitivity Rank Volatility",
            chart_paths["sensitivity_stability"],
            "Lower rank volatility means the player's rank is more stable across weighting scenarios. Average rank should be read alongside volatility, because a player can be stable but still consistently lower-ranked.",
        )
        table_cols = [
            "rank",
            "player",
            "squad",
            "control_midfielder_score",
            "defensive_protection",
            "transition_control",
            "possession_security",
            "progressive_value",
            "age_availability",
            "gate_margin",
        ]
        _pdf_table_page(
            pdf,
            "Shortlist Table",
            shortlist[table_cols].head(12),
            "The table is constrained to core columns to avoid overflow and keep the PDF readable.",
        )
        _pdf_table_page(
            pdf,
            "Archetype Summary",
            score_explanation[
                [
                    "player",
                    "final_score",
                    "archetype_label",
                    "strongest_football_category",
                    "weakest_football_category",
                    "gate_margin",
                ]
            ].head(12),
            "Archetypes translate the model output into plain-English scouting priorities. Strongest and weakest categories exclude age / availability so the football profile is clearer.",
        )
        _pdf_table_page(
            pdf,
            "Borderline Watchlist",
            borderline_watchlist[
                [
                    "player",
                    "squad",
                    "control_midfielder_score",
                    "defensive_protection",
                    "possession_security",
                    "gate_margin",
                ]
            ].head(10),
            "Players within five points below the defensive gate are moved to video/context review rather than treated as rejected.",
        )
        _pdf_table_page(
            pdf,
            "Role-Mismatch Watchlist",
            role_mismatch_watchlist[
                [
                    "player",
                    "squad",
                    "control_midfielder_score",
                    "defensive_protection",
                    "possession_security",
                    "gate_margin",
                ]
            ].head(10),
            "These players may be useful profiles, but their public-data defensive evidence is further from the minimum filter for this specific brief.",
        )
        _pdf_table_page(
            pdf,
            "Sensitivity Summary",
            sensitivity[
                [
                    "player",
                    "rank_base",
                    "rank_defensive_heavy",
                    "rank_possession_heavy",
                    "average_rank",
                    "rank_range",
                    "rank_volatility_score",
                ]
            ]
            .rename(columns={"rank_volatility_score": "rank_volatility_lower_stabler"})
            .head(12),
            "Average rank and rank volatility show whether the shortlist depends too heavily on one subjective weighting choice. Lower volatility is better only when the average rank is also strong.",
        )
        _pdf_text_page(
            pdf,
            "What the Screen Actually Suggests",
            [
                "The screen does not produce one obvious answer. It produces three useful archetypes.",
                "Palacios is the control/progression leader but needs defensive translation and availability review. Cardoso is the cleaner two-axis defensive/security fit. Hjulmand, Florentino Luís, and Wieffer preserve more defensive floor but raise different possession or progression questions.",
                "That is the value of the model: it narrows the next scouting conversation rather than pretending to finish it.",
            ],
        )
    return path


def main() -> None:
    outputs = generate_outputs()
    print("Generated Casemiro Replacement Profile outputs:")
    for name, path in outputs.items():
        print(f"- {name}: {path.relative_to(REPORT_DIR.parent)}")


if __name__ == "__main__":
    main()
