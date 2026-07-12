
import plotly.express as px
import streamlit as st
from utils.data import load_polls, scenario_name
from utils.ui import apply_style, sidebar_filters

st.set_page_config(page_title="Instituts — Présidentielle 2027", layout="wide")
apply_style()
df = load_polls()
center, institutes = sidebar_filters(df)
view = df[(df["scenario"] == scenario_name(center)) & (df["institut"].isin(institutes))].copy()

st.title("Analyse par institut")
candidate = st.selectbox(
    "Candidat",
    sorted(view["candidat_normalise"].dropna().unique())
)
cand = view[view["candidat_normalise"] == candidate].copy()

fig = px.scatter(
    cand, x="terrain_end", y="score", color="institut",
    size="poids", hover_data=["commanditaire","couverture"],
    labels={"terrain_end":"", "score":"Score (%)", "institut":"Institut"}
)
fig.update_layout(height=560)
st.plotly_chart(fig, use_container_width=True)

summary = (
    cand.groupby("institut", as_index=False)
    .agg(score_moyen=("score","mean"), mesures=("scenario_id","nunique"), dernier=("terrain_end","max"))
    .sort_values("score_moyen", ascending=False)
)
summary["dernier"] = summary["dernier"].dt.strftime("%d/%m/%Y")
st.dataframe(summary, use_container_width=True, hide_index=True)
