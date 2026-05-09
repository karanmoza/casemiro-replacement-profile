"""StatsBomb open-data loader and event-methodology helpers.

StatsBomb open data is used here to demonstrate the event-data logic behind the
role profile and to make the project extensible. The included end-to-end run
does not require network access; it falls back to aggregated public player data
when open-event loading is unavailable.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_statsbomb_events(
    competition_id: int | None = None,
    season_id: int | None = None,
    local_path: str | Path | None = None,
) -> pd.DataFrame:
    """Load StatsBomb events from a local file or via statsbombpy when present.

    Returns an empty DataFrame when data is unavailable so the broader project
    remains runnable offline.
    """

    if local_path:
        path = Path(local_path)
        if path.suffix == ".parquet":
            return pd.read_parquet(path)
        if path.suffix == ".json":
            return pd.read_json(path)
        return pd.read_csv(path)

    if competition_id is None or season_id is None:
        return pd.DataFrame()

    try:
        from statsbombpy import sb
    except ImportError:
        return pd.DataFrame()

    try:
        matches = sb.matches(competition_id=competition_id, season_id=season_id)
        event_frames = [
            sb.events(match_id=int(match_id)) for match_id in matches["match_id"].dropna().unique()
        ]
    except Exception:
        return pd.DataFrame()

    if not event_frames:
        return pd.DataFrame()
    return pd.concat(event_frames, ignore_index=True)


def engineer_event_control_metrics(events: pd.DataFrame) -> pd.DataFrame:
    """Aggregate selected StatsBomb event ideas to player level when available.

    This helper is deliberately conservative because StatsBomb open data covers
    selected competitions and uses event definitions that are not equivalent to
    FBref aggregate columns.
    """

    required = {"player", "type"}
    if events.empty or not required.issubset(events.columns):
        return pd.DataFrame()

    df = events.copy()
    player_col = "player"
    type_col = "type"
    if isinstance(df[type_col].iloc[0], dict):
        df[type_col] = df[type_col].apply(lambda value: value.get("name") if isinstance(value, dict) else value)

    grouped = df.groupby(player_col)
    out = pd.DataFrame({"player": grouped.size().index})
    out["sb_ball_recoveries"] = out["player"].map(
        df[df[type_col].eq("Ball Recovery")].groupby(player_col).size()
    ).fillna(0)
    out["sb_pressures"] = out["player"].map(
        df[df[type_col].eq("Pressure")].groupby(player_col).size()
    ).fillna(0)
    out["sb_interceptions"] = out["player"].map(
        df[df[type_col].eq("Interception")].groupby(player_col).size()
    ).fillna(0)
    return out
