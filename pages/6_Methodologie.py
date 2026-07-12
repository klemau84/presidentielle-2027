
import streamlit as st
from utils.ui import apply_style

st.set_page_config(page_title="Méthodologie — Présidentielle 2027", layout="wide")
apply_style()

st.title("Méthodologie")
st.markdown("""
### Principes

- Une ligne correspond à un candidat dans un scénario de sondage.
- Les scénarios différents ne sont pas fusionnés sans précaution.
- Le poids utilisé dans la moyenne est proportionnel à la racine carrée de la taille d'échantillon.
- Les scores RN sont regroupés sous l'étiquette analytique « Candidat RN » pour certaines vues.
- Les résultats partiels sont signalés comme tels.

### Simulation

La simulation ajoute une perturbation aléatoire autour des scores moyens puis observe les deux premiers.
Elle ne modélise pas :

- les indécis ;
- les corrélations entre candidats ;
- les effets de campagne ;
- les biais propres aux instituts ;
- les retraits ou nouvelles candidatures.

Elle doit donc être lue comme un test de sensibilité, pas comme une probabilité électorale réelle.
""")
