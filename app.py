
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Présidentielle 2027",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE = Path(__file__).parent
POLL_FILE = BASE / "sondages.csv"
CHANGELOG_FILE = BASE / "changelog.csv"


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    polls = pd.read_csv(
        POLL_FILE,
        parse_dates=["publication", "terrain_start", "terrain_end"],
    )
    polls["score"] = pd.to_numeric(polls["score"], errors="coerce")
    polls["echantillon_exprimes"] = pd.to_numeric(
        polls["echantillon_exprimes"], errors="coerce"
    )
    polls["poids"] = (
        polls["echantillon_exprimes"]
        .fillna(1000)
        .clip(lower=1)
        .pow(0.5)
    )
    polls["candidat_normalise"] = polls["candidat"].replace(
        {
            "Marine Le Pen / Jordan Bardella": "Candidat RN",
            "Marine Le Pen": "Candidat RN",
            "Jordan Bardella": "Candidat RN",
        }
    )
    changes = pd.read_csv(CHANGELOG_FILE, parse_dates=["date"])
    return polls, changes


def weighted_average(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate, group in frame.groupby("candidat_normalise"):
        rows.append(
            {
                "candidat": candidate,
                "score": np.average(group["score"], weights=group["poids"]),
                "mesures": group["scenario_id"].nunique(),
                "dernier": group["terrain_end"].max(),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("score", ascending=False)
        if rows
        else pd.DataFrame(columns=["candidat", "score", "mesures", "dernier"])
    )


def trend_table(frame: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    rows = []
    subset = frame[frame["candidat_normalise"].isin(candidates)]
    for (day, candidate), group in subset.groupby(
        ["terrain_end", "candidat_normalise"]
    ):
        rows.append(
            {
                "date": day,
                "candidat": candidate,
                "score": np.average(group["score"], weights=group["poids"]),
            }
        )
    return pd.DataFrame(rows)


def momentum(frame: pd.DataFrame) -> pd.DataFrame:
    trend = trend_table(
        frame,
        sorted(frame["candidat_normalise"].dropna().unique()),
    )
    rows = []
    for candidate, group in trend.groupby("candidat"):
        ordered = group.sort_values("date")
        if len(ordered) < 2:
            delta = np.nan
        else:
            delta = ordered.iloc[-1]["score"] - ordered.iloc[-2]["score"]
        rows.append(
            {
                "candidat": candidate,
                "score_actuel": ordered.iloc[-1]["score"],
                "variation": delta,
            }
        )
    return pd.DataFrame(rows).sort_values("score_actuel", ascending=False)


def consensus_index(frame: pd.DataFrame) -> float | None:
    latest_by_institute = (
        frame.sort_values("terrain_end")
        .groupby(["institut", "candidat_normalise"], as_index=False)
        .tail(1)
    )
    dispersions = (
        latest_by_institute.groupby("candidat_normalise")["score"]
        .std()
        .dropna()
    )
    if dispersions.empty:
        return None
    return max(0.0, 100 - float(dispersions.mean()) * 15)


st.markdown(
    """
    <style>
    .block-container {
        max-width: 1500px;
        padding-top: 1.3rem;
        padding-bottom: 3rem;
    }
    [data-testid="stMetric"] {
        background: rgba(127,127,127,.08);
        border: 1px solid rgba(127,127,127,.18);
        border-radius: 14px;
        padding: 14px 18px;
    }
    .hero-note {
        opacity: .74;
        font-size: .92rem;
        margin-bottom: 1rem;
    }
    .change-positive {color: #2ea043; font-weight: 700;}
    .change-negative {color: #f85149; font-weight: 700;}
    .change-flat {opacity: .75; font-weight: 700;}
    </style>
    """,
    unsafe_allow_html=True,
)

df, changes = load_data()

with st.sidebar:
    st.title("Filtres")
    centre = st.radio(
        "Hypothèse centrale",
        ["Édouard Philippe", "Gabriel Attal"],
        index=0,
    )
    institutes = st.multiselect(
        "Instituts",
        sorted(df["institut"].dropna().unique()),
        default=sorted(df["institut"].dropna().unique()),
    )
    uncertainty = st.slider(
        "Incertitude de simulation (points)",
        0.5, 4.0, 2.0, 0.1,
    )
    simulations = st.slider(
        "Nombre de simulations",
        5_000, 100_000, 30_000, 5_000,
    )
    st.divider()
    st.caption(
        "Les scénarios ne sont pas interchangeables. "
        "Les données Ifop de juillet restent partielles."
    )

scenario = f"{centre} candidat du centre"
view = df[
    (df["scenario"] == scenario)
    & (df["institut"].isin(institutes))
].copy()

st.title("Présidentielle 2027 — observatoire des sondages")

if view.empty:
    st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
    st.stop()

latest_date = view["terrain_end"].max()
latest = view[view["terrain_end"] == latest_date].sort_values(
    "score", ascending=False
)
average = weighted_average(view)
mom = momentum(view)
consensus = consensus_index(view)

st.markdown(
    f"<div class='hero-note'>Dernière donnée intégrée : "
    f"<b>{latest_date:%d/%m/%Y}</b> · Hypothèse : <b>{scenario}</b></div>",
    unsafe_allow_html=True,
)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Instituts", view["institut"].nunique())
m2.metric("Vagues", view["poll_id"].nunique())
m3.metric("Premier", latest.iloc[0]["candidat"], f"{latest.iloc[0]['score']:.1f} %")
m4.metric("Deuxième", latest.iloc[1]["candidat"], f"{latest.iloc[1]['score']:.1f} %")
m5.metric(
    "Consensus instituts",
    "N/D" if consensus is None else f"{consensus:.0f}/100",
)

tabs = st.tabs(
    [
        "Synthèse",
        "Évolution",
        "Instituts",
        "Scénarios",
        "Données",
        "Sources",
        "Méthodologie",
    ]
)

with tabs[0]:
    left, right = st.columns([1.15, 1])

    with left:
        st.subheader("Moyenne pondérée")
        chart_df = average.sort_values("score")
        fig = px.bar(
            chart_df,
            x="score",
            y="candidat",
            orientation="h",
            text=chart_df["score"].map(lambda v: f"{v:.1f} %"),
            labels={"score": "Score moyen (%)", "candidat": ""},
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(height=520, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Qualification simulée")
        means = average.set_index("candidat")["score"]
        rng = np.random.default_rng(2027)
        draws = rng.normal(
            means.to_numpy(),
            uncertainty,
            size=(simulations, len(means)),
        )
        draws = np.clip(draws, 0, None)
        top_two = np.argpartition(draws, -2, axis=1)[:, -2:]
        probabilities = [
            100 * (top_two == index).any(axis=1).mean()
            for index in range(len(means))
        ]
        sim_df = pd.DataFrame(
            {"candidat": means.index, "probabilite": probabilities}
        ).sort_values("probabilite")

        fig2 = px.bar(
            sim_df,
            x="probabilite",
            y="candidat",
            orientation="h",
            text=sim_df["probabilite"].map(lambda v: f"{v:.1f} %"),
            labels={"probabilite": "Probabilité simulée (%)", "candidat": ""},
        )
        fig2.update_traces(textposition="outside", cliponaxis=False)
        fig2.update_xaxes(range=[0, 105])
        fig2.update_layout(height=520, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.info(
        "La simulation est un test de sensibilité du classement. "
        "Elle ne constitue pas une prévision électorale."
    )

    st.subheader("Dynamique récente")
    momentum_display = mom.copy()
    momentum_display["score_actuel"] = momentum_display["score_actuel"].map(
        lambda v: f"{v:.1f} %"
    )
    momentum_display["variation"] = momentum_display["variation"].map(
        lambda v: "N/D" if pd.isna(v) else f"{v:+.1f} pt"
    )
    st.dataframe(momentum_display, use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Évolution des principaux candidats")
    candidates = (
        view.groupby("candidat_normalise")["score"]
        .max()
        .sort_values(ascending=False)
        .head(8)
        .index
        .tolist()
    )
    selected = st.multiselect(
        "Candidats affichés",
        candidates,
        default=candidates[:4],
    )
    trend = trend_table(view, selected)

    if trend.empty:
        st.warning("Aucune série à afficher.")
    else:
        fig3 = px.line(
            trend,
            x="date",
            y="score",
            color="candidat",
            markers=True,
            labels={"date": "", "score": "Intentions de vote (%)", "candidat": ""},
        )
        fig3.update_layout(height=620, legend_title_text="")
        st.plotly_chart(fig3, use_container_width=True)
        st.caption(
            "La série reste courte. Sa lecture deviendra plus robuste "
            "à mesure que de nouvelles vagues seront intégrées."
        )

with tabs[2]:
    st.subheader("Comparer les instituts")
    candidate = st.selectbox(
        "Candidat analysé",
        sorted(view["candidat_normalise"].dropna().unique()),
    )
    candidate_view = view[
        view["candidat_normalise"] == candidate
    ].copy()

    fig4 = px.scatter(
        candidate_view,
        x="terrain_end",
        y="score",
        color="institut",
        size="poids",
        hover_data=["commanditaire", "couverture"],
        labels={"terrain_end": "", "score": "Score (%)", "institut": "Institut"},
    )
    fig4.update_layout(height=540)
    st.plotly_chart(fig4, use_container_width=True)

    institute_summary = (
        candidate_view.groupby("institut", as_index=False)
        .agg(
            score_moyen=("score", "mean"),
            mesures=("scenario_id", "nunique"),
            dernier=("terrain_end", "max"),
        )
        .sort_values("score_moyen", ascending=False)
    )
    institute_summary["dernier"] = institute_summary["dernier"].dt.strftime(
        "%d/%m/%Y"
    )
    st.dataframe(institute_summary, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Comparer les hypothèses Philippe et Attal")
    comparable = df[df["institut"].isin(institutes)].copy()
    matrix = comparable.pivot_table(
        index="candidat_normalise",
        columns="scenario",
        values="score",
        aggfunc="mean",
    )
    st.dataframe(matrix.style.format("{:.1f}"), use_container_width=True)
    st.caption(
        "Les colonnes correspondent à des hypothèses distinctes. "
        "Un écart n'est pas nécessairement une évolution dans le temps."
    )

with tabs[4]:
    st.subheader("Base de données")
    export_cols = [
        "publication", "terrain_start", "terrain_end", "institut",
        "commanditaire", "scenario", "candidat", "score",
        "echantillon_exprimes", "couverture", "source_url",
    ]
    export = df[export_cols].sort_values(
        ["terrain_end", "scenario", "score"],
        ascending=[False, True, False],
    )
    st.dataframe(export, use_container_width=True, hide_index=True)

    csv_bytes = export.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Télécharger les données CSV",
        data=csv_bytes,
        file_name="sondages_presidentielle_2027.csv",
        mime="text/csv",
    )

with tabs[5]:
    left, right = st.columns([1.1, 1])

    with left:
        st.subheader("Journal des changements")
        log = changes.sort_values("date", ascending=False).copy()
        log["date"] = log["date"].dt.strftime("%d/%m/%Y")
        st.dataframe(log, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Couverture des vagues")
        coverage = (
            df.groupby(
                ["poll_id", "institut", "terrain_end", "couverture"],
                as_index=False,
            )
            .agg(
                scenarios=("scenario_id", "nunique"),
                lignes=("candidat", "count"),
            )
            .sort_values("terrain_end", ascending=False)
        )
        coverage["terrain_end"] = coverage["terrain_end"].dt.strftime(
            "%d/%m/%Y"
        )
        st.dataframe(coverage, use_container_width=True, hide_index=True)

    st.subheader("Liens vers les sources")
    sources = (
        df[["institut", "commanditaire", "poll_id", "source_url"]]
        .drop_duplicates()
        .sort_values("poll_id", ascending=False)
    )
    for _, row in sources.iterrows():
        st.markdown(
            f"**{row['institut']} — {row['commanditaire']}**  \n"
            f"[Ouvrir la source]({row['source_url']})"
        )

with tabs[6]:
    st.subheader("Méthodologie")
    st.markdown(
        """
        - Une ligne correspond à un candidat dans un scénario de sondage.
        - Les scénarios distincts ne sont pas fusionnés sans précaution.
        - La pondération est proportionnelle à la racine carrée de la taille
          d'échantillon.
        - Les candidatures RN sont regroupées sous l'étiquette analytique
          « Candidat RN » dans certaines vues.
        - Les résultats partiels sont signalés comme tels.

        **Limites**

        La simulation ne modélise ni les indécis, ni les corrélations entre
        candidats, ni les effets de campagne, ni les biais propres aux instituts.
        """
    )
