# Casemiro Replacement Profile

Public-data recruitment framework for identifying a modern Manchester United control midfielder. The sample target pool is framed **as of May 6, 2026**.

## Project Question

Manchester United's midfield issue is not only ball-winning. The prior memo argued that United added output when they needed control. This project extends that idea by asking:

> If United need control, what kind of midfielder should they target as a modern Casemiro replacement?

The United memo says United needed control. This project asks how to identify control.

## Core Thesis

The project is not trying to find a player who looks exactly like Casemiro statistically. The goal is to preserve his defensive floor while improving the possession-control problem around him.

**Core line:** The next signing should not only win duels. It should prevent some of them from happening.

## May 2026 Scope

The shortlist enforces these portfolio constraints:

- Candidate leagues: Premier League, La Liga, Primeira Liga, Bundesliga, Ligue 1, and Serie A.
- Current Manchester United midfielders are treated as reference profiles, not targets.
- Midfielders from Arsenal, Chelsea, Liverpool, and Manchester City are excluded from the target pool.
- Manuel Ugarte is included only as a current United reference profile.
- Date of birth is stored in the data layer and age is calculated from the as-of date, rather than manually typed.
- Published shortlist candidates must clear a light defensive-protection gate. The gate is intentionally low because the model screens for complementary control midfielders, not only defensive destroyers. The final ranking then follows the weighted Control Midfielder Score.

## Data Sources

This repo is built to work with public data:

- StatsBomb open data to demonstrate the event-data methodology behind the role profile.
- FBref-style/public aggregate player statistics for broader candidate screening, supplemented where needed for non-Big-Five leagues such as Portugal.
- Optional manual context fields such as age, minutes, market value, and availability notes.

The project includes a sample FBref-style fallback dataset in `data/raw/sample_fbref_player_stats.csv`, generated automatically by the loader. This keeps the project runnable offline and suitable for portfolio review. Replace that CSV with current exported public data to refresh the analysis.

## Methodology

The model creates a **Control Midfielder Score** from five categories:

| Category | Weight | Interpretation |
| --- | ---: | --- |
| Defensive protection | 30% | Can the player protect central spaces and retain a high defensive floor? |
| Transition control | 25% | Can the player stop attacks from becoming emergency defending? |
| Possession security | 25% | Can the player receive, circulate, and avoid cheap turnovers? |
| Progressive value | 15% | Can the player move the ball forward without turning into a high-risk creator? |
| Age / availability proxy | 5% | Does the profile fit a plausible squad-building window? |

Metrics are normalized into percentile-style 0-100 scores. Lower-risk metrics such as fouls, cards, miscontrols, dispossessions, and turnover rates use inverse percentiles.

## Key Implementation Choices

- The project is framed as a transparent public-data recruitment screen, not a proprietary scouting model.
- StatsBomb open data is used for event-data role design and methodology demonstration, while the player shortlist is scored from public aggregate statistics.
- Category scores are simple averages of normalized metric inputs so that every result can be traced back to visible public fields.
- Lower-is-better metrics use inverse percentiles rather than being dropped, because control midfielders should be rewarded for avoiding cheap turnovers and unnecessary fouls.
- The published shortlist applies a light defensive-protection gate to remove pure control profiles with limited ball-winning evidence.
- Age is calculated from date of birth using the project as-of date, which avoids stale manual age labels.
- The model keeps a filtered-out watchlist so readers can audit which otherwise interesting players were removed by the defensive gate.

## Metric Examples

**Defensive protection**

- Tackles plus interceptions per 90
- Dribblers tackled percentage
- Interceptions per 90
- Blocks per 90
- Aerial duel win percentage
- Defensive and middle-third defensive actions where available

**Transition control**

- Ball recoveries per 90
- Pressure regains or counterpressure regains where available
- Fouls committed, inverse percentile
- Cards, inverse percentile
- Miscontrols and dispossessions, inverse percentile
- Defensive actions after possession loss where available

**Possession security**

- Pass completion percentage
- Short and medium pass completion percentage
- Passes received per 90
- Touches per 90
- Dispossessed per touch, inverse percentile
- Miscontrols per touch, inverse percentile
- Turnover rate, inverse percentile

