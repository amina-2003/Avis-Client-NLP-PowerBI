"""Applique les modeles ML ENTRAINES (output/models/*.joblib) a de NOUVEAUX avis, sans reentrainer.
Usage : python src/score_new_reviews.py avis.csv --col texte [--out avis_scores.csv]
Le CSV d'entree doit contenir une colonne de texte ; une colonne 'id' est ajoutee si absente.
Sortie : une ligne par avis (Sentiment, Score, ThemePrincipal) + <out>_phrases.csv (une ligne par phrase).
Rappel : les modeles ont ete entraines sur des avis SYNTHETIQUES en francais ; sur de vrais avis, reevaluer avant usage."""
import argparse, joblib
import numpy as np, pandas as pd
from common import MODELS
from nlp_core import split_sentences
from ml_models import SentimentML, ThemeML

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("--col", default="texte"); ap.add_argument("--out", default="avis_scores.csv")
    a = ap.parse_args()
    df = pd.read_csv(a.input);  df = df.assign(id=df.get("id", range(1, len(df) + 1)))
    sent, theme, cfg = joblib.load(MODELS / "sentiment_ml.joblib"), joblib.load(MODELS / "theme_ml.joblib"), joblib.load(MODELS / "config.joblib")
    rows = [(r.id, k, s) for r in df.itertuples() for k, s in enumerate(split_sentences(getattr(r, a.col)), 1)]
    sd = pd.DataFrame(rows, columns=["id", "SentenceNo", "SentenceText"])
    sd["Score"] = sent.score(sd.SentenceText); sd["Sentiment"] = sent.predict(sd.SentenceText); sd["Theme"] = theme.predict(sd.SentenceText)
    t = cfg["seuil_sentiment_avis"] if cfg["engine"] == "ml" else 0.15
    rv = sd.groupby("id").Score.mean().rename("Score").reset_index()
    rv["Sentiment"] = np.where(rv.Score > t, "pos", np.where(rv.Score < -t, "neg", "neu"))
    mt = sd[sd.Theme != "Général"].groupby("id").apply(lambda g: g.loc[g.Score.abs().idxmax(), "Theme"]).rename("ThemePrincipal").reset_index()
    out = df.merge(rv, on="id").merge(mt, on="id", how="left").fillna({"ThemePrincipal": "Général"})
    out.to_csv(a.out, index=False, encoding="utf-8-sig"); sd.to_csv(a.out.replace(".csv", "_phrases.csv"), index=False, encoding="utf-8-sig")
    print(out[["id", "Sentiment", "Score", "ThemePrincipal"]].to_string(index=False))

if __name__ == "__main__":
    main()
