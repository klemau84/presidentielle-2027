
# Observatoire des sondages — Présidentielle 2027

## Lancement

```bash
python -m venv .venv
source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Ce que montre le prototype

- sélection d'un scénario de candidatures ;
- histogramme des intentions de vote ;
- simulation de qualification au second tour ;
- comparaison matricielle des scénarios ;
- table complète avec liens vers les sources.

## Limites

La simulation est un outil pédagogique, pas une prédiction. Les scénarios ne doivent pas être agrégés
sans méthode de normalisation. Les données incluses sont une amorce issue d'Ipsos bva (terrain du
27 au 28 mai 2026) et d'OpinionWay (terrain du 10 au 11 juin 2026).
