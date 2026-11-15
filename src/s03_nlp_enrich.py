"""Etape 3 - Enrichissement NLP : sentiment (phrase -> avis) et themes, avec evaluation.
Trois moteurs compares :
  lexique     : regles (lexique FR + negations), explicable
  ml_tfidf    : TF-IDF + regression logistique seul (reference : echoue hors des formulations vues)
  ml          : regression logistique entrainee sur indicateurs lexicaux (+ TF-IDF pour les themes)  <- ENGINE='ml'
Entrainement : phrases des avis 'train'. Evaluation : formulations 'test' (jamais vues) + jeu 'stress' ecrit a la main.
Le moteur qui alimente Power BI est choisi par common.ENGINE.
"""
import json
import numpy as np, pandas as pd
import joblib
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix
from common import *
from nlp_core import *
from ml_models import SentimentML, ThemeML, TfidfBaseline, ReviewML
from stress_set import STRESS

LAB3 = ["neg", "neu", "pos"]
SENT_NAME = {"lexique": "Lexique (règles)", "ml": "ML (régression logistique)"}

def rep(y, p, labels):
    return dict(accuracy=round(accuracy_score(y, p), 3), macro_f1=round(f1_score(y, p, labels=labels, average="macro"), 3), n=int(len(y)))

def lab(sc, t): return np.where(sc > t, "pos", np.where(sc < -t, "neg", "neu"))

def tune(scores, y):
    best = (-1, 0.2)
    for t in np.arange(0.05, 0.6, 0.025):
        best = max(best, (f1_score(y, lab(scores, t), labels=LAB3, average="macro"), round(float(t), 3)))
    return best[1]

