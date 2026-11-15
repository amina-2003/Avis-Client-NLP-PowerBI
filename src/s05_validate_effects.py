"""Etape 5 - Validation de bout en bout : les effets plantes dans les avis synthetiques sont-ils retrouves
par l'analyse (sentiment predit, agrege comme dans Power BI) ?  Produit output/effects_validation.csv + figure."""
import json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

def main():
    fx = json.load(open(OUT / "planted_effects.json"))
    ss = pd.read_csv(OUT / "sentences_scored.csv"); rv = pd.read_csv(OUT / "reviews_scored.csv")
    fact = pd.read_csv(OUT / "fact_sales.csv"); prod = pd.read_csv(OUT / "dim_product.csv")
    terr = pd.read_csv(OUT / "dim_territory.csv"); emp = pd.read_csv(OUT / "dim_employee.csv")
    d = ss.merge(rv[["ReviewID", "LineID"]], on="ReviewID").merge(
        fact[["LineID", "EmployeeKey", "SalesTerritoryKey", "ProductKey", "ShipDateMissing"]], on="LineID") \
        .merge(prod[["ProductKey", "Sous-catégorie", "Catégorie"]], on="ProductKey").merge(terr[["SalesTerritoryKey", "SalesTerritoryGroup"]], on="SalesTerritoryKey")
    rows = []
    def add(label, theme, groups, planted):
        for g, sub in groups:
            sub = sub[sub.Theme == theme]
            rows.append(dict(test=label, groupe=g, theme=theme, n_phrases=len(sub), fiable=len(sub) >= 30, score_moyen=round(sub.SentimentScore.mean(), 3) if len(sub) else np.nan,
                             effet_plante=planted.get(g, 0)))
    # support par employe (extremes plantes)
    sup = d[d.Theme == "Support"].groupby("EmployeeKey").SentimentScore.agg(["mean", "size"]).reset_index()
    sup["effet_plante"] = sup.EmployeeKey.map(fx["support_bias_by_employee"].__getitem__ if False else (lambda k: fx["support_bias_by_employee"].get(str(k), 0)))
    sup = sup[sup["size"] >= 8]
    for r in sup.itertuples(): rows.append(dict(test="Support par commercial", groupe=int(r.EmployeeKey), theme="Support", n_phrases=int(r.size), score_moyen=round(r.mean, 3), effet_plante=r.effet_plante))
    add("Livraison par groupe territoire", "Livraison", d.groupby("SalesTerritoryGroup"), fx["delivery_bias_by_territory_group"])
    add("Livraison / ShipDate manquante", "Livraison", d.groupby("ShipDateMissing"), {True: fx["delivery_bias_ship_date_missing"], False: 0})
    add("Prix par catégorie", "Prix", d.groupby("Catégorie"), fx["price_bias_by_category"])
    qs = d[d["Sous-catégorie"].isin(list(fx["quality_bias_by_subcategory"]))].groupby("Sous-catégorie")
    add("Qualité (sous-catégories plantées)", "Qualité", qs, fx["quality_bias_by_subcategory"])
    add("Qualité (référence : toutes les autres)", "Qualité", [("autres", d[~d["Sous-catégorie"].isin(list(fx["quality_bias_by_subcategory"]))])], {})
    res = pd.DataFrame(rows); res.to_csv(OUT / "effects_validation.csv", index=False, encoding="utf-8-sig")

    # --- verdicts chiffres
    out = {}
    s = res[res.test == "Support par commercial"]
    out["support_corr_effet_plante_vs_score"] = round(float(np.corrcoef(s.effet_plante, s.score_moyen)[0, 1]), 3)
    weak = s[s.groupe.isin(fx["weak_support_employees"])].score_moyen.mean(); strong = s[s.groupe.isin(fx["strong_support_employees"])].score_moyen.mean()
    out["support_score_faibles_vs_forts"] = [round(float(weak), 3), round(float(strong), 3)]
    for t in ["Livraison par groupe territoire", "Livraison / ShipDate manquante", "Prix par catégorie", "Qualité (sous-catégories plantées)"]:
        out[t] = res[res.test == t].set_index("groupe").score_moyen.to_dict()
    out["effectifs"] = {f"{r.test}|{r.groupe}": int(r.n_phrases) for r in res.itertuples() if r.test != "Support par commercial"}
    out["Qualité autres"] = float(res[res.test.str.contains("référence")].score_moyen.iloc[0])
    json.dump(out, open(OUT / "effects_validation.json", "w"), ensure_ascii=False, indent=1, default=str)

    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    ax[0].scatter(s.effet_plante, s.score_moyen, s=s.n_phrases * 2, alpha=.7); ax[0].set(xlabel="effet planté (support)", ylabel="score moyen détecté", title=f"Support par commercial (r={out['support_corr_effet_plante_vs_score']})")
    l = res[res.test == "Livraison par groupe territoire"]; ax[1].bar(l.groupe, l.score_moyen); ax[1].set(title="Livraison : score par groupe de territoire")
    p = res[res.test == "Prix par catégorie"]; ax[2].bar(p.groupe, p.score_moyen); ax[2].set(title="Prix : score par catégorie produit"); ax[2].tick_params(axis="x", rotation=20)
    for a in ax: a.axhline(0, color="grey", lw=.6)
    plt.tight_layout(); plt.savefig(DOCS / "validation_effets.png", dpi=130)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))

if __name__ == "__main__":
    main()
