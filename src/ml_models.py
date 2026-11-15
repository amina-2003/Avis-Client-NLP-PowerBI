"""Modeles ML supervises (scikit-learn). Entraines sur des phrases ANNOTEES (verite terrain du generateur).

SentimentML : regression logistique multinomiale (neg / neu / pos) sur des indicateurs numeriques par phrase :
              score lexical, nb de mots positifs, nb de mots negatifs, marqueur neutre, negation, longueur.
              Le modele APPREND les poids et seuils ; le lexique ne fournit que des variables d'entree.
ThemeML     : regression logistique sur [nb de mots-cles par theme] + TF-IDF des mots de la phrase.
              Le TF-IDF permet d'apprendre de nouveaux mots depuis les donnees annotees.
TfidfBaseline : TF-IDF mots+caracteres seul (reference : montre l'echec sans connaissance linguistique).
Essai documente : des vecteurs de mots spaCy (fr_core_news_md) n'ont PAS ameliore le sentiment -> non retenus.
"""
import numpy as np, pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from common import norm
from lexicons import POS, NEG, NEGATORS
from nlp_core import lexicon_score, theme_scores, _n, _NEUTRAL

THEMES4 = ["Prix", "Qualité", "Livraison", "Support"]

def sentiment_features(texts):
    rows = []
    for s in texts:
        n = _n(s); tk = n.split()
        rows.append([lexicon_score(s), sum(t in POS for t in tk), sum(t in NEG for t in tk),
                     float(any(m in n for m in _NEUTRAL)), float(any(t in NEGATORS for t in tk)), len(tk)])
    return np.array(rows, float)

class SentimentML:
    def __init__(self, C=0.5):
        self.sc = StandardScaler(); self.lr = LogisticRegression(C=C, max_iter=5000, class_weight="balanced")
    def fit(self, X, y):
        self.lr.fit(self.sc.fit_transform(sentiment_features(X)), y); return self
    def proba(self, X):
        return pd.DataFrame(self.lr.predict_proba(self.sc.transform(sentiment_features(X))), columns=self.lr.classes_)
    def predict(self, X): return self.lr.predict(self.sc.transform(sentiment_features(X)))
    def score(self, X):
        p = self.proba(X); return (p["pos"] - p["neg"]).values          # dans [-1, 1]

class ThemeML:
    def __init__(self, C=1.0):
        self.tf = TfidfVectorizer(ngram_range=(1, 2), preprocessor=norm, sublinear_tf=True)
        self.lr = LogisticRegression(C=C, max_iter=5000, class_weight="balanced")
    def _m(self, X, fit=False):
        cnt = csr_matrix(np.array([[theme_scores(s).get(t, 0) for t in THEMES4] for s in X], float))
        tf = self.tf.fit_transform(X) if fit else self.tf.transform(X)
        return hstack([cnt, tf]).tocsr()
    def fit(self, X, y): self.lr.fit(self._m(X, True), y); return self
    def predict(self, X): return self.lr.predict(self._m(X))

class TfidfBaseline:
    def __init__(self, C=4.0):
        self.w = TfidfVectorizer(ngram_range=(1, 2), preprocessor=norm, sublinear_tf=True)
        self.c = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), preprocessor=norm, min_df=2, sublinear_tf=True)
        self.lr = LogisticRegression(C=C, max_iter=2000, class_weight="balanced")
    def fit(self, X, y):
        self.lr.fit(hstack([self.w.fit_transform(X), self.c.fit_transform(X)]).tocsr(), y); return self
    def _m(self, X): return hstack([self.w.transform(X), self.c.transform(X)]).tocsr()
    def predict(self, X): return self.lr.predict(self._m(X))
    def proba(self, X): return pd.DataFrame(self.lr.predict_proba(self._m(X)), columns=self.lr.classes_)


class ReviewML:
    """2e niveau : apprend a passer des probabilites de phrases au sentiment de l'AVIS (regression logistique).
    Variables : moyenne des P(neg), P(neu), P(pos) des phrases, score min, score max, nb de phrases."""
    def __init__(self, C=1.0):
        self.lr = LogisticRegression(C=C, max_iter=5000, class_weight="balanced")
    @staticmethod
    def features(sent_model, sentences_df):
        p = sent_model.proba(sentences_df.SentenceText); p["ReviewID"] = sentences_df.ReviewID.values; p["s"] = p["pos"] - p["neg"]
        g = p.groupby("ReviewID", sort=False)
        return pd.DataFrame({"neg": g["neg"].mean(), "neu": g["neu"].mean(), "pos": g["pos"].mean(),
                             "smin": g["s"].min(), "smax": g["s"].max(), "n": g.size()})
    def fit(self, F, y): self.lr.fit(F.values, y); return self
    def predict(self, F): return self.lr.predict(F.values)
    def score(self, F):
        p = pd.DataFrame(self.lr.predict_proba(F.values), columns=self.lr.classes_); return (p["pos"] - p["neg"]).values
