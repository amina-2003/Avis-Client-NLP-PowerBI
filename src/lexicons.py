"""Lexiques francais (valeurs normalisees : minuscules, sans accents). Volontairement simples et lisibles."""
POS = set("""bon bonne bons bien excellent excellente parfait parfaite parfaitement impeccable impeccables rapide rapides rapidement
efficace efficaces satisfait satisfaits satisfaisante satisfaisant ravi ravis attractif attractifs competitif competitifs avantageux
avantageuse interessant interessante interessantes raisonnable solide solides robuste soigne soignee soignees irreprochable reactif
disponible competent competents professionnel agreable recommande recommandons recommandez fiable genereuse genereux superbe super
merci ponctuel ponctuelle plaisir remarquable confortable bas bonne surprise heureusement ecoute conseil""".split())
NEG = set("""cher chers chere excessif excessifs abusif abusifs eleve eleves defectueux defectueuse defectueuses decevant decevante decevants
decu decus casse casses cassee cassees fragile fragiles retard retards lent lente lents lentes catastrophique injoignable desagreable
desorganise insuffisant insuffisante insuffisantes mauvais mauvaise mauvaises probleme problemes abime abimee abimes incomplet incomplete
baclees baclee rouille crevent creve hesitons songeons perdu ecrase frein baisse hausse bricolage impossible tomber laisses
use usent""".split())
NEGATORS = {"pas", "jamais", "aucun", "aucune", "sans", "non"}
NEUTRAL_MARKERS = ["sans plus", "rien de plus", "rien de particulier", "rien a signaler", "rien de marquant", "rien d'exceptionnel",
                   "correct", "correcte", "corrects", "moyen", "moyenne", "acceptable", "acceptables", "standard", "standards",
                   "honnete", "dans la norme", "dans la moyenne", "ni bonne ni mauvaise", "ni cher ni", "comme un autre", "peut mieux faire",
                   "inchanges", "conforme"]

# themes : mots entiers ; suffixe '*' = prefixe
THEME_WORDS = {
 "Prix": ["prix","tarif","tarifs","tarification","tarifaire","tarifaires","cout","remise","remises","cher","chers","marge","budget","promotion","promotions","onereux","abordable"],
 "Qualité": ["qualite","fabrication","finition","finitions","defaut","defauts","defectueux","defectueuse","defectueuses","solide","solides","robuste","fragile","fragiles",
             "casse*","durabilite","materiaux","use","soudure*","rouille*","creve*","crevent","piece","pieces","finis","fini","baclees"],
 "Livraison": ["livraison","livraisons","livre","colis","expedition","expeditions","delai","delais","retard","retards","emballage","reapprovisionnement",
               "conditionnement","incomplete","arrive","arrivee","expedie","emballe","stock"],
 "Support": ["support","commercial","service client","interlocuteur","assistance","conseiller","apres-vente","relancer","reponse","reponses","joindre",
             "reclamation","reclamations","equipe","suivi commercial","suivi de notre compte","aucun suivi","suivi apres","accompagnement","sav","rappelle","mails"],
}
THEME_PRIORITY = ["Livraison", "Support", "Prix", "Qualité"]   # departage en cas d'egalite
