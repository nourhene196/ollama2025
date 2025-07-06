"""
Configuration de l'application
"""

import os

class Config:
    """Configuration principale de l'application"""
    
    # Configuration Ollama
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "tinyllama"
    
    # Configuration de l'application
    APP_TITLE = "Assistant Culinaire & Calories"
    APP_VERSION = "1.0.0"
    APP_GEOMETRY = "1200x800"
    
    # Chemins des fichiers
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    CALORIES_CSV = os.path.join(DATA_DIR, "calories.csv")
    INGREDIENTS_CSV = os.path.join(DATA_DIR, "ingredients.csv")
    
    # Configuration des couleurs
    COLORS = {
        'primary': '#2E86AB',
        'secondary': '#A23B72',
        'success': '#F18F01',
        'background': '#F8F9FA',
        'text': '#212529',
        'accent': '#E9ECEF'
    }
    
    # Configuration des polices
    FONTS = {
        'default': ('Arial', 10),
        'heading': ('Arial', 14, 'bold'),
        'title': ('Arial', 18, 'bold'),
        'small': ('Arial', 8)
    }
    
    # Messages système
    MESSAGES = {
        'error_ollama': "Erreur de connexion à Ollama. Vérifiez que le service est démarré.",
        'error_model': "Modèle TinyLlama non trouvé. Vérifiez l'installation.",
        'error_data': "Erreur lors du chargement des données.",
        'success_recipe': "Recette générée avec succès !",
        'success_calories': "Calcul des calories terminé !",
        'no_ingredients': "Veuillez sélectionner au moins un ingrédient.",
        'loading': "Chargement en cours..."
    }
    
    # Prompts pour TinyLlama
    PROMPTS = {
        'recipe_system': """Tu es un chef cuisinier expert. Génère une recette simple et délicieuse 
        avec les ingrédients fournis. Donne un titre, les ingrédients avec quantités, 
        et les étapes de préparation. Reste concis et pratique.""",
        
        'recipe_template': """Crée une recette avec ces ingrédients: {ingredients}
        
        Format de réponse:
        TITRE: [nom de la recette]
        
        INGRÉDIENTS:
        - [ingrédient 1] : [quantité]
        - [ingrédient 2] : [quantité]
        
        PRÉPARATION:
        1. [étape 1]
        2. [étape 2]
        
        TEMPS: [temps de préparation]
        DIFFICULTÉ: [facile/moyen/difficile]"""
    }
    
    @classmethod
    def ensure_data_dir(cls):
        """Crée le répertoire de données s'il n'existe pas"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)