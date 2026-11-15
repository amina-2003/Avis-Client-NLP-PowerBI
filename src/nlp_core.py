"""Briques NLP : segmentation, sentiment par lexique, themes par lexique, evaluation."""
import re
import numpy as np
from common import norm, THEMES
from lexicons import *

SPLIT_RE = re.compile(r"(?<=[.!?;])\s+")
def split_sentences(text: str):
    return [s.strip() for s in SPLIT_RE.split(str(text).strip()) if s.strip()]

def _n(s):
    """norm + traitement des elisions (l'assistance -> l assistance)"""
    return norm(s).replace("'", " ")
_NEUTRAL = [m.replace("'", " ") for m in NEUTRAL_MARKERS]

# ---------------- sentiment lexique ----------------
def lexicon_score(sentence: str) -> float:
    """Score dans [-1, 1]. Negation : inverse le mot de polarite dans une fenetre de 3 mots."""
    n = _n(sentence); toks = n.split(); score = 0.0; flipped_any = False; neg_left = 0; had_neg_word = False
    for t in toks:
        if t in NEGATORS: neg_left = 3; had_neg_word = True; continue
        p = 1 if t in POS else -1 if t in NEG else 0
        if p:
            if neg_left > 0: p = -p; flipped_any = True
            score += p
        neg_left = max(0, neg_left - 1)
    if had_neg_word and not flipped_any and "jamais" in toks: score -= 1
    if any(m in n for m in _NEUTRAL): score *= 0.3
    return float(np.tanh(score / 1.5))

def lexicon_label(score, t=0.3): return "pos" if score > t else "neg" if score < -t else "neu"

# ---------------- themes lexique ----------------
def _build_theme_matchers():
    ms = {}
    for th, ws in THEME_WORDS.items():
        exact = {w for w in ws if not w.endswith("*") and " " not in w and "-" not in w}
        pref = tuple(w[:-1] for w in ws if w.endswith("*"))
        phr = [w.replace("-", " ") for w in ws if " " in w or "-" in w]
        ms[th] = (exact, pref, phr)
    return ms
_M = _build_theme_matchers()

def theme_scores(sentence: str):
    n = _n(sentence); toks = n.split(); out = {}
    for th, (exact, pref, phr) in _M.items():
        c = sum(1 for t in toks if t in exact or (pref and t.startswith(pref))) + sum(1 for p in phr if p in n)
        if c: out[th] = c
    return out

def lexicon_theme(sentence: str) -> str:
    sc = theme_scores(sentence)
    if not sc: return "Général"
    best = max(sc.values())
    tied = [t for t in sc if sc[t] == best]
    return sorted(tied, key=THEME_PRIORITY.index)[0]
