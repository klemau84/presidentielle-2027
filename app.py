
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Présidentielle 2027",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE = Path(__file__).parent


@st.cache_data
def load_data():
    first = pd.read_csv(
        BASE / "sondages.csv",
        parse_dates=["publication", "terrain_start", "terrain_end"],
    )
    second = pd.read_csv(
        BASE / "second_tour.csv",
        parse_dates=["publication", "terrain_start", "terrain_end"],
    )
    changes = pd.read_csv(BASE / "changelog.csv", parse_dates=["date"])
    reports = pd.read_csv(BASE / "reports_demo.csv")
    leaders = pd.read_csv(BASE / "leaders_demo.csv")

    first["score"] = pd.to_numeric(first["score"], errors="coerce")
    first["echantillon_exprimes"] = pd.to_numeric(
        first["echantillon_exprimes"], errors="coerce"
    )
    first["poids"] = (
        first["echantillon_exprimes"]
        .fillna(1000)
        .clip(lower=1)
        .pow(0.5)
    )
    first["candidat_normalise"] = first["candidat"].replace(
        {
            "Marine Le Pen / Jordan Bardella": "Candidat RN",
            "Marine Le Pen": "Candidat RN",
            "Jordan Bardella": "Candidat RN",
        }
    )

    second["score"] = pd.to_numeric(second["score"], errors="coerce")
    return first, second, changes, reports, leaders


