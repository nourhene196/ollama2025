#!/usr/bin/env python3
"""
Configuration de l'application
"""
import os

class Config:
    """Configuration principale de l'application"""
    
    # Configuration Ollama
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama3.2:1b"  # Modèle compact spécialisé
    
    # Configuration de l'application
    APP_TITLE = "🍽️ Assistant Culinaire & Calories IA"
    APP_VERSION = "3.0.0"
    APP_GEOMETRY = "1600x1000"
    
    # Chemins des fichiers
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    CALORIES_CSV = os.path.join(DATA_DIR, "calories.csv")
    
    # Configuration des couleurs
    COLORS = {
        'primary': '#FF6B35',      # Orange vif
        'secondary': '#004E98',    # Bleu foncé
        'success': '#2ECC71',      # Vert
        'background': '#F8F9FA',   # Gris clair
        'card': '#FFFFFF',         # Blanc
        'accent': '#FFE066',       # Jaune
        'text': '#2C3E50'          # Gris foncé
    }
    
    # Configuration des polices
    FONTS = {
        'title': ('Segoe UI', 20, 'bold'),
        'heading': ('Segoe UI', 14, 'bold'),
        'default': ('Segoe UI', 11),
        'small': ('Segoe UI', 9),
        'button': ('Segoe UI', 12, 'bold')
    }
    
    # Prompts optimisés pour llama3.2:1b
    PROMPTS = {
        'recipe_system': """Tu es un chef cuisinier français expert. Réponds UNIQUEMENT en français.
        Format obligatoire: TITRE, INGRÉDIENTS, PRÉPARATION, TEMPS, DIFFICULTÉ, CONSEILS.""",
        
        'calories_system': """Tu es un nutritionniste expert. Analyse précisément en français.
        Format: CALORIES_TOTALES, PROTEINES, GLUCIDES, LIPIDES, CONSEILS_NUTRITION.""",
        
        'recipe_prompt': """Crée une recette française avec: {ingredients}

TITRE: [nom de recette créatif]

INGRÉDIENTS:
{ingredient_list}

PRÉPARATION:
1. [étape détaillée et claire]
2. [étape suivante]
3. [étape finale]

TEMPS: [X minutes]
DIFFICULTÉ: [Facile/Moyen/Difficile]
CONSEILS: [astuce du chef]""",
        
        'nutrition_prompt': """Analyse nutritionnelle pour: {dish_name}
Ingrédients: {ingredients}

CALORIES_TOTALES: [nombre précis] kcal
PROTEINES: [nombre] g
GLUCIDES: [nombre] g
LIPIDES: [nombre] g
CONSEILS_NUTRITION: [conseil santé français court et utile]"""
    }
    
    @classmethod
    def ensure_data_dir(cls):
        """Crée le répertoire de données s'il n'existe pas"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)