def main():
    assert ENGINE in ("ml", "lexique")
    rv = pd.read_csv(OUT / "reviews_raw.csv"); tr = pd.read_csv(OUT / "reviews_truth.csv")
    st = pd.read_csv(OUT / "sentences_truth.csv").merge(rv[["ReviewID", "PhrasePool"]], on="ReviewID")
    seg = {r.ReviewID: split_sentences(r.ReviewText) for r in rv.itertuples()}
    n_true = st.groupby("ReviewID").size()
    seg_ok = float(np.mean([len(seg[i]) == n_true[i] for i in rv.ReviewID])); assert seg_ok > 0.98, seg_ok

    trn, tst = st[st.PhrasePool == "train"], st[st.PhrasePool == "test"]
    stress = pd.DataFrame(STRESS, columns=["SentenceText", "PolarityTrue", "ThemeTrue"])
    metrics = dict(segmentation_match_rate=round(seg_ok, 4), n_train_sentences=len(trn), n_test_sentences=len(tst), n_stress=len(stress), engine=ENGINE)

    # ---------- entrainement ----------
    base_s = TfidfBaseline().fit(trn.SentenceText, trn.PolarityTrue); base_t = TfidfBaseline().fit(trn.SentenceText, trn.ThemeTrue)
    sent = SentimentML().fit(trn.SentenceText, trn.PolarityTrue); theme = ThemeML().fit(trn.SentenceText, trn.ThemeTrue)
    MODELS.mkdir(parents=True, exist_ok=True); joblib.dump(sent, MODELS / "sentiment_ml.joblib"); joblib.dump(theme, MODELS / "theme_ml.joblib")

    # ---------- evaluation phrase ----------
    for name, d in [("test", tst), ("stress", stress)]:
        lexs = [lexicon_label(lexicon_score(s)) for s in d.SentenceText]
        metrics[f"sentiment_phrase_{name}"] = dict(lexique=rep(d.PolarityTrue, lexs, LAB3), ml_tfidf=rep(d.PolarityTrue, base_s.predict(d.SentenceText), LAB3),
                                                    ml=rep(d.PolarityTrue, sent.predict(d.SentenceText), LAB3))
        lext = [lexicon_theme(s) for s in d.SentenceText]
        metrics[f"theme_phrase_{name}"] = dict(lexique=rep(d.ThemeTrue, lext, THEMES), ml_tfidf=rep(d.ThemeTrue, base_t.predict(d.SentenceText), THEMES),
                                                ml=rep(d.ThemeTrue, theme.predict(d.SentenceText), THEMES))
    # sens inverse (entrainement sur 'test', evaluation sur 'train') : controle de stabilite
    s_rev = SentimentML().fit(tst.SentenceText, tst.PolarityTrue); t_rev = ThemeML().fit(tst.SentenceText, tst.ThemeTrue)
    metrics["controle_sens_inverse"] = dict(sentiment_phrase=rep(trn.PolarityTrue, s_rev.predict(trn.SentenceText), LAB3), theme_phrase=rep(trn.ThemeTrue, t_rev.predict(trn.SentenceText), THEMES))

    # ---------- toutes les phrases a scorer ----------
    sd = pd.DataFrame([(r.ReviewID, k, s) for r in rv.itertuples() for k, s in enumerate(seg[r.ReviewID], 1)], columns=["ReviewID", "SentenceNo", "SentenceText"])
    sd["ScoreLexique"] = [lexicon_score(s) for s in sd.SentenceText]; sd["ScoreML"] = sent.score(sd.SentenceText)
    sd["ScoreTfidf"] = (lambda p: (p["pos"] - p["neg"]).values)(base_s.proba(sd.SentenceText))
    sd["ThemeLexique"] = [lexicon_theme(s) for s in sd.SentenceText]; sd["ThemeML"] = theme.predict(sd.SentenceText)
    sd["SentLexique"] = [lexicon_label(x) for x in sd.ScoreLexique]; sd["SentML"] = sent.predict(sd.SentenceText)

    # ---------- avis : agregation des phrases ----------
    y = tr.set_index("ReviewID").SentimentTrue.loc[rv.ReviewID].values
    is_tr, is_te = (rv.PhrasePool == "train").values, (rv.PhrasePool == "test").values
    res, rscore, rpred = {}, {}, {}
    for eng, col in [("lexique", "ScoreLexique"), ("ml_tfidf", "ScoreTfidf"), ("ml", "ScoreML")]:
        sc = sd.groupby("ReviewID")[col].mean().loc[rv.ReviewID].values
        t = tune(sc[is_tr], y[is_tr]); pr = lab(sc, t); rscore[eng], rpred[eng] = sc, pr
        res[eng] = dict(seuil=t, train=rep(y[is_tr], pr[is_tr], LAB3), test=rep(y[is_te], pr[is_te], LAB3),
                        confusion_test=confusion_matrix(y[is_te], pr[is_te], labels=LAB3).tolist())
    # --- ML de 2e niveau (avis) : entraine sur les avis 'train' uniquement
    F = ReviewML.features(sent, sd).loc[rv.ReviewID]
    rml = ReviewML().fit(F[is_tr], y[is_tr]); pr2 = rml.predict(F); sc2 = rml.score(F)
    rscore["ml_2niveaux"], rpred["ml_2niveaux"] = sc2, pr2
    res["ml_2niveaux"] = dict(train=rep(y[is_tr], pr2[is_tr], LAB3), test=rep(y[is_te], pr2[is_te], LAB3),
                              confusion_test=confusion_matrix(y[is_te], pr2[is_te], labels=LAB3).tolist())
    ceil_sc = st.assign(v=st.PolarityTrue.map({"pos": 1, "neu": 0, "neg": -1})).groupby("ReviewID").v.mean().loc[rv.ReviewID].values
    tc = tune(ceil_sc, y); res["plafond_theorique"] = dict(accuracy=round(accuracy_score(y, lab(ceil_sc, tc)), 3), note="polarites de phrases parfaites -> bruit de la note")
    metrics["sentiment_avis"] = res; metrics["labels"] = LAB3

    # ---------- moteur de production ----------
    eng = ENGINE; t_eng = res[eng].get("seuil")
    avis_key = eng      # variante simple retenue sur le jeu d'entrainement ; le modele a 2 niveaux est consigne dans metrics.json (essai non retenu)
    sd["Theme"] = sd["ThemeML"] if eng == "ml" else sd["ThemeLexique"]
    sd["SentimentScore"] = (sd.ScoreML if eng == "ml" else sd.ScoreLexique).round(4)
    sd["Sentiment"] = sd["SentML"] if eng == "ml" else sd["SentLexique"]
    ss_df = sd[["ReviewID", "SentenceNo", "SentenceText", "Theme", "SentimentScore", "Sentiment", "ThemeLexique", "ScoreLexique", "SentLexique"]].copy()
    ss_df["ScoreLexique"] = ss_df.ScoreLexique.round(4)

    def main_theme(g):
        g2 = g[g.Theme != "Général"]
        return "Général" if g2.empty else g2.loc[g2.SentimentScore.abs().idxmax(), "Theme"]
    mt = ss_df.groupby("ReviewID").apply(main_theme).rename("MainTheme").reset_index()
    out = rv.assign(SentimentPred=rpred[avis_key], SentimentScore=np.round(rscore[avis_key], 4), SentimentLexique=rpred["lexique"],
                    SentimentScoreLexique=np.round(rscore["lexique"], 4), Moteur=SENT_NAME[eng]).merge(mt, on="ReviewID")
    out["NbSentences"] = out.ReviewID.map(ss_df.groupby("ReviewID").size())
    out.to_csv(OUT / "reviews_scored.csv", index=False, encoding="utf-8-sig"); ss_df.to_csv(OUT / "sentences_scored.csv", index=False, encoding="utf-8-sig")
    joblib.dump(dict(seuil_sentiment_avis=t_eng, engine=eng), MODELS / "config.joblib")
    json.dump(metrics, open(OUT / "metrics.json", "w"), ensure_ascii=False, indent=2)
    stress.assign(lex_sent=[lexicon_label(lexicon_score(s)) for s in stress.SentenceText], ml_sent=sent.predict(stress.SentenceText),
                  lex_theme=[lexicon_theme(s) for s in stress.SentenceText], ml_theme=theme.predict(stress.SentenceText)
                  ).to_csv(OUT / "stress_results.csv", index=False, encoding="utf-8-sig")
    print(json.dumps({k: v for k, v in metrics.items() if k != "labels"}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
