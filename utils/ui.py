
import streamlit as st

def apply_style() -> None:
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

def sidebar_filters(df):
    with st.sidebar:
        st.title("Filtres")
        center = st.radio("Hypothèse centrale", ["Édouard Philippe", "Gabriel Attal"])
        institutes = st.multiselect(
            "Instituts",
            sorted(df["institut"].dropna().unique()),
            default=sorted(df["institut"].dropna().unique()),
        )
        st.divider()
        st.caption(
            "Les scénarios ne sont pas interchangeables. "
            "Les données Ifop de juillet restent partielles."
        )
    return center, institutes
