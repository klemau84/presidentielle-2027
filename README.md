# Présidentielle 2027 — V7.6 corrigée

Même contenu électoral que la V7.6.

## Correction définitive du conflit Git
`metadonnees_application.csv` est désormais statique.
Le workflow écrit son état dans `etat_veille.csv`.

GitHub Actions ne commit plus que :
- `sondages_detectes.csv`
- `etat_veille.csv`

L'application fusionne ces informations à la lecture.
Les prochaines mises à jour du dashboard ne devraient donc plus entrer
en conflit avec les commits automatiques du workflow sur le fichier de métadonnées.
