
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "data"

def load_polls() -> pd.DataFrame:
    df = pd.read_csv(
        DATA_DIR / "sondages.csv",
        parse_dates=["publication", "terrain_start", "terrain_end"]
    )
    df["echantillon_exprimes"] = pd.to_numeric(df["echantillon_exprimes"], errors="coerce")
    df["poids"] = df["echantillon_exprimes"].fillna(1000).clip(lower=1).pow(0.5)
    df["candidat_normalise"] = df["candidat"].replace({
        "Marine Le Pen / Jordan Bardella": "Candidat RN",
        "Marine Le Pen": "Candidat RN",
        "Jordan Bardella": "Candidat RN",
    })
    return df

def load_changelog() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "changelog.csv", parse_dates=["date"])

def weighted_average(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["candidat_normalise", "score", "n_mesures", "dernier"])
    rows = []
    for candidate, group in frame.groupby("candidat_normalise"):
        rows.append({
            "candidat_normalise": candidate,
            "score": np.average(group["score"], weights=group["poids"]),
            "n_mesures": group["scenario_id"].nunique(),
            "dernier": group["terrain_end"].max(),
        })
    return pd.DataFrame(rows).sort_values("score", ascending=False)

def scenario_name(center_candidate: str) -> str:
    return f"{center_candidate} candidat du centre"
