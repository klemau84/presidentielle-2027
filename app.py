
from pathlib import Path
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
df = pd.read_csv(BASE / "sondages.csv", parse_dates=["publication","terrain_start","terrain_end"])
changes = pd.read_csv(BASE / "changelog.csv", parse_dates=["date"])

# ---------- Style ----------
st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px;}
[data-testid="stMetric"] {
    background: rgba(127,127,127,.08);
    border: 1px solid rgba(127,127,127,.18);
    padding: 14px 18px;
    border-radius: 14px;
}
.small-note {opacity:.72; font-size:.9rem;}
.source-box {
    padding: 12px 14px; border-radius: 12px;
    border: 1px solid rgba(127,127,127,.2);
    background: rgba(127,127,127,.06);
}
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def normalize_candidate(name: str) -> str:
    replacements = {
        "Marine Le Pen / Jordan Bardella": "Candidat RN",
        "Marine Le Pen": "Candidat RN",
        "Jordan Bardella": "Candidat RN",
    }
    return replacements.get(name, name)

df["candidat_normalise"] = df["candidat"].map(normalize_candidate)
df["poids"] = pd.to_numeric(df["echantillon_exprimes"], errors="coerce").fillna(1000).pow(0.5)

def weighted_average(frame):
    return (
        frame.groupby("candidat_normalise", as_index=False)
        .apply(lambda g: pd.Series({
            "score": np.average(g["score"], weights=g["poids"]),
            "n_mesures": g["scenario_id"].nunique(),
            "dernier": g["terrain_end"].max()
        }), include_groups=False)
        .reset_index(drop=True)
        .sort_values("score", ascending=False)
    )

# ---------- Sidebar ----------
with st.sidebar:
    st.title("Filtres")
    family = st.radio("Hypothèse centrale", ["Édouard Philippe", "Gabriel Attal"], index=0)
    scenario_text = f"{family} candidat du centre"
    institutes = st.multiselect(
        "Instituts",
        sorted(df["institut"].unique()),
        default=sorted(df["institut"].unique()),
    )
    uncertainty = st.slider("Incertitude de simulation (points)", 0.5, 4.0, 2.0, 0.1)
    simulations = st.slider("Nombre de simulations", 5_000, 100_000, 30_000, 5_000)
    st.divider()
    st.caption("Les scénarios de candidatures ne sont pas interchangeables. Les données Ifop de juillet sont partielles tant que le tableau détaillé n'est pas intégré.")

view = df[(df["scenario"] == scenario_text) & (df["institut"].isin(institutes))].copy()
latest_date = view["terrain_end"].max()
latest = view[view["terrain_end"] == latest_date].sort_values("score", ascending=False)
avg = weighted_average(view)

