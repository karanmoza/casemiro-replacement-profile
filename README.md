# Casemiro Replacement Profile

Public-data recruitment framework for identifying a modern Casemiro replacement profile for Manchester United.

## Project Question

> If Manchester United need more control, what kind of midfielder should they target as a modern Casemiro replacement?

## Core Thesis

The goal is not to find a player who looks exactly like Casemiro statistically. The goal is to find a midfielder who preserves enough defensive protection while improving United's possession-control problem.

**The next signing should not only win duels. It should prevent some of them from happening.**

The United memo says United needed control. This project asks how to identify control.

## What This Is

A public-data recruitment screen that converts a tactical problem into a transparent player-scoring framework. It is designed to focus scouting and video discussion.

## What This Is Not

- Not proprietary scouting data.
- Not a final signing recommendation.
- Not a substitute for video, medical, contract, fee, or tactical role analysis.

## Data

The project uses public-data inputs:

- FBref-style/public aggregate player statistics for broader player screening.
- StatsBomb open-data concepts for event-data role design and methodology.
- Manual public context fields where needed, such as age, minutes, market value, and availability notes.
- A fallback sample dataset in `data/raw/sample_fbref_player_stats.csv` so the project can run offline.

Caveats: StatsBomb open data is limited to selected competitions, public aggregate stats are not equivalent to club scouting data, and public statsbombpy access should not be treated as full 360 data access.

## Methodology

1. Build a public player pool across the selected leagues.
2. Filter to midfield profiles and practical target constraints.
3. Calculate per-90, rate, and per-touch metrics.
4. Convert input metrics to 0-100 percentile-style scores within the screened pool.
5. Invert negative metrics such as fouls, cards, miscontrols, dispossessions, and turnover rate.
6. Average input metric scores into five category scores.
7. Weight category scores into the final Control Midfielder Score.
8. Apply a light defensive gate to create the published shortlist.
9. Run sensitivity analysis across reasonable alternative weighting schemes.
10. Produce a shortlist, watchlist, metric dictionary, player explanation table, charts, HTML report, and PDF report.

Each input metric is first converted into a comparable rate, percentage, or per-touch measure. It is then normalized into a 0-100 percentile-style score within the screened player pool. For negative events such as fouls, cards, miscontrols, dispossessions, and turnover rate, the score is inverted so that safer players receive higher values. Category scores are calculated as the average of available input-metric scores. The final Control Midfielder Score is a weighted average of the five category scores.

## Category Scores

### Defensive Protection

Football question: can the player protect the back line, defend central spaces, and retain enough of Casemiro's defensive floor?

Input metrics: tackles + interceptions per 90, interceptions per 90, dribblers tackled %, blocks per 90, aerial duel win %, defensive/middle-third actions per 90.

Transformation: higher values receive higher percentile scores.

Caveat: defensive volume is affected by team style, possession share, and tactical role.

### Transition Control

Football question: can the player stop broken-play moments from becoming emergency defending?

Input metrics: ball recoveries per 90, pressure/counterpressure regains per 90, defensive actions after loss, fouls committed per 90, cards per 90, miscontrols per 90, dispossessed per 90.

Transformation: regain/activity metrics use normal percentiles; fouls, cards, miscontrols, and dispossessions use inverse percentiles.

Caveat: public aggregate data cannot fully capture pressing triggers or exact event sequence context.

### Possession Security

Football question: can the player receive, circulate, and avoid cheap turnovers under volume?

Input metrics: pass completion %, short/medium pass completion %, passes received per 90, touches per 90, dispossessed per touch, miscontrols per touch, turnover rate.

Transformation: positive involvement/security metrics use normal percentiles; per-touch turnover risk uses inverse percentiles.

Caveat: public data does not fully show pressure level, pass difficulty, or pitch location.

### Progressive Value

Football question: can the player move the ball forward without turning the role into a high-risk creator search?

Input metrics: progressive passes per 90, progressive carries per 90, passes into final third per 90, carries into final third per 90, progressive passing distance per 90, live-ball shot-creating actions per 90.

Transformation: higher values receive higher percentile scores.

Caveat: progression type matters. Passing progressors and carrying progressors solve different tactical problems.

### Age / Availability

Football question: does the player fit a plausible squad-building and signal-reliability window?

Input metrics: age score and minutes played score.

Transformation: age is scored around a useful squad-building band; minutes use percentile scoring.

Caveat: this is only a public proxy. Medical history, workload, contract status, fee, and player availability need separate work.

## Weighting Rationale

The weighting scheme reflects Manchester United's specific midfield-control problem.

This is not a search for the best pure ball-winner. It is a search for a midfielder who can preserve enough defensive protection while improving control.

- Defensive protection receives 30%, the highest single weight, because any Casemiro replacement profile must still protect the back line, defend central spaces, and survive defensive responsibility.
- Transition control receives 25% because United's issue is not only settled defending; it is also the number of chaotic moments created after possession breaks.
- Possession security receives 25% because the deeper thesis is that United need control. A midfielder who loses possession too often will recreate the same emergency-defending problem even if he wins duels.
- Progressive value receives 15% because United still need the player to move the ball forward, but this role should not become a pure creator search.
- Age / availability receives 5% because practical squad-building context matters, but it should not overpower the football profile.

The weighting scheme is designed to reward midfielders who can defend first, stabilize transitions second, secure possession third, and progress the ball without turning the role into a high-risk creator profile.

These weights are subjective but transparent. That is why the report includes sensitivity analysis to test whether the shortlist collapses when reasonable weighting assumptions change.

## Defensive Gate

A weight ranks players. A gate enforces a minimum requirement.

