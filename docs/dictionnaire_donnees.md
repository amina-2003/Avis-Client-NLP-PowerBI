# Dictionnaire de données (généré automatiquement)


## FactSales — 68782 lignes

| Colonne | Type | Exemple |
|---|---|---|
| LineID | int64 | 1 |
| SalesOrderNumber | str | SO43659 |
| SalesOrderLineNumber | int64 | 1 |
| OrderDate | str | 2017-07-01 |
| DueDate | str | 2017-07-11 |
| ShipDate | str | 2017-07-08 |
| DateKey | int64 | 20170701 |
| ProductKey | int64 | 349 |
| ResellerKey | int64 | 676 |
| PromotionKey | int64 | 1 |
| EmployeeKey | int64 | 285 |
| SalesTerritoryKey | int64 | 5 |
| OrderQuantity | int64 | 1 |
| UnitPrice | float64 | 2024.99 |
| TotalProductCost | float64 | 10.19 |
| SalesAmount | float64 | 2024.99 |
| ShipDelayDays | float64 | 7.0 |
| ShipDateMissing | bool | False |
| KeyIsDuplicated | bool | False |

## FactReviews — 953 lignes

| Colonne | Type | Exemple |
|---|---|---|
| ReviewID | int64 | 1 |
| LineID | int64 | 78 |
| ReviewDate | str | 2017-08-04 |
| Rating | int64 | 2 |
| ReviewText | str | Relation commerciale à améliorer d'urgence. Par ailleurs, su |
| EvalPool | str | test |
| SentimentScore | float64 | 0.2007 |
| SentimentScoreLexique | float64 | 0.0 |
| Moteur | str | ML (régression logistique) |
| MainTheme | str | Support |
| NbSentences | int64 | 3 |
| ReviewDateKey | int64 | 20170804 |
| SentimentLabel | str | Neutre |
| SentimentOrder | int64 | 2 |
| IsNegative | int64 | 0 |
| IsPositive | int64 | 0 |
| SentimentLabelLexique | str | Neutre |
| AccordMLLexique | int64 | 1 |

## FactReviewThemes — 2773 lignes

| Colonne | Type | Exemple |
|---|---|---|
| ReviewID | int64 | 1 |
| SentenceNo | int64 | 1 |
| SentenceText | str | Relation commerciale à améliorer d'urgence. |
| Theme | str | Général |
| SentimentScore | float64 | 0.3421 |
| ThemeLexique | str | Général |
| ScoreLexique | float64 | 0.0 |
| SentimentLabel | str | Positif |
| SentimentOrder | int64 | 1 |
| IsNegative | int64 | 0 |
| IsPositive | int64 | 1 |

## DimDate — 2161 lignes

| Colonne | Type | Exemple |
|---|---|---|
| Date | str | 2017-07-01 |
| DateKey | int64 | 20170701 |
| Year | int32 | 2017 |
| MonthNo | int32 | 7 |
| MonthName | str | juillet |
| YearMonth | str | 2017-07 |
| Quarter | str | T3 |

## DimReviewDate — 2161 lignes

| Colonne | Type | Exemple |
|---|---|---|
| Date | str | 2017-07-01 |
| DateKey | int64 | 20170701 |
| Year | int32 | 2017 |
| MonthNo | int32 | 7 |
| MonthName | str | juillet |
| YearMonth | str | 2017-07 |
| Quarter | str | T3 |

## DimTheme — 5 lignes

| Colonne | Type | Exemple |
|---|---|---|
| Theme | str | Prix |
| ThemeOrder | int64 | 1 |

## Targets — 809 lignes

| Colonne | Type | Exemple |
|---|---|---|
| Year | int64 | 2018 |
| Month | int64 | 1 |
| EmployeeKey | int64 | 286 |
| Target | float64 | 200.0 |
| TargetDateKey | int64 | 20180101 |

## DimProduct — 334 lignes

| Colonne | Type | Exemple |
|---|---|---|
| ProductKey | int64 | 223 |
| ProductName | str | AWC Logo Cap |
| ModelName | str | Cycling Cap |
| ProductLine | str | S |
| Color | str | Multi |
| ListPrice | float64 | 8.64 |
| ProductSubcategoryKey | float64 | 19.0 |
| Sous-catégorie | str | Casquettes |
| Catégorie | str | Vêtements |

## DimReseller — 701 lignes

| Colonne | Type | Exemple |
|---|---|---|
| ResellerKey | int64 | 296 |
| ResellerName | str | Extreme Toy Store |
| BusinessType | str | Warehouse |
| City | str | Birmingham |
| StateProvince | str | Alabama |
| Country | str | United States |
| NumberEmployees | int64 | 91 |

## DimEmployee — 18 lignes

| Colonne | Type | Exemple |
|---|---|---|
| EmployeeKey | int64 | 272 |
| EmployeeName | str | Stephen Jiang |
| Title | str | North American Sales Manager |

## DimSalesTerritory — 11 lignes

| Colonne | Type | Exemple |
|---|---|---|
| SalesTerritoryKey | int64 | 1 |
| SalesTerritoryRegion | str | Northwest |
| SalesTerritoryCountry | str | United States |
| SalesTerritoryGroup | str | North America |