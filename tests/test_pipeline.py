import sys, json, hashlib
from pathlib import Path
import pandas as pd, pytest
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
P = ROOT / "powerbi"; O = ROOT / "output"
rd = lambda n: pd.read_csv(P / f"{n}.csv")

def test_primary_keys_unique():
    for t, k in [("FactSales", "LineID"), ("FactReviews", "ReviewID"), ("DimProduct", "ProductKey"), ("DimReseller", "ResellerKey"),
                 ("DimEmployee", "EmployeeKey"), ("DimSalesTerritory", "SalesTerritoryKey"), ("DimDate", "DateKey"), ("DimTheme", "Theme")]:
        assert rd(t)[k].is_unique, f"{t}.{k} non unique"
    ft = rd("FactReviewThemes"); assert not ft.duplicated(["ReviewID", "SentenceNo"]).any()

@pytest.mark.parametrize("child,col,parent,pcol", [
    ("FactSales", "ProductKey", "DimProduct", "ProductKey"), ("FactSales", "ResellerKey", "DimReseller", "ResellerKey"),
    ("FactSales", "EmployeeKey", "DimEmployee", "EmployeeKey"), ("FactSales", "SalesTerritoryKey", "DimSalesTerritory", "SalesTerritoryKey"),
    ("FactSales", "DateKey", "DimDate", "DateKey"), ("FactReviews", "LineID", "FactSales", "LineID"),
    ("FactReviews", "ReviewDateKey", "DimReviewDate", "DateKey"), ("FactReviewThemes", "ReviewID", "FactReviews", "ReviewID"),
    ("FactReviewThemes", "Theme", "DimTheme", "Theme"), ("FactReviews", "MainTheme", "DimTheme", "Theme"),
    ("Targets", "EmployeeKey", "DimEmployee", "EmployeeKey"), ("Targets", "TargetDateKey", "DimDate", "DateKey")])
def test_referential_integrity(child, col, parent, pcol):
    assert rd(child)[col].isin(rd(parent)[pcol]).all(), f"orphelins {child}.{col}"

def test_reviews_consistency():
    r = rd("FactReviews").merge(rd("FactSales")[["LineID", "OrderDate"]], on="LineID")
    assert (pd.to_datetime(r.ReviewDate) > pd.to_datetime(r.OrderDate)).all(), "avis anterieur a la commande"
    assert r.Rating.between(1, 5).all() and set(r.SentimentLabel) <= {"Positif", "Neutre", "Négatif"}
    assert r.ReviewText.str.len().min() > 10
    assert len(r) > 500

def test_every_review_has_sentences():
    assert set(rd("FactReviews").ReviewID) == set(rd("FactReviewThemes").ReviewID)

def test_nlp_quality_floor():
    m = json.load(open(O / "metrics.json"))
    assert m["segmentation_match_rate"] > 0.98
    assert m["sentiment_phrase_stress"]["lexique"]["macro_f1"] >= 0.70
    assert m["theme_phrase_stress"]["lexique"]["macro_f1"] >= 0.70
    assert m["sentiment_avis"]["lexique"]["test"]["accuracy"] >= 0.60       # plafond theorique ~0.83 (bruit de la note)

def test_planted_effects_recovered():
    v = json.load(open(O / "effects_validation.json"))
    assert v["support_corr_effet_plante_vs_score"] > 0.6
    f, s = v["support_score_faibles_vs_forts"]; assert s > f + 0.3
    n = v["effectifs"]
    # on n'affirme que les effets portes par un effectif suffisant (>= 30 phrases) ; les autres restent indicatifs
    q = v["Qualité (sous-catégories plantées)"]
    assert min(n["Qualité (sous-catégories plantées)|Vélos VTT"], n["Qualité (sous-catégories plantées)|Vélos de route"]) >= 30
    assert q["Vélos VTT"] < v["Qualité autres"] < q["Vélos de route"]
    p = v["Prix par catégorie"]; assert n["Prix par catégorie|Vélos"] >= 30 and p["Vélos"] < p["Composants"]
    l = v["Livraison par groupe territoire"]; assert n["Livraison par groupe territoire|Europe"] >= 30 and l["Europe"] < l["North America"]

def test_eval_pools_present():
    r = pd.read_csv(O / "reviews_scored.csv"); assert set(r.PhrasePool) == {"train", "test"}

def test_reproducibility():
    """Rejouer la generation avec la meme graine doit donner un fichier identique."""
    import s02_generate_reviews as g
    h = lambda: hashlib.md5((O / "reviews_raw.csv").read_bytes()).hexdigest()
    before = h(); g.main(); assert h() == before


# ---------------- moteur ML ----------------
def test_ml_engine_in_production_and_models_saved():
    assert (O / "models" / "sentiment_ml.joblib").exists() and (O / "models" / "theme_ml.joblib").exists()
    assert rd("FactReviews").Moteur.iloc[0].startswith("ML")
    assert {"SentimentLabelLexique", "AccordMLLexique"} <= set(rd("FactReviews").columns)   # comparaison ML / lexique possible

def test_ml_quality_floor_and_beats_tfidf_baseline():
    m = json.load(open(O / "metrics.json"))
    assert m["engine"] == "ml"
    s, t = m["sentiment_phrase_test"], m["theme_phrase_test"]
    assert s["ml"]["accuracy"] >= 0.65 and s["ml"]["accuracy"] > s["ml_tfidf"]["accuracy"] + 0.2
    assert t["ml"]["accuracy"] >= 0.85
    assert m["sentiment_phrase_stress"]["ml"]["accuracy"] >= 0.80 and m["theme_phrase_stress"]["ml"]["accuracy"] >= 0.80
    assert m["sentiment_avis"]["ml"]["test"]["accuracy"] >= 0.50          # plafond theorique ~0.83

def test_trained_model_scores_new_text():
    import joblib; from nlp_core import split_sentences
    sent = joblib.load(O / "models" / "sentiment_ml.joblib"); theme = joblib.load(O / "models" / "theme_ml.joblib")
    s = split_sentences("Livraison rapide et soignée. Le service client ne répond jamais à nos mails.")
    assert list(sent.predict(s)) == ["pos", "neg"] and list(theme.predict(s)) == ["Livraison", "Support"]
