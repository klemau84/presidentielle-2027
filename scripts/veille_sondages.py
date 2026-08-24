
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote_plus
import hashlib
import pandas as pd
import requests
import feedparser

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/"sondages_detectes.csv"
STATE=BASE/"metadonnees_application.csv"
queries=[
    'présidentielle 2027 sondage Ifop',
    'présidentielle 2027 sondage Elabe',
    'présidentielle 2027 sondage Harris Interactive',
    'présidentielle 2027 sondage OpinionWay',
    'présidentielle 2027 sondage Ipsos',
    'présidentielle 2027 sondage Verian',
    'présidentielle 2027 sondage Odoxa',
]
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
old=pd.read_csv(OUT).fillna("") if OUT.exists() else pd.DataFrame()
known=set(old["url"]) if not old.empty else set()
rows=[]
for q in queries:
    rss="https://news.google.com/rss/search?q="+quote_plus(q)+"&hl=fr&gl=FR&ceid=FR:fr"
    feed=feedparser.parse(rss)
    for e in feed.entries[:12]:
        link=getattr(e,"link","")
        title=getattr(e,"title","")
        if link and link not in known:
            rows.append({
                "date_detection_utc":now,"titre":title,"source":"Google News RSS",
                "url":link,"statut":"À vérifier",
                "motif":"Nouveau résultat de veille présidentielle 2027"
            })
            known.add(link)
new=pd.DataFrame(rows)
merged=pd.concat([new,old],ignore_index=True) if not old.empty else new
if merged.empty:
    merged=pd.DataFrame(columns=["date_detection_utc","titre","source","url","statut","motif"])
merged.to_csv(OUT,index=False,encoding="utf-8-sig")
meta=pd.read_csv(STATE)
updates={"dernier_balayage_utc":now,"derniers_signaux_detectes":str(len(new))}
for k,v in updates.items():
    if k in set(meta["cle"]):
        meta.loc[meta["cle"]==k,"valeur"]=v
    else:
        meta.loc[len(meta)]=[k,v]
meta.to_csv(STATE,index=False,encoding="utf-8-sig")
print(f"{len(new)} nouveaux signaux détectés")