**Progressive value**

- Progressive passes per 90
- Progressive carries per 90
- Passes into final third per 90
- Carries into final third per 90
- Progressive passing distance
- Live-ball shot-creating actions, low weight

**Age / availability**

- Age score, with the ideal public-screening range around 21-27
- Minutes played score
- Optional market value and availability notes for interpretation

## Outputs

Running the pipeline creates:

- `outputs/candidate_shortlist.csv`
- `outputs/category_scores.csv`
- `outputs/sensitivity_analysis.csv`
- `outputs/player_context_sources.csv`
- `outputs/filtered_out_watchlist.csv`, showing otherwise eligible players removed by the defensive-protection gate
- `outputs/scoring_methodology.csv`, listing category weights, metric inputs, and scoring direction
- `reports/charts/ranked_control_midfielder_score.png`
- `reports/charts/category_heatmap.png`
- `reports/charts/casemiro_candidate_radar.png`
- `reports/charts/security_vs_defensive_floor.png`
- `reports/charts/sensitivity_analysis.png`
- `reports/casemiro_replacement_report.html`, the primary polished report with clean chart sections and plain-English explanations
- `reports/casemiro_replacement_summary.pdf`, a secondary PDF export

The report and charts are committed so the repo can be inspected without rerunning the pipeline:

- [HTML report](reports/casemiro_replacement_report.html)
- [Ranked shortlist chart](reports/charts/ranked_control_midfielder_score.png)
- [Category heatmap](reports/charts/category_heatmap.png)
- [Radar comparison](reports/charts/casemiro_candidate_radar.png)

## How To Run

Create an environment, install dependencies, and run the report module from the project root:

```bash
pip install -r requirements.txt
python -m src.report
```

If Matplotlib cannot write to its default cache directory, set a local cache:

```bash
MPLCONFIGDIR=.mplconfig python -m src.report
```

## Notebook Flow

The notebooks are organized as a portfolio workflow:

1. `notebooks/01_statsbomb_event_methodology.ipynb` - demonstrate event-data logic using StatsBomb open data when available.
2. `notebooks/01_data_collection.ipynb` - load public aggregate data and document fallback logic.
3. `notebooks/02_metric_engineering.ipynb` - create per-90 and possession-risk metrics.
4. `notebooks/03_scoring_model.ipynb` - calculate category and total scores.
5. `notebooks/04_visualisations.ipynb` - generate charts.
6. `notebooks/05_recruitment_summary.ipynb` - create the final shortlist, HTML report, and PDF export.

## Interpretation

A high score does not mean "sign this player." It means the player is worth deeper review under a control-midfielder brief, inside the May 2026 target-pool constraints. The best candidates should combine:

- Enough defensive output to keep Casemiro's floor.
- Better security and receiving volume to stabilize possession.
- Transition behavior that prevents duels from occurring in dangerous spaces.
- Enough progression to help United move up the pitch without forcing every attack.

In the generated sample, Exequiel Palacios leads the public-data screen as a possession-control profile, not as a pure Casemiro defensive replacement. He clears the light defensive gate but remains below Casemiro's defensive reference band, so any recommendation would require video confirmation that his coverage translates to United's transition-heavy environment, plus availability and injury-history review. Manuel Ugarte is retained as an internal reference: his defensive protection and basic security are useful, but his low progressive-value score points to why United may still need a complementary midfielder.

## Limitations

- StatsBomb open data is limited to selected competitions and does not cover every current recruitment target.
- Public statsbombpy access should not be treated as access to proprietary 360 metrics.
- FBref/public data is aggregated and not equivalent to club scouting data.
- Public definitions vary by provider and may not match internal event tagging.
- League strength, tactical role, team possession share, and pressing systems affect these metrics.
- Market value is treated only as context, not a definitive availability measure.
- This is a screening framework, not a final recruitment decision model.

## Suggested Resume Bullet

Built a Python public-data recruitment framework for Manchester United midfield succession planning, combining FBref-style/public aggregate metrics, StatsBomb open-data concepts for event-data role design, percentile normalization, weighted scoring, sensitivity analysis, BCG-style visual exhibits, and an HTML analytical report.
