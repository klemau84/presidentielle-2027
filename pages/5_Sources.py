
import streamlit as st
from utils.data import load_polls, load_changelog
from utils.ui import apply_style

st.set_page_config(page_title="Sources — Présidentielle 2027", layout="wide")
apply_style()
df = load_polls()
changes = load_changelog()

st.title("Sources et changements")
left, right = st.columns([1.1, 1])

with left:
    st.subheader("Journal des changements")
    log = changes.sort_values("date", ascending=False).copy()
    log["date"] = log["date"].dt.strftime("%d/%m/%Y")
    st.dataframe(log, use_container_width=True, hide_index=True)

with right:
    st.subheader("Couverture des vagues")
    coverage = (
        df.groupby(["poll_id","institut","terrain_end","couverture"], as_index=False)
        .agg(scenarios=("scenario_id","nunique"), lignes=("candidat","count"))
        .sort_values("terrain_end", ascending=False)
    )
    coverage["terrain_end"] = coverage["terrain_end"].dt.strftime("%d/%m/%Y")
    st.dataframe(coverage, use_container_width=True, hide_index=True)

st.subheader("Liens officiels")
sources = df[["institut","commanditaire","poll_id","source_url"]].drop_duplicates()
for _, row in sources.iterrows():
    st.markdown(
        f"**{row['institut']} — {row['commanditaire']}**  \n"
        f"[Ouvrir la source]({row['source_url']})"
    )
