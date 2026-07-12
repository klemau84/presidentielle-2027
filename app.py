
import streamlit as st
from utils.ui import apply_style

st.set_page_config(
    page_title="Présidentielle 2027",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_style()

st.title("Présidentielle 2027 — observatoire des sondages")
st.markdown(
    """
    Cette application suit les intentions de vote publiées pour l'élection présidentielle de 2027.
    Utilise le menu de gauche pour ouvrir les différentes analyses.
    """
)

c1, c2, c3 = st.columns(3)
c1.page_link("pages/1_Accueil.py", label="Vue d'ensemble", icon="📊")
c2.page_link("pages/2_Tendances.py", label="Tendances", icon="📈")
c3.page_link("pages/3_Instituts.py", label="Instituts", icon="🏛️")

c4, c5, c6 = st.columns(3)
c4.page_link("pages/4_Scenarios.py", label="Scénarios", icon="🔀")
c5.page_link("pages/5_Sources.py", label="Sources", icon="🔎")
c6.page_link("pages/6_Methodologie.py", label="Méthodologie", icon="📘")

st.info(
    "Les simulations présentées dans l'application sont pédagogiques. "
    "Elles ne constituent pas une prévision du résultat de 2027."
)