Even though defensive protection has the highest single weight, a player can still score highly overall if he is elite in possession security and progression. For a Casemiro replacement profile, that creates a risk: the model could surface elegant possession players who do not have enough defensive evidence to survive United's midfield environment.

The defensive gate is therefore a light screening threshold. It is not a scouting verdict. It removes profiles with limited defensive evidence from the published shortlist, while keeping interesting names on the watchlist for video review.

**The defensive gate should be read as a minimum-evidence filter, not as a final judgment on defensive ability.**

Palacios clears the defensive gate narrowly, so he should not be treated as a pure defensive replacement. Elliot Anderson falls just below the gate, so he should remain a watchlist player rather than be treated as definitively rejected. Borderline differences around the gate should be tested with video, tactical role context, league translation, and team style.

This is why the report separates the published shortlist from two watchlist groups rather than deleting below-gate players entirely:

- `borderline_watchlist.csv`: players within five points below the gate, where video and role review should decide whether the public-data signal is too harsh.
- `role_mismatch_watchlist.csv`: players further below the gate, who may still be useful footballers but are less aligned with this specific Casemiro-replacement control brief.

## Sensitivity Analysis

Sensitivity analysis tests whether the shortlist depends too heavily on one subjective weighting choice. A robust candidate remains near the top under several reasonable versions of the model. A fragile candidate ranks highly only when the model favors one specific trait.

Scenarios:

- Base case: defensive 30, transition 25, possession 25, progressive 15, age 5
- Defensive-heavy: defensive 40, transition 25, possession 20, progressive 10, age 5
- Possession-heavy: defensive 25, transition 20, possession 35, progressive 15, age 5
- Transition-heavy: defensive 25, transition 35, possession 20, progressive 15, age 5
- Progression-heavy: defensive 25, transition 20, possession 20, progressive 30, age 5
- Equal-weight football profile: defensive 25, transition 25, possession 25, progressive 20, age 5

Sensitivity analysis is used because the category weights are transparent but still subjective. If a candidate only ranks well under one weighting scheme, the model is telling us that the recommendation is fragile. If a candidate stays high across multiple schemes, the player is a more robust scouting priority. The output includes `average_rank` and `rank_volatility_score` so the ranking can be audited without relying only on the base-case score.

Lower rank volatility means the player's rank is more stable across weighting scenarios. Average rank should be read alongside volatility, because a player can be stable but still consistently lower-ranked.

## Diagnostic Charts

The final score uses all five categories, but the diagnostic charts intentionally use smaller subsets of input metrics. This avoids every plot telling the same story and helps identify why a player scores well: defensive activity, possession security, transition safety, or progression type.

## Substack Adaptation Note

The full HTML/PDF/GitHub report keeps the complete input-metric dictionary for auditability. For a Substack article, use a shorter methodology table with only `Category`, `Football question`, and `Example inputs`, then link back to the GitHub report for the full metric dictionary.

## Outputs

Reports:

- `reports/casemiro_replacement_report.html`
- `reports/casemiro_replacement_report.pdf`
- `reports/casemiro_replacement_summary.pdf`

Tables:

- `outputs/candidate_shortlist.csv`
- `outputs/watchlist_removed_by_gate.csv`
- `outputs/borderline_watchlist.csv`
- `outputs/role_mismatch_watchlist.csv`
- `outputs/category_scores.csv`
- `outputs/player_score_explanation.csv`
- `outputs/metric_dictionary.csv`
- `outputs/sensitivity_analysis.csv`

Charts:

- `reports/charts/ranked_control_midfielder_score.png`
- `reports/charts/security_vs_defensive_floor.png`
- `reports/charts/category_heatmap.png`
- `reports/charts/casemiro_candidate_radar.png`
- `reports/charts/defensive_gate_diagnostic.png`
- `reports/charts/possession_security_breakdown.png`
- `reports/charts/transition_chaos_map.png`
- `reports/charts/progression_type_chart.png`
- `reports/charts/sensitivity_rank_stability.png`
- `reports/charts/archetype_summary.png`

## Key Interpretation

Palacios leads the screen as a possession-control candidate, not as a like-for-like Casemiro replacement. Cardoso is the cleaner two-axis defensive/security fit. Casemiro and Manuel Ugarte are reference players in the report, not transfer targets. Borderline and watchlist players should be reviewed through video and tactical role context.

## What the Screen Actually Suggests

The screen does not produce one obvious answer. It produces three useful archetypes. Palacios is the control/progression leader but needs defensive translation and availability review. Cardoso is the cleaner two-axis defensive/security fit. Hjulmand, Florentino Luís, and Wieffer preserve more defensive floor but raise different possession or progression questions.

That is the value of the model: it narrows the next scouting conversation rather than pretending to finish it.

## Limitations

- Public data cannot replace club scouting.
- Aggregate stats lose role, team, pressure, and pitch-location context.
- StatsBomb open data is limited to selected competitions.
- Public statsbombpy access should not be treated as full 360 data access.
- League strength and team style affect metrics.
- Injury history and transfer feasibility require separate work.
- The defensive gate is a screen, not a verdict.

## How To Run

From the project root:

```bash
pip install -r requirements.txt
python -m src.report
python -m src.validate_outputs
```

If Matplotlib cannot write to its default cache directory:

```bash
MPLCONFIGDIR=.mplconfig python -m src.report
python -m src.validate_outputs
```

## Suggested Resume Bullet

Built a Python public-data recruitment framework for Manchester United midfield succession planning, combining public aggregate metrics, StatsBomb open-data concepts for event-data role design, percentile normalization, defensive-gate screening, sensitivity analysis, diagnostic visualizations, and HTML/PDF analytical reporting.
