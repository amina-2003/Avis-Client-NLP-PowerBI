"""Etape 4 - Export du modele en etoile pour Power BI (CSV UTF-8 avec BOM) + dictionnaire de donnees."""
import pandas as pd
from common import *

SENT_FR = {"pos": ("Positif", 1), "neu": ("Neutre", 2), "neg": ("Négatif", 3)}
MOIS = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]

def sent_cols(df, col, prefix=""):
    df[prefix + "SentimentLabel"] = df[col].map(lambda x: SENT_FR[x][0])
    df[prefix + "SentimentOrder"] = df[col].map(lambda x: SENT_FR[x][1])
    return df

def main():
    PBI.mkdir(exist_ok=True)
    fact = pd.read_csv(OUT / "fact_sales.csv", parse_dates=["OrderDate", "DueDate", "ShipDate"])
    rv = pd.read_csv(OUT / "reviews_scored.csv", parse_dates=["ReviewDate"]); ss = pd.read_csv(OUT / "sentences_scored.csv")
    tg = pd.read_csv(OUT / "targets.csv")

    # Faits
    fs = fact.drop(columns=["SourceFile"]).copy()
    for c in ["OrderDate", "DueDate", "ShipDate"]: fs[c] = fs[c].dt.strftime("%Y-%m-%d")
    fr = rv.copy(); fr["ReviewDateKey"] = fr.ReviewDate.dt.strftime("%Y%m%d").astype(int)
    fr["ReviewDate"] = fr.ReviewDate.dt.strftime("%Y-%m-%d"); fr = sent_cols(fr, "SentimentPred")
    fr["IsNegative"] = (fr.SentimentPred == "neg").astype(int); fr["IsPositive"] = (fr.SentimentPred == "pos").astype(int)
    fr["SentimentLabelLexique"] = fr.SentimentLexique.map(lambda x: SENT_FR[x][0])
    fr["AccordMLLexique"] = (fr.SentimentLabelLexique == fr.SentimentLabel).astype(int)
    fr = fr.rename(columns={"PhrasePool": "EvalPool"}).drop(columns=["SentimentPred", "SentimentLexique"])
    ft = sent_cols(ss.copy(), "Sentiment").drop(columns=["Sentiment", "SentLexique"])
    ft["IsNegative"] = (ft.SentimentLabel == "Négatif").astype(int); ft["IsPositive"] = (ft.SentimentLabel == "Positif").astype(int)

    # Dimensions
    d0, d1 = min(fact.OrderDate.min(), rv.ReviewDate.min()), max(fact.OrderDate.max(), rv.ReviewDate.max())
    dd = pd.DataFrame({"Date": pd.date_range(d0.replace(day=1), d1 + pd.offsets.MonthEnd(0))})
    dd["DateKey"] = dd.Date.dt.strftime("%Y%m%d").astype(int); dd["Year"] = dd.Date.dt.year; dd["MonthNo"] = dd.Date.dt.month
    dd["MonthName"] = dd.MonthNo.map(lambda m: MOIS[m-1]); dd["YearMonth"] = dd.Date.dt.strftime("%Y-%m"); dd["Quarter"] = "T" + dd.Date.dt.quarter.astype(str)
    dd["Date"] = dd.Date.dt.strftime("%Y-%m-%d")
    dth = pd.DataFrame({"Theme": THEMES, "ThemeOrder": range(1, len(THEMES) + 1)})
    tg = tg.assign(TargetDateKey=lambda d: d.Year * 10000 + d.Month * 100 + 1)

    tables = dict(FactSales=fs, FactReviews=fr, FactReviewThemes=ft, DimDate=dd, DimReviewDate=dd.copy(), DimTheme=dth, Targets=tg,
                  DimProduct=pd.read_csv(OUT / "dim_product.csv"), DimReseller=pd.read_csv(OUT / "dim_reseller.csv"),
                  DimEmployee=pd.read_csv(OUT / "dim_employee.csv"), DimSalesTerritory=pd.read_csv(OUT / "dim_territory.csv"))
    dico = ["# Dictionnaire de données (généré automatiquement)\n"]
    for n, df in tables.items():
        df.to_csv(PBI / f"{n}.csv", index=False, encoding="utf-8-sig"); print(f"{n:18s}{len(df):>7d} x {df.shape[1]}")
        dico.append(f"\n## {n} — {len(df)} lignes\n\n| Colonne | Type | Exemple |\n|---|---|---|")
        for c in df.columns:
            ex = str(df[c].dropna().iloc[0])[:60].replace("|", "/") if df[c].notna().any() else ""
            dico.append(f"| {c} | {df[c].dtype} | {ex} |")
    (DOCS / "dictionnaire_donnees.md").write_text("\n".join(dico), encoding="utf-8")

if __name__ == "__main__":
    main()
