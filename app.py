
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Présidentielle 2027", page_icon="🗳️", layout="wide")

DATA = Path(__file__).with_name("sondages.csv")
df = pd.read_csv(DATA, parse_dates=["publication","terrain_start","terrain_end"])

st.title("Présidentielle 2027 — observatoire des sondages")
st.caption("Prototype exploratoire. Les scénarios ne sont pas interchangeables et la simulation n'est pas une prévision électorale.")

with st.sidebar:
    st.header("Filtres")
    institutes = st.multiselect("Instituts", sorted(df.institut.unique()), default=sorted(df.institut.unique()))
    scenario = st.selectbox("Scénario", df.sort_values("terrain_end", ascending=False).scenario.drop_duplicates())
    n_sims = st.slider("Simulations", 2_000, 100_000, 20_000, 2_000)
    uncertainty = st.slider("Incertitude par candidat (points)", 0.5, 4.0, 2.0, 0.1)
    st.markdown("---")
    st.caption("Règle : ne comparer que des hypothèses de candidatures proches.")

filtered = df[df.institut.isin(institutes)]
sc = filtered[filtered.scenario == scenario].sort_values("score", ascending=False)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Instituts", filtered.institut.nunique())
c2.metric("Scénarios", filtered.scenario_id.nunique())
c3.metric("Dernier terrain", filtered.terrain_end.max().strftime("%d/%m/%Y"))
c4.metric("Base exprimés", f"{int(sc.echantillon_exprimes.max()):,}".replace(",", " "))

left, right = st.columns([1.15, 1])
with left:
    st.subheader("Rapport de forces du scénario sélectionné")
    fig = px.bar(sc, x="score", y="candidat", orientation="h", text="score",
                 labels={"score":"Intention de vote (%)","candidat":""})
    fig.update_layout(yaxis={"categoryorder":"total ascending"}, height=520)
    fig.update_traces(texttemplate="%{text:.1f} %", textposition="outside", cliponaxis=False)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Probabilité simulée de finir dans les deux premiers")
    rng = np.random.default_rng(2027)
    means = sc.set_index("candidat")["score"]
    draws = rng.normal(means.to_numpy(), uncertainty, size=(n_sims, len(means)))
    draws = np.clip(draws, 0, None)
    top2 = np.argpartition(draws, -2, axis=1)[:, -2:]
    probs = np.zeros(len(means))
    for j in range(len(means)):
        probs[j] = (top2 == j).any(axis=1).mean() * 100
    qualif = pd.DataFrame({"candidat":means.index, "probabilité":probs}).sort_values("probabilité", ascending=False)
    fig2 = px.bar(qualif, x="probabilité", y="candidat", orientation="h",
                  labels={"probabilité":"Qualification simulée (%)","candidat":""})
    fig2.update_layout(yaxis={"categoryorder":"total ascending"}, height=520)
    fig2.update_traces(texttemplate="%{x:.1f} %", textposition="outside", cliponaxis=False)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Comparer les scénarios")
pivot = filtered.pivot_table(index="candidat", columns="scenario", values="score", aggfunc="mean")
st.dataframe(pivot.style.format("{:.1f}").background_gradient(axis=None), use_container_width=True, height=430)

st.subheader("Données sources")
display_cols = ["terrain_start","terrain_end","institut","scenario","candidat","score","echantillon_exprimes","source_url"]
st.dataframe(filtered[display_cols].sort_values(["terrain_end","scenario","score"], ascending=[False,True,False]),
             use_container_width=True, hide_index=True)

with st.expander("Comment lire la simulation"):
    st.write("""
    Chaque score est perturbé aléatoirement autour de la valeur publiée. La simulation mesure uniquement
    la sensibilité du classement à une incertitude choisie par l'utilisateur. Elle ne modélise ni les
    indécis, ni les évolutions de campagne, ni les biais propres aux instituts, ni les corrélations entre candidats.
    """)
