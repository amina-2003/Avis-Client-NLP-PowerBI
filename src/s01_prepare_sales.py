"""Etape 1 - Nettoyage des donnees AdventureWorks et creation des tables de faits/dimensions.
Decisions de qualite (documentees dans docs/NOTE_PEDAGOGIQUE.md) :
 - SalesOrderNumber+SalesOrderLineNumber n'est PAS unique (reutilises avec contenus differents) -> LineID artificiel.
 - ShipDate manquante conservee (flag), jamais imputee.
 - Faute 'Ware House' normalisee en 'Warehouse'.
"""
import glob, warnings
import pandas as pd
from common import *

warnings.filterwarnings("ignore")

def load_sales():
    parts = []
    for f in sorted(glob.glob(str(RAW / "FactSales" / "*.xlsx"))):
        d = pd.read_excel(f); d["SourceFile"] = Path(f).name; parts.append(d)
    f = pd.concat(parts, ignore_index=True)
    for c in ["OrderDate", "DueDate", "ShipDate"]:
        f[c] = pd.to_datetime(f[c], errors="coerce")
    f = f.sort_values(["OrderDate", "SalesOrderNumber", "SalesOrderLineNumber"]).reset_index(drop=True)
    f.insert(0, "LineID", range(1, len(f) + 1))
    f["KeyIsDuplicated"] = f.duplicated(["SalesOrderNumber", "SalesOrderLineNumber"], keep=False)
    f["ShipDateMissing"] = f.ShipDate.isna()
    f["ShipDelayDays"] = (f.ShipDate - f.OrderDate).dt.days
    f["DateKey"] = f.OrderDate.dt.strftime("%Y%m%d").astype(int)
    keep = ["LineID","SalesOrderNumber","SalesOrderLineNumber","OrderDate","DueDate","ShipDate","DateKey","ProductKey",
            "ResellerKey","PromotionKey","EmployeeKey","SalesTerritoryKey","OrderQuantity","UnitPrice",
            "TotalProductCost","SalesAmount","ShipDelayDays","ShipDateMissing","KeyIsDuplicated","SourceFile"]
    return f[keep]

def build_dims(fact):
    p = pd.read_csv(RAW / "DimProduct.txt", sep="\t", dtype=str)
    p["ProductKey"] = p.ProductKey.astype(int)
    p["ProductSubcategoryKey"] = pd.to_numeric(p.ProductSubcategoryKey, errors="coerce")
    p["ListPrice"] = pd.to_numeric(p.ListPrice.str.replace(r"[$,]", "", regex=True), errors="coerce")
    p["Sous-catégorie"] = p.ProductSubcategoryKey.map(lambda k: SUBCATEGORIES.get(k, (None, None))[0] if pd.notna(k) else None)
    p["Catégorie"] = p.ProductSubcategoryKey.map(lambda k: SUBCATEGORIES.get(k, (None, None))[1] if pd.notna(k) else None)
    dim_product = p[["ProductKey","EnglishProductName","ModelName","ProductLine","Color","ListPrice",
                     "ProductSubcategoryKey","Sous-catégorie","Catégorie"]].rename(columns={"EnglishProductName": "ProductName"})
    dim_product = dim_product[dim_product.ProductKey.isin(fact.ProductKey.unique())]

    r = pd.read_csv(RAW / "DimReseller.txt", sep="\t", dtype=str)
    r["BusinessType"] = r.BusinessType.replace({"Ware House": "Warehouse"})
    dim_reseller = r.rename(columns={"DimGeography.City":"City","DimGeography.StateProvinceName":"StateProvince",
                    "DimGeography.EnglishCountryRegionName":"Country"})[
        ["ResellerKey","ResellerName","BusinessType","City","StateProvince","Country","NumberEmployees"]]
    dim_reseller["ResellerKey"] = dim_reseller.ResellerKey.astype(int)

    e = pd.read_csv(RAW / "DimEmployee.txt", sep="\t", dtype=str)
    e["EmployeeKey"] = e.EmployeeKey.astype(int)
    e["EmployeeName"] = e.FirstName + " " + e.LastName
    e["EmployeeID"] = pd.to_numeric(e.EmployeeNationalIDAlternateKey)
    tg_ids = set(pd.read_csv(RAW / "ResellerSalesTargets.csv", encoding="utf-16").EmployeeID)
    # employes presents dans les ventes OU porteurs d'objectifs
    dim_employee = e[e.EmployeeKey.isin(fact.EmployeeKey.unique()) | e.EmployeeID.isin(tg_ids)][
        ["EmployeeKey","EmployeeName","Title","EmployeeID"]]

    t = pd.read_csv(RAW / "DimSalesTerritory.txt", sep="\t")
    dim_territory = t[["SalesTerritoryKey","SalesTerritoryRegion","SalesTerritoryCountry","SalesTerritoryGroup"]]

    # objectifs : depivot M01..M12, '-' = pas d'objectif
    tg = pd.read_csv(RAW / "ResellerSalesTargets.csv", encoding="utf-16")
    tg = tg.melt(id_vars=["Year","EmployeeID"], var_name="M", value_name="Target")
    tg["Month"] = tg.M.str[1:].astype(int)
    tg["Target"] = pd.to_numeric(tg.Target.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")
    tg = tg.dropna(subset=["Target"])
    tg = tg.merge(dim_employee[["EmployeeID","EmployeeKey"]], on="EmployeeID", how="left")
    targets = tg[["Year","Month","EmployeeKey","Target"]]
    return dim_product, dim_reseller, dim_employee.drop(columns="EmployeeID"), dim_territory, targets

def main():
    OUT.mkdir(exist_ok=True)
    fact = load_sales()
    dp, dr, de, dt, tg = build_dims(fact)
    for name, df in dict(fact_sales=fact, dim_product=dp, dim_reseller=dr, dim_employee=de,
                         dim_territory=dt, targets=tg).items():
        df.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")
        print(f"{name:14s} {len(df):>7d} lignes")
    print("Lignes a cle commande-ligne dupliquee:", int(fact.KeyIsDuplicated.sum()))
    print("Cibles sans employe rattache:", int(tg.EmployeeKey.isna().sum()))

if __name__ == "__main__":
    main()
