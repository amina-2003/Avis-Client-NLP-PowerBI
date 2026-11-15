"""Etape 2 - Generation d'un jeu d'avis SYNTHETIQUE relie aux lignes de vente reelles.
Pourquoi : l'archive ne contient aucun texte d'avis. Les effets plantes (commerciaux, territoires, categories...)
sont enregistres dans output/planted_effects.json : ils servent de verite terrain pour valider l'analyse.
ATTENTION : ces avis sont fictifs ; aucune conclusion metier reelle ne peut en etre tiree.
"""
import json, random
import numpy as np, pandas as pd
from common import *
from phrases import BANK, CONNECTORS_CONTRAST, CONNECTORS_ADD, CONNECTORS_NEG, CONNECTORS_POS

POL = {"pos": 1, "neu": 0, "neg": -1}
INV = {1: "pos", 0: "neu", -1: "neg"}

def split_bank(rng):
    """Marque chaque formulation train/test (les formulations 'test' ne servent jamais a l'entrainement)."""
    out = {}
    for th, d in BANK.items():
        for pol, lst in d.items():
            idx = list(range(len(lst))); rng.shuffle(idx)
            n_test = max(2, round(len(lst) * TEST_PHRASE_SHARE))
            test = set(idx[:n_test])
            out[(th, pol)] = {"train": [lst[i] for i in range(len(lst)) if i not in test],
                              "test": [lst[i] for i in sorted(test)]}
    return out

def add_noise(s, pol, rng):
    if rng.random() < 0.15: s = strip_accents(s)
    if rng.random() < 0.10: s = s.lower()
    if rng.random() < 0.05 and len(s) > 12:   # coquille : inversion de 2 lettres consecutives d'un meme mot
        cands = [i for i in range(1, len(s) - 1) if s[i].isalpha() and s[i+1].isalpha()]
        if cands:
            i = rng.choice(cands); s = s[:i] + s[i+1] + s[i] + s[i+2:]
    if rng.random() < 0.04: s += {1: " 😊", -1: " 😡", 0: " 😐"}[pol]   # emoji AVANT la ponctuation finale
    return s + ("!!" if rng.random() < 0.08 else ".")

