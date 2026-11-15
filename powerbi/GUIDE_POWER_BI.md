# Guide de construction du rapport Power BI

> **Statut honnête** : les 10 tables CSV, le modèle de relations et les mesures DAX sont fournis et leurs données sont
> contrôlées par 22 tests automatiques. **Le fichier `.pbix` lui-même n'a pas pu être produit** (pas de Power BI Desktop
> dans l'environnement de travail) ; les mesures DAX et le script M n'ont donc **pas été exécutés dans Power BI**.
> Compter 45 à 60 min pour monter le rapport en suivant ce guide, et corriger la syntaxe si Desktop signale une erreur.

## 1. Chargement
`charger_tables.pq` (fonction M) ou *Obtenir les données > Texte/CSV* sur chaque fichier de `powerbi/` (encodage UTF-8).

## 2. Modèle en étoile — relations à créer

| De (plusieurs) | Vers (un) | Actif | Direction filtre |
|---|---|---|---|
| FactSales[DateKey] | DimDate[DateKey] | oui | simple |
| FactSales[ProductKey] | DimProduct[ProductKey] | oui | simple |
| FactSales[ResellerKey] | DimReseller[ResellerKey] | oui | simple |
| FactSales[EmployeeKey] | DimEmployee[EmployeeKey] | oui | simple |
| FactSales[SalesTerritoryKey] | DimSalesTerritory[SalesTerritoryKey] | oui | simple |
| **FactReviews[LineID]** | **FactSales[LineID]** | oui | simple (FactSales → FactReviews) |
| FactReviews[ReviewDateKey] | **DimReviewDate**[DateKey] | oui | simple |
| FactReviewThemes[ReviewID] | FactReviews[ReviewID] | oui | simple |
| FactReviewThemes[Theme] | DimTheme[Theme] | oui | simple |
| Targets[EmployeeKey] | DimEmployee[EmployeeKey] | oui | simple |
| Targets[TargetDateKey] | DimDate[DateKey] | oui | simple |

Points de conception à connaître (ce sont les pièges classiques) :
- **`LineID` et non `SalesOrderNumber`** : le numéro de commande est réutilisé par plusieurs revendeurs (136 cas) et le couple commande-ligne n'est pas unique (1 914 lignes concernées). Une relation sur ces colonnes serait plusieurs-à-plusieurs et fausserait les agrégats.
- **`DimReviewDate` est une copie de `DimDate`** : sans elle, filtrer par date filtrerait à la fois la date de commande *et* la date d'avis (deux chemins). Axe temporel des avis = `DimReviewDate`; axe des ventes = `DimDate`.
- **Ne pas relier `FactReviews[MainTheme]` à `DimTheme`** : deuxième chemin vers `DimTheme` = ambiguïté. Utiliser `MainTheme` directement comme champ.
- Trier `SentimentLabel` par `SentimentOrder` (Positif, Neutre, Négatif) et `Theme` par `ThemeOrder`; `MonthName` par `MonthNo`.
- Masquer les clés techniques; le `ReviewText` reste visible dans une table de détail (drill-through).

## 3. Pages proposées

1. **Vue d'ensemble** — cartes : `Nb avis`, `Note moyenne`, `% Positifs`, `% Négatifs`, `Net sentiment`; courbe `% Négatifs` par `DimReviewDate[YearMonth]`; jauge de couverture. Segments : année, catégorie, territoire.
2. **Thèmes** — barres `Nb mentions` par thème; barres 100 % empilées Positif/Neutre/Négatif par thème (`FactReviewThemes[SentimentLabel]`); matrice thème × catégorie produit avec `Score thème (si fiable)`.
3. **Produits** — sous-catégories triées par `% Négatifs (si fiable)`; table des avis négatifs avec `ReviewText`.
4. **Équipe & territoires** — `Score thème` filtré sur Support par commercial (`DimEmployee`); `Score thème` Livraison par `SalesTerritoryGroup`; carte de pays.
5. **Satisfaction × ventes** — nuage de points (X = `CA`, Y = `Score sentiment`, détail = commercial ou catégorie); `Revendeurs à risque`. **Titre à mettre sur la page : « corrélation ≠ causalité »**.
6. **Qualité de l'analyse** (page de transparence) — `Fiabilité`, part des avis du jeu `EvalPool`, rappel que les avis sont synthétiques.

Toujours afficher `Nb avis` ou `Fiabilité` à côté d'un score : avec ~950 avis répartis sur ~480 revendeurs (≈2 avis/revendeur), une analyse au niveau revendeur individuel n'est pas significative; privilégier commercial, territoire, catégorie.

## 4. Résultats attendus (moteur ML ; pour vérifier que votre rapport est juste)
- 953 avis; ≈ 36 % positifs, 38 % neutres, 25 % négatifs; note moyenne ≈ 3,12; `Net sentiment` ≈ +11.
- Mentions négatives par thème : **Prix ≈ 37 %** (le plus négatif), Qualité ≈ 29 %, Support ≈ 26 %, Livraison ≈ 20 %.
- Les 2 commerciaux « faibles » plantés ressortent avec un score Support moyen négatif; les 2 « forts » à ≈ +0,5.
- Livraison Europe < Amérique du Nord; Prix des vélos < Prix des vêtements; Qualité VTT < Qualité vélos de route.
- Colonne `Moteur` = « ML (régression logistique) »; `Accord ML / Lexique` ≈ 88 %.
(`docs/validation_effets.png` montre ces effets recalculés. Avec `ENGINE = "lexique"`, les valeurs deviennent 39 / 38 / 23 %.)

**Page de comparaison facultative** : `% Négatifs` contre `% Négatifs (lexique)` par thème ou par commercial, et `Accord ML / Lexique`.

## 5. Pièges de données à signaler dans la restitution
- **Objectifs (`Targets`)** : ~200× inférieurs au CA (unité/périmètre inconnus) → aucune mesure « atteinte d'objectif » n'est fournie.
- **2022 et 2023** : 327 lignes chacune, CA identique (176 773 $) → très probablement une copie décalée d'un an; **aucun avis n'est généré après 2021**.
- Lignes à `ShipDateMissing` = TRUE (1 575) : date d'expédition absente, conservée telle quelle (non imputée).
