
import numpy as np
import plotly.express as px
import streamlit as st
from utils.data import load_polls, scenario_name
from utils.ui import apply_style, sidebar_filters

st.set_page_config(page_title="Tendances — Présidentielle 2027", layout="wide")
apply_style()
df = load_polls()
center, institutes = sidebar_filters(df)
view = df[(df["scenario"] == scenario_name(center)) & (df["institut"].isin(institutes))].copy()

st.title("Tendances")
candidates = (
    view.groupby("candidat_normalise")["score"].max()
    .sort_values(ascending=False).head(8).index.tolist()
)
selected = st.multiselect("Candidats affichés", candidates, default=candidates[:4])

rows = []
for (day, candidate), group in view[view["candidat_normalise"].isin(selected)].groupby(
    ["terrain_end","candidat_normalise"]
):
    rows.append({
        "terrain_end": day,
        "candidat_normalise": candidate,
        "score": np.average(group["score"], weights=group["poids"])
    })

if not rows:
    st.warning("Aucune série disponible.")
else:
    import pandas as pd
    trend = pd.DataFrame(rows)
    fig = px.line(
        trend, x="terrain_end", y="score", color="candidat_normalise",
        markers=True,
        labels={"terrain_end":"", "score":"Intentions de vote (%)", "candidat_normalise":""}
    )
    fig.update_layout(height=620, legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("La série est encore courte. Sa valeur augmentera avec l'ajout de nouvelles vagues.")