def main():
    rng = random.Random(SEED); nrng = np.random.default_rng(SEED)
    fact = pd.read_csv(OUT / "fact_sales.csv", parse_dates=["OrderDate","ShipDate"])
    prod = pd.read_csv(OUT / "dim_product.csv"); terr = pd.read_csv(OUT / "dim_territory.csv")
    emp = pd.read_csv(OUT / "dim_employee.csv")

    # --- 1 avis candidat = 1 groupe commande (SO + revendeur + date) ; ligne principale = montant max
    f = fact[fact.OrderDate <= LAST_ORDER_CUTOFF].copy()
    f = f.sort_values("SalesAmount", ascending=False)
    main_line = f.groupby(["SalesOrderNumber","ResellerKey","OrderDate"], as_index=False).first()
    sample = main_line.sample(frac=REVIEW_RATE, random_state=SEED).sort_values("LineID").reset_index(drop=True)
    sample = sample.merge(prod[["ProductKey","Sous-catégorie","Catégorie"]], on="ProductKey", how="left") \
                   .merge(terr[["SalesTerritoryKey","SalesTerritoryGroup"]], on="SalesTerritoryKey", how="left")

    # --- 2 effets plantes
    reps = sorted(emp.EmployeeKey[emp.Title.str.contains("Sales Representative")].tolist())
    rrng = random.Random(SEED + 1); weak = rrng.sample(reps, 2); strong = rrng.sample([r for r in reps if r not in weak], 2)
    support_bias = {int(e): (-1.0 if e in weak else 0.8 if e in strong else 0.0) for e in emp.EmployeeKey}
    price_bias = {"Vélos": -0.55, "Composants": -0.1, "Vêtements": 0.2, "Accessoires": 0.3}
    quality_sub = {"Vélos VTT": -0.6, "Vélos de route": 0.4}   # sous-categories a fort volume (la ligne principale est presque toujours un velo)
    deliv_group = {"Europe": -0.5, "Pacific": -0.4}
    effects = dict(support_bias_by_employee=support_bias, weak_support_employees=[int(x) for x in weak],
                   strong_support_employees=[int(x) for x in strong], price_bias_by_category=price_bias,
                   quality_bias_by_subcategory=quality_sub, delivery_bias_by_territory_group=deliv_group,
                   delivery_bias_ship_date_missing=-0.7, base=0.25, reseller_sd=0.4, aspect_noise_sd=0.55)
    (OUT / "planted_effects.json").write_text(json.dumps(effects, ensure_ascii=False, indent=2))
    reseller_re = {int(r): nrng.normal(0, effects["reseller_sd"]) for r in fact.ResellerKey.unique()}

    bank = split_bank(rng)
    p_mention = {"Prix": .50, "Qualité": .60, "Livraison": .55, "Support": .45}
    reviews, sent_rows = [], []
    for i, r in sample.iterrows():
        rid = i + 1
        mu = {
         "Prix": price_bias.get(r["Catégorie"], 0),
         "Qualité": quality_sub.get(r["Sous-catégorie"], 0),
         "Livraison": deliv_group.get(r["SalesTerritoryGroup"], 0) + (effects["delivery_bias_ship_date_missing"] if r.ShipDateMissing else 0),
         "Support": support_bias.get(int(r.EmployeeKey), 0)}
        u = {a: effects["base"] + mu[a] + reseller_re[int(r.ResellerKey)] + nrng.normal(0, effects["aspect_noise_sd"]) for a in mu}
        pol = {a: (1 if v > 0.4 else -1 if v < -0.4 else 0) for a, v in u.items()}
        gen_u = 0.8 * np.mean(list(u.values())) + nrng.normal(0, 0.3)
        gen_pol = 1 if gen_u > 0.4 else -1 if gen_u < -0.4 else 0

        pm = dict(p_mention); 
        if r.ShipDateMissing: pm["Livraison"] = 0.85
        ment = [a for a in pm if rng.random() < pm[a]]
        if not ment: ment = [rng.choice(list(pm))]
        general = rng.random() < 0.7
        order = ment[:]; rng.shuffle(order)
        if general: order = (["Général"] + order) if rng.random() < 0.5 else (order + ["Général"])
        use_test = rng.random() < 0.25          # 25 % des avis n'emploient QUE des formulations 'test'
        split = "test" if use_test else "train"

        sentences, prev = [], None
        for a in order:
            p = gen_pol if a == "Général" else pol[a]
            pool = bank[(a, INV[p])][split]
            txt = rng.choice(pool); iron = txt.startswith("~"); txt = txt.lstrip("~")
            if rng.random() < 0.3 and a != "Général" and pd.notna(r["Sous-catégorie"]) and not iron:
                sc = r["Sous-catégorie"].lower().replace("vtt", "VTT")
                txt = f"Sur les {sc}, " + txt[0].lower() + txt[1:]
            if prev is not None and rng.random() < 0.6:
                if p != prev:
                    pool_c = CONNECTORS_CONTRAST + (CONNECTORS_NEG if p < 0 else CONNECTORS_POS if p > 0 else [])
                else:
                    pool_c = CONNECTORS_ADD
                conn = rng.choice(pool_c)
                if conn: txt = conn + txt[0].lower() + txt[1:]
            else:
                txt = txt[0].upper() + txt[1:]
            txt = add_noise(txt, p, rng)
            sentences.append(txt); prev = p
            sent_rows.append(dict(ReviewID=rid, SentenceNo=len(sentences), SentenceText=txt, ThemeTrue=a,
                                  PolarityTrue=INV[p], Ironic=iron))
        pv = np.mean([s["PolarityTrue"] == "pos" for s in sent_rows[-len(sentences):]]) - \
             np.mean([s["PolarityTrue"] == "neg" for s in sent_rows[-len(sentences):]])
        rating = int(np.clip(round(3 + 1.6 * pv + nrng.normal(0, 0.35)), 1, 5))
        base = r.ShipDate if pd.notna(r.ShipDate) else r.OrderDate + pd.Timedelta(days=7)
        reviews.append(dict(ReviewID=rid, LineID=int(r.LineID), ReviewDate=(base + pd.Timedelta(days=rng.randint(5, 45))).date(),
                            Rating=rating, ReviewText=" ".join(sentences), PhrasePool=split,
                            SentimentTrue="pos" if rating >= 4 else "neg" if rating <= 2 else "neu"))
    rv = pd.DataFrame(reviews); st = pd.DataFrame(sent_rows)
    rv.drop(columns="SentimentTrue").to_csv(OUT / "reviews_raw.csv", index=False, encoding="utf-8-sig")
    rv[["ReviewID","SentimentTrue"]].to_csv(OUT / "reviews_truth.csv", index=False, encoding="utf-8-sig")
    st.to_csv(OUT / "sentences_truth.csv", index=False, encoding="utf-8-sig")
    print(len(rv), "avis,", len(st), "phrases")
    print(rv.SentimentTrue.value_counts(normalize=True).round(3).to_dict(), rv.Rating.value_counts().sort_index().to_dict())
    print(rv.PhrasePool.value_counts().to_dict())
    for t in rv.sample(6, random_state=3).itertuples(): print(f"[{t.Rating}] {t.ReviewText}")

if __name__ == "__main__":
    main()
