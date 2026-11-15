"""Configuration et utilitaires partages. Tout parametre modifiable est ici."""
from pathlib import Path
import unicodedata, re

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data_raw"
OUT = ROOT / "output"          # donnees intermediaires
PBI = ROOT / "powerbi"         # tables pretes pour Power BI
DOCS = ROOT / "docs"

SEED = 42                      # reproductibilite
REVIEW_RATE = 0.22             # part des commandes ayant un avis
LAST_ORDER_CUTOFF = "2021-12-31"   # pas d'avis apres cette date (2022/2023 suspects, voir note)
TEST_PHRASE_SHARE = 0.30       # part des formulations reservees au jeu de test

THEMES = ["Prix", "Qualité", "Livraison", "Support", "Général"]

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def norm(s: str) -> str:
    """minuscule, sans accents, ponctuation -> espace"""
    s = strip_accents(str(s).lower())
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

SUBCATEGORIES = {  # reconstruit (non fourni dans l'archive) ; verifie sur les noms de produits
 1:("Vélos VTT","Vélos"),2:("Vélos de route","Vélos"),3:("Vélos de randonnée","Vélos"),
 4:("Guidons","Composants"),5:("Boîtiers de pédalier","Composants"),6:("Freins","Composants"),
 7:("Chaînes","Composants"),8:("Pédaliers","Composants"),9:("Dérailleurs","Composants"),
 10:("Fourches","Composants"),11:("Jeux de direction","Composants"),12:("Cadres VTT","Composants"),
 13:("Pédales","Composants"),14:("Cadres route","Composants"),15:("Selles","Composants"),
 16:("Cadres randonnée","Composants"),17:("Roues","Composants"),
 18:("Cuissards","Vêtements"),19:("Casquettes","Vêtements"),20:("Gants","Vêtements"),
 21:("Maillots","Vêtements"),22:("Shorts","Vêtements"),23:("Chaussettes","Vêtements"),
 24:("Collants","Vêtements"),25:("Gilets","Vêtements"),
 26:("Porte-vélos","Accessoires"),27:("Supports d'atelier","Accessoires"),28:("Bidons et porte-bidons","Accessoires"),
 29:("Produits d'entretien","Accessoires"),30:("Garde-boue","Accessoires"),31:("Casques","Accessoires"),
 32:("Sacs d'hydratation","Accessoires"),33:("Éclairages","Accessoires"),34:("Antivols","Accessoires"),
 35:("Sacoches","Accessoires"),36:("Pompes","Accessoires"),37:("Pneus et chambres","Accessoires"),
}

# Moteur NLP utilise pour alimenter Power BI : "ml" (modele entraine, par defaut) ou "lexique" (regles).
ENGINE = "ml"
MODELS = ROOT / "output" / "models"
