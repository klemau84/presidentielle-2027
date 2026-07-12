
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

    first["score"] = pd.to_numeric(first["score"], errors="coerce")
    first["echantillon_exprimes"] = pd.to_numeric(
        first["echantillon_exprimes"], errors="coerce"
    )
    first["poids"] = first["echantillon_exprimes"].fillna(1000).clip(lower=1).pow(0.5)
    first["candidat_normalise"] = first["candidat"].replace({
        "Marine Le Pen / Jordan Bardella": "Candidat RN",
        "Marine Le Pen": "Candidat RN",
        "Jordan Bardella": "Candidat RN",
    })

    second["score"] = pd.to_numeric(second["score"], errors="coerce")
    return first, second, changes


def weighted_average(frame):
    rows = []
    for candidate, group in frame.groupby("candidat_normalise"):
        rows.append({
            "candidat": candidate,
            "score": np.average(group["score"], weights=group["poids"]),
            "mesures": group["scenario_id"].nunique(),
        })
    return pd.DataFrame(rows).sort_values("score", ascending=False)


def trend_table(frame, candidates):
    rows = []
    subset = frame[frame["candidat_normalise"].isin(candidates)]
    for (day, candidate), group in subset.groupby(["terrain_end", "candidat_normalise"]):
        rows.append({
            "date": day,
            "candidat": candidate,
            "score": np.average(group["score"], weights=group["poids"]),
        })
    return pd.DataFrame(rows)


st.markdown("""
<style>
.block-container {max-width: 1500px; padding-top: 1.3rem; padding-bottom: 3rem;}
[data-testid="stMetric"] {
    background: rgba(127,127,127,.08);
    border: 1px solid rgba(127,127,127,.18);
    border-radius: 14px;
    padding: 14px 18px;
}
.hero-note {opacity:.74; font-size:.92rem; margin-bottom:1rem;}
</style>
""", unsafe_allow_html=True)

first, second, changes = load_data()

st.title("Présidentielle 2027 — observatoire des sondages")

round_choice = st.radio(
    "Tour analysé",
    ["Premier tour", "Second tour"],
    horizontal=True,
)

