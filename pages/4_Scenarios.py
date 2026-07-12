
import streamlit as st
from utils.data import load_polls
from utils.ui import apply_style

st.set_page_config(page_title="Scénarios — Présidentielle 2027", layout="wide")
apply_style()
df = load_polls()

st.title("Comparer les scénarios")
institutes = st.multiselect(
    "Instituts",
    sorted(df["institut"].unique()),
    default=sorted(df["institut"].unique())
)
view = df[df["institut"].isin(institutes)]
matrix = view.pivot_table(
    index="candidat_normalise",
    columns="scenario",
    values="score",
    aggfunc="mean"
)
st.dataframe(matrix.style.format("{:.1f}"), use_container_width=True)
st.info(
    "Comparer deux colonnes revient à comparer deux hypothèses de candidatures. "
    "Ce n'est pas nécessairement une évolution dans le temps."
)