# ---------- Header ----------
st.title("Présidentielle 2027 — observatoire des sondages")
st.markdown(
    f"<div class='small-note'>Dernière donnée intégrée : <b>{latest_date:%d/%m/%Y}</b> · "
    f"Hypothèse : <b>{scenario_text}</b></div>",
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Instituts", view["institut"].nunique())
m2.metric("Vagues", view["poll_id"].nunique())
leader = latest.iloc[0]
m3.metric("Premier du dernier sondage", leader["candidat"], f"{leader['score']:.1f} %")
runner = latest.iloc[1]
m4.metric("Deuxième du dernier sondage", runner["candidat"], f"{runner['score']:.1f} %")

tab_overview, tab_trend, tab_scenarios, tab_sources = st.tabs(
    ["Vue d'ensemble", "Évolution", "Scénarios", "Sources et changements"]
)

# ---------- Overview ----------
with tab_overview:
    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("Moyenne des vagues disponibles")
        fig = px.bar(
            avg.sort_values("score"),
            x="score", y="candidat_normalise", orientation="h",
            text=avg.sort_values("score")["score"].map(lambda x: f"{x:.1f} %"),
            labels={"score":"Score moyen pondéré (%)", "candidat_normalise":""},
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(height=510, margin=dict(l=10,r=45,t=10,b=30), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Qualification simulée au second tour")
        means = avg.set_index("candidat_normalise")["score"]
        rng = np.random.default_rng(2027)
        draws = rng.normal(means.to_numpy(), uncertainty, size=(simulations, len(means)))
        draws = np.clip(draws, 0, None)
        top2 = np.argpartition(draws, -2, axis=1)[:, -2:]
        probs = [100 * (top2 == i).any(axis=1).mean() for i in range(len(means))]
        sim = pd.DataFrame({"candidat":means.index, "probabilite":probs}).sort_values("probabilite")
        fig2 = px.bar(
            sim, x="probabilite", y="candidat", orientation="h",
            text=sim["probabilite"].map(lambda x: f"{x:.1f} %"),
            labels={"probabilite":"Probabilité simulée (%)","candidat":""},
        )
        fig2.update_traces(textposition="outside", cliponaxis=False)
        fig2.update_layout(height=510, margin=dict(l=10,r=45,t=10,b=30), showlegend=False)
        fig2.update_xaxes(range=[0,105])
        st.plotly_chart(fig2, use_container_width=True)

    st.info(
        "La simulation mesure la sensibilité du classement à une incertitude choisie. "
        "Elle ne prédit pas le résultat de 2027 et ne modélise pas les évolutions de campagne."
    )

    st.subheader("Dernière vague intégrée")
    display = latest[["institut","terrain_end","candidat","score","couverture"]].copy()
    display["terrain_end"] = display["terrain_end"].dt.strftime("%d/%m/%Y")
    display["score"] = display["score"].map(lambda x: f"{x:.1f} %")
    st.dataframe(display, use_container_width=True, hide_index=True)

# ---------- Trend ----------
with tab_trend:
    st.subheader("Évolution des principaux candidats")
    candidates = (
        view.groupby("candidat_normalise")["score"].max()
        .sort_values(ascending=False).head(6).index.tolist()
    )
    selected = st.multiselect("Candidats affichés", candidates, default=candidates[:4])
    trend = (
        view[view["candidat_normalise"].isin(selected)]
        .groupby(["terrain_end","candidat_normalise"], as_index=False)
        .apply(lambda g: pd.Series({"score": np.average(g["score"], weights=g["poids"])}), include_groups=False)
        .reset_index(drop=True)
    )
    if trend.empty:
        st.warning("Aucune série à afficher.")
    else:
        fig3 = px.line(
            trend, x="terrain_end", y="score", color="candidat_normalise",
            markers=True, labels={"terrain_end":"","score":"Intentions de vote (%)","candidat_normalise":""}
        )
        fig3.update_layout(height=560, legend_title_text="")
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("La série reste courte : les courbes deviendront plus utiles à mesure que de nouvelles vagues seront intégrées.")

# ---------- Scenarios ----------
with tab_scenarios:
    st.subheader("Comparer Philippe et Attal")
    comparable = df[df["institut"].isin(institutes)].copy()
    matrix = comparable.pivot_table(
        index="candidat_normalise", columns="scenario", values="score", aggfunc="mean"
    )
    st.dataframe(matrix.style.format("{:.1f}"), use_container_width=True)
    st.caption("Cette matrice décrit des hypothèses différentes. Un écart entre colonnes n'est pas nécessairement une évolution dans le temps.")

# ---------- Sources ----------
with tab_sources:
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.subheader("Journal des changements")
        log = changes.sort_values("date", ascending=False).copy()
        log["date"] = log["date"].dt.strftime("%d/%m/%Y")
        st.dataframe(log, use_container_width=True, hide_index=True)
    with c2:
        st.subheader("Couverture des données")
        coverage = (
            df.groupby(["poll_id","institut","terrain_end","couverture"], as_index=False)
            .agg(scénarios=("scenario_id","nunique"), lignes=("candidat","count"))
            .sort_values("terrain_end", ascending=False)
        )
        coverage["terrain_end"] = coverage["terrain_end"].dt.strftime("%d/%m/%Y")
        st.dataframe(coverage, use_container_width=True, hide_index=True)

    st.subheader("Liens vers les sources")
    sources = (
        df[["institut","commanditaire","poll_id","source_url"]]
        .drop_duplicates()
        .sort_values("poll_id", ascending=False)
    )
    for _, row in sources.iterrows():
        st.markdown(
            f"<div class='source-box'><b>{row['institut']}</b> — {row['commanditaire']}<br>"
            f"<a href='{row['source_url']}' target='_blank'>Ouvrir la source</a></div><br>",
            unsafe_allow_html=True,
        )