if round_choice == "Premier tour":
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
            0.5, 4.0, 2.0, 0.1,
        )
        simulations = st.slider(
            "Nombre de simulations",
            5_000, 100_000, 30_000, 5_000,
        )
        st.caption("Les scénarios de candidatures ne sont pas interchangeables.")

    scenario = f"{centre} candidat du centre"
    view = first[
        (first["scenario"] == scenario)
        & (first["institut"].isin(institutes))
    ].copy()

    if view.empty:
        st.warning("Aucune donnée ne correspond aux filtres.")
        st.stop()

    latest_date = view["terrain_end"].max()
    latest = view[view["terrain_end"] == latest_date].sort_values("score", ascending=False)
    average = weighted_average(view)

    st.markdown(
        f"<div class='hero-note'>Dernière donnée : <b>{latest_date:%d/%m/%Y}</b> · "
        f"Hypothèse : <b>{scenario}</b></div>",
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Instituts", view["institut"].nunique())
    m2.metric("Vagues", view["poll_id"].nunique())
    m3.metric("Premier", latest.iloc[0]["candidat"], f"{latest.iloc[0]['score']:.1f} %")
    m4.metric("Deuxième", latest.iloc[1]["candidat"], f"{latest.iloc[1]['score']:.1f} %")

    tabs = st.tabs(["Synthèse", "Évolution", "Instituts", "Scénarios", "Données"])

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
            draws = rng.normal(means.to_numpy(), uncertainty, size=(simulations, len(means)))
            draws = np.clip(draws, 0, None)
            top_two = np.argpartition(draws, -2, axis=1)[:, -2:]
            probabilities = [
                100 * (top_two == i).any(axis=1).mean()
                for i in range(len(means))
            ]
            sim_df = pd.DataFrame({
                "candidat": means.index,
                "probabilite": probabilities,
            }).sort_values("probabilite")

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
            "La qualification affichée est une simulation pédagogique, "
            "pas une intention de vote de second tour."
        )

    with tabs[1]:
        candidates = (
            view.groupby("candidat_normalise")["score"]
            .max().sort_values(ascending=False).head(8).index.tolist()
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

    with tabs[2]:
        candidate = st.selectbox(
            "Candidat analysé",
            sorted(view["candidat_normalise"].dropna().unique()),
        )
        candidate_view = view[view["candidat_normalise"] == candidate]
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

    with tabs[3]:
        comparable = first[first["institut"].isin(institutes)]
        matrix = comparable.pivot_table(
            index="candidat_normalise",
            columns="scenario",
            values="score",
            aggfunc="mean",
        )
        st.dataframe(matrix.style.format("{:.1f}"), use_container_width=True)

    with tabs[4]:
        export = first.sort_values(
            ["terrain_end", "scenario", "score"],
            ascending=[False, True, False],
        )
        st.dataframe(export, use_container_width=True, hide_index=True)
        st.download_button(
            "Télécharger les données du premier tour",
            export.to_csv(index=False).encode("utf-8-sig"),
            "premier_tour_2027.csv",
            "text/csv",
        )

else:
    with st.sidebar:
        st.title("Filtres — Second tour")
        duel = st.selectbox(
            "Duel",
            second["duel"].drop_duplicates().tolist(),
        )
        st.caption(
            "Les valeurs affichées sont des intentions de vote publiées, "
            "pas une simulation issue du premier tour."
        )

    duel_data = second[second["duel"] == duel].copy().sort_values("score", ascending=False)
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
    s3.metric("Écart", f"{duel_data.iloc[0]['score'] - duel_data.iloc[1]['score']:.0f} pts")
    s4.metric("Sans opinion", f"{nsp:.1f} %")

    tabs = st.tabs(["Duel", "Comparer les seconds tours", "Données", "Méthodologie"])

    with tabs[0]:
        fig = px.bar(
            duel_data.sort_values("score"),
            x="score",
            y="candidat",
            orientation="h",
            text=duel_data.sort_values("score")["score"].map(lambda v: f"{v:.0f} %"),
            labels={"score": "Intentions de vote (%)", "candidat": ""},
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_xaxes(range=[0, 100])
        fig.update_layout(height=430, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

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
        st.dataframe(compare.style.format("{:.0f}"), use_container_width=True)

        winner = (
            second.sort_values(["duel", "score"], ascending=[True, False])
            .groupby("duel", as_index=False)
            .first()[["duel", "candidat", "score"]]
        )
        st.subheader("Vainqueur mesuré dans chaque duel")
        st.dataframe(winner, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.dataframe(second, use_container_width=True, hide_index=True)
        st.download_button(
            "Télécharger les données du second tour",
            second.to_csv(index=False).encode("utf-8-sig"),
            "second_tour_2027.csv",
            "text/csv",
        )

    with tabs[3]:
        st.markdown(
            """
            Les résultats de second tour proviennent de questions distinctes posées
            aux mêmes enquêtés. Ils ne doivent pas être dérivés des scores du premier tour.

            **Duels publiés dans la vague Ifop des 7 et 8 juillet 2026 :**

            - Marine Le Pen / Édouard Philippe ;
            - Marine Le Pen / Gabriel Attal ;
            - Marine Le Pen / Jean-Luc Mélenchon.

            Les pourcentages sont calculés parmi les suffrages exprimés. La proportion
            de personnes sans opinion est affichée séparément.
            """
        )

st.divider()

with st.expander("Sources et journal des changements"):
    log = changes.sort_values("date", ascending=False).copy()
    log["date"] = log["date"].dt.strftime("%d/%m/%Y")
    st.dataframe(log, use_container_width=True, hide_index=True)

    st.markdown(
        "Source Ifop juillet 2026 : "
        "[notice officielle de la Commission des sondages]"
        "(https://www.commission-des-sondages.fr/notices/medias/fichiers/add/2227)"
    )
