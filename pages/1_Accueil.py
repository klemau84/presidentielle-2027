
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from utils.data import load_polls, weighted_average, scenario_name
from utils.ui import apply_style, sidebar_filters

st.set_page_config(page_title="Accueil — Présidentielle 2027", layout="wide")
apply_style()
df = load_polls()
center, institutes = sidebar_filters(df)
scenario = scenario_name(center)
view = df[(df["scenario"] == scenario) & (df["institut"].isin(institutes))].copy()

st.title("Vue d'ensemble")
if view.empty:
    st.warning("Aucune donnée ne correspond aux filtres.")
    st.stop()

latest_date = view["terrain_end"].max()
latest = view[view["terrain_end"] == latest_date].sort_values("score", ascending=False)
avg = weighted_average(view)

st.caption(f"Dernière donnée intégrée : {latest_date:%d/%m/%Y} · {scenario}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Instituts", view["institut"].nunique())
m2.metric("Vagues", view["poll_id"].nunique())
m3.metric("Premier", latest.iloc[0]["candidat"], f"{latest.iloc[0]['score']:.1f} %")
m4.metric("Deuxième", latest.iloc[1]["candidat"], f"{latest.iloc[1]['score']:.1f} %")

left, right = st.columns([1.15, 1])
with left:
    st.subheader("Moyenne pondérée")
    chart_df = avg.sort_values("score")
    fig = px.bar(
        chart_df, x="score", y="candidat_normalise", orientation="h",
        text=chart_df["score"].map(lambda x: f"{x:.1f} %"),
        labels={"score":"Score moyen (%)", "candidat_normalise":""}
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(height=520, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Qualification simulée")
    uncertainty = st.slider("Incertitude (points)", 0.5, 4.0, 2.0, 0.1)
    simulations = st.slider("Simulations", 5_000, 100_000, 30_000, 5_000)
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
        labels={"probabilite":"Probabilité simulée (%)", "candidat":""}
    )
    fig2.update_traces(textposition="outside", cliponaxis=False)
    fig2.update_xaxes(range=[0,105])
    fig2.update_layout(height=520, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Dernière vague")
display = latest[["institut","terrain_end","candidat","score","couverture"]].copy()
display["terrain_end"] = display["terrain_end"].dt.strftime("%d/%m/%Y")
display["score"] = display["score"].map(lambda x: f"{x:.1f} %")
st.dataframe(display, use_container_width=True, hide_index=True)
