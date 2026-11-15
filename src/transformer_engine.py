"""MOTEUR OPTIONNEL (NON EXECUTE NI TESTE ICI) : sentiment par modele pre-entraine multilingue.
L'environnement de developpement n'avait pas acces a huggingface.co ; ce fichier documente la voie d'evolution
recommandee pour de VRAIS avis. Prerequis : pip install transformers torch ; acces Internet au premier lancement.
Le modele renvoie 1 a 5 etoiles -> converti en score [-1, 1] puis en pos/neu/neg comme le moteur lexical.
Evaluation a refaire avec le meme protocole (jeu 'test' + jeu 'stress') avant toute adoption."""
from transformers import pipeline

_clf = None
def sentiment_score(texts):
    global _clf
    if _clf is None:
        _clf = pipeline("text-classification", model="nlptown/bert-base-multilingual-uncased-sentiment", top_k=None)
    out = []
    for res in _clf(list(texts), truncation=True):
        p = {int(r["label"][0]): r["score"] for r in res}          # '4 stars' -> 4
        out.append(sum((k - 3) / 2 * v for k, v in p.items()))        # esperance ramenee dans [-1, 1]
    return out
