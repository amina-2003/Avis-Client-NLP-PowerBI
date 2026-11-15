"""Banque de formulations (FR) par theme et polarite. '~' en tete = phrase ironique (negatif litteralement positif).
Aucune phrase ne contient de point, point-virgule, '?' ou '!' interne (segmentation par ponctuation)."""
BANK = {
"Prix": {
 "pos": ["Les tarifs sont très compétitifs pour notre marge","Excellent rapport qualité prix","Les remises accordées sont intéressantes",
         "Prix attractifs par rapport à la concurrence","Tarification claire et avantageuse","On y gagne vraiment sur le prix d'achat",
         "Le coût d'achat est tout à fait raisonnable","Bon positionnement tarifaire pour nos clients"],
 "neu": ["Les prix sont dans la moyenne du marché","Tarifs corrects sans être exceptionnels","Le prix est acceptable mais sans plus",
         "Rien à signaler sur les tarifs","Les prix sont conformes à ce que nous attendions","Tarifs standards pour ce type de produit",
         "Prix honnête, ni cher ni bon marché"],
 "neg": ["Les prix sont beaucoup trop élevés pour notre marge","Tarifs excessifs par rapport à la concurrence","Le coût d'achat est un vrai frein pour nous",
         "Les remises sont insuffisantes","Prix en hausse sans aucune justification","C'est trop cher pour ce que c'est",
         "Notre marge est écrasée par ces tarifs","~Super, encore une hausse de tarifs, on adore payer plus cher"]},
"Qualité": {
 "pos": ["La qualité de fabrication est irréprochable","Produit solide et très bien fini","Aucun défaut constaté à la réception",
         "Nos clients sont ravis de la qualité","Finitions impeccables","Très bonne durabilité, peu de retours en magasin",
         "Matériaux de grande qualité","Les produits tiennent parfaitement leurs promesses"],
 "neu": ["La qualité est correcte sans être exceptionnelle","Produit conforme à la description, sans plus","Finition moyenne mais acceptable",
         "Qualité standard pour cette gamme","Rien d'exceptionnel côté fabrication","Quelques petits détails à améliorer mais rien de grave",
         "Qualité honnête dans l'ensemble"],
 "neg": ["Plusieurs produits sont arrivés défectueux","La qualité de fabrication est décevante","Beaucoup de retours clients pour des pièces cassées",
         "Finitions bâclées et matériaux fragiles","Des défauts de fabrication récurrents","Le produit s'use beaucoup trop vite",
         "Qualité en nette baisse par rapport à avant","~Bravo pour la qualité, le cadre s'est cassé au bout d'une semaine"]},
"Livraison": {
 "pos": ["Livraison rapide et soignée","Colis reçu en avance et bien emballé","Les délais de livraison sont toujours respectés",
         "Expédition très efficace","Livraison ponctuelle à chaque commande","Emballage parfait et suivi clair du colis",
         "Réapprovisionnement très rapide","Aucun retard à signaler sur les livraisons"],
 "neu": ["Délai de livraison dans la moyenne","Livraison correcte, sans surprise","Le colis est arrivé à la date prévue, rien de plus",
         "Délais acceptables mais le suivi pourrait être meilleur","Emballage correct","Livraison standard comme d'habitude",
         "Un léger retard mais sans conséquence"],
 "neg": ["La livraison a pris beaucoup trop de temps","Colis arrivé en retard et abîmé","Retards de livraison à répétition",
         "Délais non respectés et aucun suivi du colis","Commande incomplète à la réception","Livraison catastrophique, nous avons perdu des ventes",
         "Réapprovisionnement beaucoup trop lent","~Génial, encore une livraison en retard, quelle belle surprise"]},
"Support": {
 "pos": ["Le commercial est très réactif et à l'écoute","Excellent suivi de notre compte","Support client disponible et compétent",
         "Réponses rapides à toutes nos questions","Notre interlocuteur est professionnel et de bon conseil","Les problèmes sont réglés immédiatement",
         "Très bon accompagnement commercial","Une équipe agréable et efficace"],
 "neu": ["Le support répond, mais pas toujours très vite","Service client correct sans plus","Le suivi commercial est moyen",
         "Interlocuteur aimable mais peu de proactivité","Rien de particulier à dire sur le support","Réponses correctes mais parfois incomplètes",
         "Le suivi est standard"],
 "neg": ["Impossible de joindre notre commercial","Le service client ne répond jamais à nos mails","Aucun suivi après la commande",
         "Support injoignable et peu compétent","Nos réclamations restent sans réponse","Interlocuteur désagréable et désorganisé",
         "Il faut relancer trois fois pour obtenir une réponse","~Merci au support, on adore attendre trois semaines une réponse"]},
"Général": {
 "pos": ["Nous sommes très satisfaits dans l'ensemble","Excellente collaboration, nous recommandons","Un partenaire fiable que nous recommandons vivement",
         "Très bonne expérience globale","Nous renouvellerons nos commandes avec plaisir","Globalement tout est parfait",
         "Une relation commerciale très satisfaisante"],
 "neu": ["Expérience globale correcte","Ni bonne ni mauvaise expérience dans l'ensemble","Collaboration correcte mais peut mieux faire",
         "Globalement acceptable","Rien de marquant à signaler","Un partenaire comme un autre"],
 "neg": ["Nous sommes très déçus dans l'ensemble","Nous hésitons à renouveler nos commandes","Expérience globale décevante",
         "Nous ne recommandons pas ce fournisseur","Relation commerciale à améliorer d'urgence","Nous songeons à changer de fournisseur",
         "Globalement une mauvaise expérience"]},
}
CONNECTORS_CONTRAST = ["Par contre, ","En revanche, ","Cependant, ","Mais "]
CONNECTORS_NEG = ["Malheureusement, ","Hélas, "]
CONNECTORS_POS = ["Heureusement, ","Bonne surprise, "]
CONNECTORS_ADD = ["Par ailleurs, ","De plus, ","Et ","Aussi, ",""]
