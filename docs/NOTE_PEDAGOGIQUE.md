# Note pédagogique — Projet 12 : analyse des avis clients

## 1. Scénario métier
AdventureWorks vend des vélos, composants, vêtements et accessoires à **701 revendeurs** (ventes B2B, 2017-2023).
Après une commande, un revendeur laisse un commentaire libre. La direction commerciale veut savoir **quoi** pose problème
(prix, qualité, livraison, support) et **où** (produit, territoire, commercial), sans lire des milliers de commentaires.
Livrable : un modèle de données et un rapport Power BI reliant sentiment, thèmes et indicateurs de ventes.

## 2. Démarche
1. **Audit des données** avant toute modélisation (voir §4) — c'est là que se sont jouées les décisions les plus importantes.
2. **Avis synthétiques reliés à de vraies lignes de vente** (l'archive ne contient aucun texte client). Chaque avis pointe vers une
   ligne précise (`LineID`) ; ses caractéristiques (commercial, territoire, produit, date d'expédition) proviennent de la base.
3. **Effets plantés** : certains commerciaux, territoires et catégories reçoivent un biais connu (ex. 2 commerciaux « faibles »).
   Ils servent de **vérité terrain** : si le pipeline fonctionne, le tableau de bord doit les retrouver.
4. **NLP en deux niveaux** : segmentation en phrases → sentiment + thème par phrase → agrégation en sentiment d'avis.
   Le niveau phrase permet un **sentiment par thème** (un avis peut être positif sur le support et négatif sur le prix).
5. **Évaluation sur trois jeux** : formulations de test jamais vues à l'entraînement, jeu « stress » écrit à la main, et validation
   de bout en bout (effets retrouvés ?).
6. **Export en étoile** pour Power BI, 22 tests automatiques, exécution complète reproductible en ~20 s.

## 3. Choix techniques et justification
| Choix | Pourquoi | Alternative écartée |
|---|---|---|
| **Modèle ML** (régression logistique sur variables lexicales) comme moteur de production | Exigence du sujet ; modèle réellement entraîné, évalué et sauvegardé ; égale le lexique sur les phrases et corrige son biais sur les négatifs | Lexique seul (conservé comme référence et comparable dans Power BI) ; transformer pré-entraîné (inaccessible ici) |
| Analyse **par phrase** puis agrégation | Donne le sentiment par thème, cœur de la mission | Un seul score par avis : perd l'information |
| Thème = mots-clés (un thème principal par phrase) | Transparent, 100 % reproductible | BERTopic / zero-shot : utile pour *découvrir* des thèmes, pas pour un référentiel métier fixe |
| Seuil de décision tuné **sur le jeu d'entraînement seulement** | Évite de gonfler le score de test | Tuning sur tout le jeu (fuite) |
| `LineID` artificiel comme clé de liaison | Les clés natives ne sont pas fiables (§4) | Relation sur `SalesOrderNumber` : agrégats faux |
| `DimReviewDate` séparée de `DimDate` | Évite le double filtrage date de commande / date d'avis | `USERELATIONSHIP` : ne supprime pas le 2ᵉ chemin actif |
| Graine fixe, tests, `run_all.py` | Reproductibilité exigée par le sujet | — |

## 4. Difficultés rencontrées (et ce qu'on en a fait)
- **Clé commande-ligne non unique** : 1 914 lignes partagent une clé commande-ligne avec des contenus *différents* (surtout 2021). Ce ne sont pas des doublons à supprimer. → `LineID` artificiel, indicateur `KeyIsDuplicated` conservé.
- **Numéros de commande partagés** : 136 `SalesOrderNumber` concernent plusieurs revendeurs → impossible de les utiliser comme clé d'avis.
- **2022 et 2023** : 327 lignes chacun, CA strictement identique (176 773 $) → copie décalée probable. **Aucun avis n'est généré après 2021.**
- **Objectifs** : ~200× inférieurs au CA (ex. 2019 : 157 k$ contre 32,5 M$). Unité inconnue → **aucun taux d'atteinte fourni** plutôt qu'un chiffre absurde.
- **54 objectifs sans employé** au premier jet (dimension filtrée trop tôt) → dimension élargie, contrôlée par test d'intégrité.
- **Bug de tokenisation** : « l'assistance » restait collé à l'apostrophe, « après-vente » cassé par le trait d'union (thème Support manqué). Corrigé, correction générale (pas un réglage au cas par cas).
- **Générateur** : un connecteur « Malheureusement » collé à une phrase positive aurait piégé le modèle ; une « coquille » aléatoire échangeait une lettre avec une espace. Corrigés avant toute mesure finale.
- **Correction de ma propre validation** : une première version « validait » l'effet qualité sur 1 et 2 phrases seulement (la ligne principale est presque toujours un vélo). Sans valeur statistique → effet replanté sur VTT / vélos de route (161 et 193 phrases) et **seuil d'effectif minimal (30)** ajouté dans le test.

## 5. Le modèle ML : ce qui a échoué, ce qui a marché, et ce que cela vaut
1. **ML naïf (TF-IDF seul)** : 43 % de justesse par phrase sur des formulations jamais vues (hasard ≈ 33 %). Le corpus n'a qu'une centaine de formulations ; le modèle mémorise des gabarits au lieu d'apprendre la langue.
2. **Vecteurs de mots spaCy (`fr_core_news_md`)** : essayés pour donner une compréhension préalable du français. Sentiment à 55-58 % : insuffisant, ajoutés aux autres variables ils n'apportent rien → **non retenus**.
3. **Modèle retenu** : régression logistique sur des variables calculées par phrase (score lexical, nombres de mots positifs et négatifs, négation, marqueur neutre, longueur). Il **apprend** poids et seuils à partir de phrases annotées. Résultats : 74 % par phrase en test (lexique : 79 %), **96 % sur le jeu stress** (lexique : 92 %), contrôle en sens inverse (entraîné sur 25 % des phrases, testé sur le reste) : 88 %.
4. **Par avis entier**, le ML est moins bon que le lexique (58 % contre 64 %). Un modèle de second niveau (phrases → avis) a été testé **une seule fois** (55 %) et abandonné ; la variante simple a été retenue sur le jeu d'entraînement, pas sur le test.
5. **Ce que le ML change dans le tableau de bord** : la part de mentions négatives du thème Support passe d'environ 12 % (lexique) à 26 % (ML), et la vérité terrain est à 25,5 %. Le lexique sous-estimait les négatifs (« impossible de joindre » n'est pas dans ses mots). Réserve : 75 % des phrases de cette comparaison ont servi à l'entraînement.
**Limite à citer** : la qualité du ML vient de variables lexicales que j'ai écrites ; ce n'est pas une « compréhension » de la langue. Pour de vrais avis, un modèle pré-entraîné multilingue (`src/transformer_engine.py`, **non exécuté**, pas d'accès à huggingface.co ici) serait la suite, à évaluer avec le même protocole.

## 6. Limites et points de vigilance (à citer à l'oral)
1. **Avis synthétiques** : plus propres, plus réguliers et plus « expressifs » que de vrais avis. Les scores réels seraient plus bas.
2. **Le lexique a été écrit en connaissant la banque de phrases**, et le ML en reçoit des variables : les 99,7 % sur les thèmes (test) sont **optimistes par construction** pour les deux moteurs. Le jeu stress (24 phrases, effectif faible, intervalle de confiance large) est plus parlant mais **n'est plus totalement indépendant** : j'ai corrigé deux bugs généraux après en avoir vu les erreurs.
3. **Étiquette d'avis = note bruitée** : plafond théorique ≈ 83 % de justesse par avis. Obtenu en test : **58 % (ML retenu)**, 64 % (lexique) ; en entraînement 78 % et 74 %. L'écart avec le plafond reste important.
4. **Ironie** : 62 % de justesse sur les phrases ironiques (contre 87 % sinon) ; « Livraison express, nous avons été surpris » (mot inconnu) ou « les freins » (vocabulaire produit) échappent au lexique.
5. **Faibles effectifs** : ≈ 2 avis par revendeur ; Pacifique (21 phrases), date d'expédition manquante (14), accessoires (3) → indicatifs seulement. Toujours afficher l'effectif.
6. **Corrélation ≠ causalité** entre satisfaction et ventes ; ici le lien est de toute façon **fabriqué** par construction.
7. **Un thème principal par phrase** : une phrase mêlant prix et qualité n'en retient qu'un.
8. **Power BI non testé** : les 10 tables et les relations sont contrôlées par tests d'intégrité, mais le `.pbix`, les mesures DAX et le script M n'ont pas été exécutés dans Power BI Desktop.
9. **Avis réels** : ils contiendraient des données personnelles (noms, e-mails) → anonymisation / RGPD à prévoir avant tout traitement.

## 7. Bonnes pratiques retenues
Auditer avant de modéliser · ne jamais faire confiance à une clé sans test d'unicité · séparer entraînement / test **par formulation**, pas seulement par ligne ·
régler les seuils sur l'entraînement uniquement · comparer à un plafond théorique · tester avec un jeu rédigé indépendamment ·
planter des effets connus pour valider de bout en bout · comparer chaque modèle à une référence simple et publier aussi les essais non retenus · afficher l'effectif à côté de chaque indicateur · documenter les corrections de ses propres erreurs.

## 8. Démonstration (≈ 5 min)
1. `python src/run_all.py` puis `pytest` (verts) → reproductibilité.
2. Montrer `docs/validation_effets.png` : « les problèmes que j'ai plantés sont retrouvés ».
3. Power BI : page Thèmes (Prix le plus négatif), page Équipe (2 commerciaux faibles), page Qualité de l'analyse (limites).
4. Conclure par le §5 et le §6 : ce qui marche, ce qui ne prouve rien, ce qu'il faudrait avec de vrais avis.
