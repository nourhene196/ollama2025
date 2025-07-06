#!/usr/bin/env python3
"""
Modèles de données pour l'application
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd
import os

@dataclass
class Ingredient:
    """Modèle pour un ingrédient"""
    name: str
    calories_per_100g: float
    proteins: float = 0.0
    carbs: float = 0.0
    fats: float = 0.0
    fiber: float = 0.0
    category: str = "Autre"

@dataclass
class Recipe:
    """Modèle pour une recette"""
    title: str
    ingredients: List[Dict[str, any]]
    steps: List[str]
    prep_time: str
    difficulty: str
    tips: str = ""
    total_calories: float = 0.0
    total_proteins: float = 0.0
    total_carbs: float = 0.0
    total_fats: float = 0.0

@dataclass
class NutritionAnalysis:
    """Analyse nutritionnelle"""
    total_calories: float
    total_proteins: float
    total_carbs: float
    total_fats: float
    health_tips: str = ""

@dataclass
class CalorieCalculation:
    """Résultat d'un calcul de calories"""
    ingredient_name: str
    quantity: float
    unit: str
    calories_per_100g: float
    total_calories: float
    proteins: float
    carbs: float
    fats: float
    fiber: float

class DataManager:
    """Gestionnaire des données nutritionnelles"""
    
    def __init__(self, config):
        self.config = config
        self.ingredients_db: Dict[str, Ingredient] = {}
        self.load_data()
    
    def load_data(self):
        """Charge les données depuis les fichiers CSV"""
        try:
            if os.path.exists(self.config.CALORIES_CSV):
                df = pd.read_csv(self.config.CALORIES_CSV)
                self._process_data(df)
            else:
                self._create_sample_data()
        except Exception as e:
            print(f"Erreur chargement données: {e}")
            self._create_sample_data()
    
    def _process_data(self, df: pd.DataFrame):
        """Traite les données du fichier CSV"""
        for _, row in df.iterrows():
            try:
                name = str(row.get('name', '')).lower().strip()
                calories = float(row.get('calories', 0))
                if name and calories > 0:
                    self.ingredients_db[name] = Ingredient(
                        name=name,
                        calories_per_100g=calories,
                        proteins=float(row.get('protein', 0)),
                        carbs=float(row.get('carbs', 0)),
                        fats=float(row.get('fat', 0)),
                        fiber=float(row.get('fiber', 0)),
                        category=str(row.get('category', 'Autre'))
                    )
            except (ValueError, KeyError):
                continue
    
    def _create_sample_data(self):
        """Crée des données d'exemple"""
        sample_ingredients = [
            ("tomate", 18, 0.9, 3.9, 0.2, 1.2, "Légume"),
            ("poulet", 239, 27.3, 0, 13.6, 0, "Viande"),
            ("riz", 365, 7.1, 77.2, 0.7, 1.3, "Céréale"),
            ("carotte", 41, 0.9, 9.6, 0.2, 2.8, "Légume"),
            ("oignon", 40, 1.1, 9.3, 0.1, 1.7, "Légume"),
            ("pomme de terre", 77, 2.1, 17.6, 0.1, 2.1, "Légume"),
            ("bœuf", 250, 26.1, 0, 15.4, 0, "Viande"),
            ("saumon", 208, 25.4, 0, 10.4, 0, "Poisson"),
            ("œuf", 155, 13.0, 1.1, 11.0, 0, "Produit laitier"),
            ("lait", 42, 3.4, 5.0, 1.0, 0, "Produit laitier"),
            ("fromage", 402, 25.0, 1.3, 33.1, 0, "Produit laitier"),
            ("pain", 265, 9.0, 49.4, 3.2, 2.7, "Céréale"),
            ("pâtes", 371, 13.0, 74.7, 1.5, 3.2, "Céréale"),
            ("huile d'olive", 884, 0, 0, 100.0, 0, "Matière grasse"),
            ("beurre", 717, 0.9, 0.1, 81.1, 0, "Matière grasse"),
            ("banane", 89, 1.1, 22.8, 0.3, 2.6, "Fruit"),
            ("pomme", 52, 0.3, 13.8, 0.2, 2.4, "Fruit"),
            ("épinard", 23, 2.9, 3.6, 0.4, 2.2, "Légume"),
            ("champignon", 22, 3.1, 3.3, 0.3, 1.0, "Légume"),
            ("ail", 149, 6.4, 33.1, 0.5, 2.1, "Aromate"),
            ("thym", 276, 9.1, 63.9, 7.4, 37.0, "Aromate"),
            ("basilic", 251, 14.4, 47.8, 4.1, 61.0, "Aromate"),
            ("persil", 292, 26.6, 50.6, 5.5, 26.7, "Aromate"),
            ("courgette", 17, 1.2, 3.1, 0.3, 1.0, "Légume"),
            ("aubergine", 25, 1.0, 5.9, 0.2, 3.0, "Légume")
        ]
        
        for name, calories, proteins, carbs, fats, fiber, category in sample_ingredients:
            self.ingredients_db[name.lower()] = Ingredient(
                name=name,
                calories_per_100g=calories,
                proteins=proteins,
                carbs=carbs,
                fats=fats,
                fiber=fiber,
                category=category
            )
    
    def get_ingredient(self, name: str) -> Optional[Ingredient]:
        """Récupère un ingrédient par nom"""
        return self.ingredients_db.get(name.lower())
    
    def get_all_ingredients(self) -> List[Ingredient]:
        """Retourne tous les ingrédients"""
        return list(self.ingredients_db.values())
    
    def get_ingredients_by_category(self, category: str) -> List[Ingredient]:
        """Retourne les ingrédients d'une catégorie"""
        return [ing for ing in self.ingredients_db.values() if ing.category == category]
    
    def get_categories(self) -> List[str]:
        """Retourne toutes les catégories"""
        return list(set(ing.category for ing in self.ingredients_db.values()))
    
    def search_ingredients(self, query: str) -> List[Ingredient]:
        """Recherche d'ingrédients par nom"""
        query = query.lower()
        return [ing for ing in self.ingredients_db.values() if query in ing.name.lower()]