def weighted_average(frame):
    rows = []
    for candidate, group in frame.groupby("candidat_normalise"):
        rows.append(
            {
                "candidat": candidate,
                "score": np.average(group["score"], weights=group["poids"]),
                "mesures": group["scenario_id"].nunique(),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["candidat", "score", "mesures"])
    return pd.DataFrame(rows).sort_values("score", ascending=False)


def trend_table(frame, candidates):
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
    </style>
    """,
    unsafe_allow_html=True,
)

first, second, changes, reports, leaders = load_data()

st.title("Présidentielle 2027 — observatoire des sondages")

section = st.radio(
    "Analyse",
    ["Premier tour", "Second tour", "Familles et reports — démonstration"],
    horizontal=True,
)

if section == "Premier tour":
    with st.sidebar:
        st.title("Filtres — Premier tour")
        centre = st.radio(
            "Hypothèse centrale",
            ["Édouard Philippe", "Gabriel Attal"],
            index=0,
        )
        institutes = st.multiselect(
            "Instituts",
            sorted(first["institut"].dropna().unique()),
            default=sorted(first["institut"].dropna().unique()),
        )
        uncertainty = st.slider(
            "Incertitude de simulation (points)",
            0.5,
            4.0,
            2.0,
            0.1,
        )
        simulations = st.slider(
            "Nombre de simulations",
            5_000,
            100_000,
            30_000,
            5_000,
        )
        st.caption(
            "Les scénarios de candidatures ne sont pas interchangeables."
        )

    scenario = f"{centre} candidat du centre"
    view = first[
        (first["scenario"] == scenario)
        & (first["institut"].isin(institutes))
    ].copy()

    if view.empty:
        st.warning("Aucune donnée ne correspond aux filtres.")
        st.stop()

    latest_date = view["terrain_end"].max()
    latest = view[view["terrain_end"] == latest_date].sort_values(
        "score", ascending=False
    )
    average = weighted_average(view)

    st.markdown(
        f"<div class='hero-note'>Dernière donnée : "
        f"<b>{latest_date:%d/%m/%Y}</b> · Hypothèse : "
        f"<b>{scenario}</b></div>",
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Instituts", view["institut"].nunique())
    m2.metric("Vagues", view["poll_id"].nunique())
    m3.metric(
        "Premier",
        latest.iloc[0]["candidat"],
        f"{latest.iloc[0]['score']:.1f} %",
    )
    m4.metric(
        "Deuxième",
        latest.iloc[1]["candidat"],
        f"{latest.iloc[1]['score']:.1f} %",
    )

    tabs = st.tabs(
        ["Synthèse", "Évolution", "Instituts", "Scénarios", "Données"]
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
            st.plotly_chart(fig, width="stretch")

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
                text=sim_df["probabilite"].map(
                    lambda value: f"{value:.1f} %"
                ),
                labels={
                    "probabilite": "Probabilité simulée (%)",
                    "candidat": "",
                },
            )
            fig2.update_traces(textposition="outside", cliponaxis=False)
            fig2.update_xaxes(range=[0, 105])
            fig2.update_layout(height=520, showlegend=False)
            st.plotly_chart(fig2, width="stretch")

        st.info(
            "La qualification affichée est une simulation pédagogique, "
            "pas une intention de vote de second tour."
        )

    with tabs[1]:
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
                labels={
                    "date": "",
                    "score": "Intentions de vote (%)",
                    "candidat": "",
                },
            )
            fig3.update_layout(height=620, legend_title_text="")
            st.plotly_chart(fig3, width="stretch")

    with tabs[2]:
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
            labels={
                "terrain_end": "",
                "score": "Score (%)",
                "institut": "Institut",
            },
        )
        fig4.update_layout(height=540)
        st.plotly_chart(fig4, width="stretch")

    with tabs[3]:
        comparable = first[first["institut"].isin(institutes)]
        matrix = comparable.pivot_table(
            index="candidat_normalise",
            columns="scenario",
            values="score",
            aggfunc="mean",
        )
        st.dataframe(
            matrix.style.format("{:.1f}"),
            width="stretch",
        )

    with tabs[4]:
        export = first.sort_values(
            ["terrain_end", "scenario", "score"],
            ascending=[False, True, False],
        )
        st.dataframe(export, width="stretch", hide_index=True)
        st.download_button(
            "Télécharger les données du premier tour",
            export.to_csv(index=False).encode("utf-8-sig"),
            "premier_tour_2027.csv",
            "text/csv",
        )

elif section == "Second tour":
    with st.sidebar:
        st.title("Filtres — Second tour")
        duel = st.selectbox(
            "Duel",
            second["duel"].drop_duplicates().tolist(),
        )
        st.caption(
            "Les valeurs affichées sont des intentions de vote publiées."
        )

    duel_data = second[second["duel"] == duel].copy().sort_values(
        "score", ascending=False
    )
    latest_date = duel_data["terrain_end"].max()
    nsp = duel_data["nsp_pct"].iloc[0]
    base = int(duel_data["echantillon_exprimes"].iloc[0])

    st.markdown(
        f"<div class='hero-note'>Dernier sondage de second tour : "
        f"<b>{latest_date:%d/%m/%Y}</b> · <b>{duel}</b></div>",
        unsafe_allow_html=True,
    )

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Vainqueur du duel", duel_data.iloc[0]["candidat"])
    s2.metric("Score", f"{duel_data.iloc[0]['score']:.0f} %")
    s3.metric(
        "Écart",
        f"{duel_data.iloc[0]['score'] - duel_data.iloc[1]['score']:.0f} pts",
    )
    s4.metric("Sans opinion", f"{nsp:.1f} %")

    tabs = st.tabs(
        ["Duel", "Comparer les seconds tours", "Données", "Méthodologie"]
    )

    with tabs[0]:
        fig = px.bar(
            duel_data.sort_values("score"),
            x="score",
            y="candidat",
            orientation="h",
            text=duel_data.sort_values("score")["score"].map(
                lambda value: f"{value:.0f} %"
            ),
            labels={"score": "Intentions de vote (%)", "candidat": ""},
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_xaxes(range=[0, 100])
        fig.update_layout(height=430, showlegend=False)
        st.plotly_chart(fig, width="stretch")

        st.caption(
            f"Ifop pour LCI / Le Figaro · base exprimés : {base} · "
            f"sans opinion parmi les inscrits : {nsp:.1f} %."
        )

    with tabs[1]:
        compare = second.pivot_table(
            index="duel",
            columns="candidat",
            values="score",
            aggfunc="mean",
        )
        st.dataframe(
            compare.style.format("{:.0f}"),
            width="stretch",
        )

        winner = (
            second.sort_values(
                ["duel", "score"],
                ascending=[True, False],
            )
            .groupby("duel", as_index=False)
            .first()[["duel", "candidat", "score"]]
        )
        st.subheader("Vainqueur mesuré dans chaque duel")
        st.dataframe(winner, width="stretch", hide_index=True)

    with tabs[2]:
        st.dataframe(second, width="stretch", hide_index=True)
        st.download_button(
            "Télécharger les données du second tour",
            second.to_csv(index=False).encode("utf-8-sig"),
            "second_tour_2027.csv",
            "text/csv",
        )

    with tabs[3]:
        st.markdown(
            """
            Les résultats de second tour proviennent de questions distinctes.
            Ils ne doivent pas être dérivés des scores du premier tour.

            Les pourcentages sont calculés parmi les suffrages exprimés.
            La proportion de personnes sans opinion est affichée séparément.
            """
        )

else:
    with st.sidebar:
        st.title("Familles et reports")
        st.caption(
            "Cette section utilise uniquement des données fictives "
            "pour tester la présentation."
        )

    st.warning(
        "Démonstration uniquement : les chiffres ci-dessous sont fictifs. "
        "Ils ne décrivent pas le comportement réel des électeurs."
    )

    demo_tabs = st.tabs(
        [
            "Reports de voix",
            "Leaders vs électeurs",
            "Données de démonstration",
        ]
    )

    with demo_tabs[0]:
        st.subheader("Reports simulés par famille politique")
        st.caption(
            "Lecture : chaque ligne totalise 100 %. "
            "Elle indique la répartition simulée au second tour."
        )

        st.dataframe(
            reports,
            width="stretch",
            hide_index=True,
        )

        selected_family = st.selectbox(
            "Famille politique à visualiser",
            reports["famille_premier_tour"].tolist(),
        )
        row = reports[
            reports["famille_premier_tour"] == selected_family
        ].iloc[0]

        simple_chart = pd.DataFrame(
            {
                "destination": ["Philippe", "Le Pen", "Abstention"],
                "pourcentage": [
                    row["Philippe"],
                    row["Le Pen"],
                    row["Abstention"],
                ],
            }
        )

        fig_demo = px.bar(
            simple_chart,
            x="destination",
            y="pourcentage",
            text="pourcentage",
            labels={
                "destination": "",
                "pourcentage": "Part simulée (%)",
            },
        )
        fig_demo.update_traces(texttemplate="%{text:.0f} %", textposition="outside")
        fig_demo.update_yaxes(range=[0, 100])
        fig_demo.update_layout(height=430, showlegend=False)
        st.plotly_chart(fig_demo, width="stretch")

    with demo_tabs[1]:
        st.subheader("Position du leader et comportement simulé")
        st.dataframe(
            leaders,
            width="stretch",
            hide_index=True,
        )

        leader_chart = leaders[
            ["famille", "part_suivant_le_candidat_soutenu"]
        ].sort_values("part_suivant_le_candidat_soutenu")

        fig_leaders = px.bar(
            leader_chart,
            x="part_suivant_le_candidat_soutenu",
            y="famille",
            orientation="h",
            text=leader_chart["part_suivant_le_candidat_soutenu"].map(
                lambda value: f"{value:.0f} %"
            ),
            labels={
                "part_suivant_le_candidat_soutenu":
                    "Part suivant le candidat soutenu (%)",
                "famille": "",
            },
        )
        fig_leaders.update_traces(textposition="outside", cliponaxis=False)
        fig_leaders.update_xaxes(range=[0, 100])
        fig_leaders.update_layout(height=430, showlegend=False)
        st.plotly_chart(fig_leaders, width="stretch")

    with demo_tabs[2]:
        st.download_button(
            "Télécharger les reports fictifs",
            reports.to_csv(index=False).encode("utf-8-sig"),
            "reports_demo.csv",
            "text/csv",
        )
        st.download_button(
            "Télécharger les données leaders fictives",
            leaders.to_csv(index=False).encode("utf-8-sig"),
            "leaders_demo.csv",
            "text/csv",
        )

st.divider()

with st.expander("Sources et journal des changements"):
    log = changes.sort_values("date", ascending=False).copy()
    log["date"] = log["date"].dt.strftime("%d/%m/%Y")
    st.dataframe(log, width="stretch", hide_index=True)

    st.markdown(
        "Source Ifop juillet 2026 : "
        "[notice officielle de la Commission des sondages]"
        "(https://www.commission-des-sondages.fr/notices/medias/fichiers/add/2227)"
    )
