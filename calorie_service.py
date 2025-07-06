"""
Service de calcul de calories
"""

from typing import List, Dict, Any, Optional, Tuple
from models import Ingredient, DataManager
from dataclasses import dataclass
import math

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

@dataclass
class MealAnalysis:
    """Analyse nutritionnelle d'un repas"""
    calculations: List[CalorieCalculation]
    total_calories: float
    total_proteins: float
    total_carbs: float
    total_fats: float
    total_fiber: float
    
    def get_macros_percentage(self) -> Dict[str, float]:
        """Calcule les pourcentages de macronutriments"""
        total_macros = self.total_proteins + self.total_carbs + self.total_fats
        if total_macros == 0:
            return {"proteins": 0, "carbs": 0, "fats": 0}
        
        return {
            "proteins": round((self.total_proteins / total_macros) * 100, 1),
            "carbs": round((self.total_carbs / total_macros) * 100, 1),
            "fats": round((self.total_fats / total_macros) * 100, 1)
        }

class CalorieService:
    """Service principal pour le calcul des calories"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        
        # Facteurs de conversion approximatifs
        self.conversion_factors = {
            'g': 1.0,
            'kg': 1000.0,
            'ml': 1.0,  # Pour les liquides, approximation 1ml = 1g
            'l': 1000.0,
            'litre': 1000.0,
            'tasse': 240.0,
            'cuillère': 15.0,
            'c. à soupe': 15.0,
            'c. à café': 5.0,
            'cuillère à soupe': 15.0,
            'cuillère à café': 5.0,
            'pincée': 2.0,
            'poignée': 50.0,
            'tranche': 30.0,
            'unité': 100.0,
            'pièce': 100.0,
            'portion': 150.0
        }
    
    def calculate_calories(self, ingredients_data: List[Dict[str, Any]]) -> MealAnalysis:
        """
        Calcule les calories pour une liste d'ingrédients
        Format: [{"name": str, "quantity": float, "unit": str}]
        """
        calculations = []
        
        for item in ingredients_data:
            calc = self._calculate_single_ingredient(
                item.get('name', ''),
                item.get('quantity', 0),
                item.get('unit', 'g')
            )
            if calc:
                calculations.append(calc)
        
        # Calculer les totaux
        total_calories = sum(calc.total_calories for calc in calculations)
        total_proteins = sum(calc.proteins for calc in calculations)
        total_carbs = sum(calc.carbs for calc in calculations)
        total_fats = sum(calc.fats for calc in calculations)
        total_fiber = sum(calc.fiber for calc in calculations)
        
        return MealAnalysis(
            calculations=calculations,
            total_calories=round(total_calories, 1),
            total_proteins=round(total_proteins, 1),
            total_carbs=round(total_carbs, 1),
            total_fats=round(total_fats, 1),
            total_fiber=round(total_fiber, 1)
        )
    
    def _calculate_single_ingredient(self, name: str, quantity: float, unit: str) -> Optional[CalorieCalculation]:
        """Calcule les calories pour un seul ingrédient"""
        
        # Chercher l'ingrédient dans la base de données
        ingredient = self.data_manager.get_ingredient(name)
        if not ingredient:
            # Essayer une recherche floue
            search_results = self.data_manager.search_ingredients(name)
            if search_results:
                ingredient = search_results[0]  # Prendre le premier résultat
        
        if not ingredient:
            return None
        
        # Convertir en grammes
        quantity_in_grams = self._convert_to_grams(quantity, unit)
        
        # Calculer les valeurs nutritionnelles
        factor = quantity_in_grams / 100.0
        
        return CalorieCalculation(
            ingredient_name=ingredient.name,
            quantity=quantity,
            unit=unit,
            calories_per_100g=ingredient.calories_per_100g,
            total_calories=ingredient.calories_per_100g * factor,
            proteins=ingredient.proteins * factor,
            carbs=ingredient.carbs * factor,
            fats=ingredient.fats * factor,
            fiber=ingredient.fiber * factor
        )
    
    def _convert_to_grams(self, quantity: float, unit: str) -> float:
        """Convertit une quantité en grammes"""
        unit_clean = unit.lower().strip()
        
        # Chercher dans les facteurs de conversion
        for unit_key, factor in self.conversion_factors.items():
            if unit_clean == unit_key.lower() or unit_clean in unit_key.lower():
                return quantity * factor
        
        # Si l'unité n'est pas trouvée, considérer comme grammes
        return quantity
    
    def get_daily_needs_comparison(self, analysis: MealAnalysis, 
                                 age: int = 30, gender: str = "M", 
                                 activity_level: str = "modéré") -> Dict[str, Any]:
        """Compare les apports avec les besoins quotidiens recommandés"""
        
        # Besoins caloriques de base (approximatifs)
        base_needs = self._calculate_daily_needs(age, gender, activity_level)
        
        return {
            'recommended_calories': base_needs['calories'],
            'current_calories': analysis.total_calories,
            'percentage_of_needs': round((analysis.total_calories / base_needs['calories']) * 100, 1),
            'remaining_calories': base_needs['calories'] - analysis.total_calories,
            'macros_comparison': {
                'proteins': {
                    'recommended': base_needs['proteins'],
                    'current': analysis.total_proteins,
                    'percentage': round((analysis.total_proteins / base_needs['proteins']) * 100, 1)
                },
                'carbs': {
                    'recommended': base_needs['carbs'],
                    'current': analysis.total_carbs,
                    'percentage': round((analysis.total_carbs / base_needs['carbs']) * 100, 1)
                },
                'fats': {
                    'recommended': base_needs['fats'],
                    'current': analysis.total_fats,
                    'percentage': round((analysis.total_fats / base_needs['fats']) * 100, 1)
                }
            }
        }
    
    def _calculate_daily_needs(self, age: int, gender: str, activity_level: str) -> Dict[str, float]:
        """Calcule les besoins nutritionnels quotidiens"""
        
        # Métabolisme de base approximatif
        if gender.upper() == 'M':
            bmr = 88.362 + (13.397 * 70) + (4.799 * 175) - (5.677 * age)  # Homme moyen
        else:
            bmr = 447.593 + (9.247 * 60) + (3.098 * 165) - (4.330 * age)  # Femme moyenne
        
        # Facteur d'activité
        activity_factors = {
            'sédentaire': 1.2,
            'léger': 1.375,
            'modéré': 1.55,
            'intense': 1.725,
            'très intense': 1.9
        }
        
        factor = activity_factors.get(activity_level, 1.55)
        total_calories = bmr * factor
        
        # Répartition des macronutriments (recommandations générales)
        proteins_calories = total_calories * 0.15  # 15% des calories
        carbs_calories = total_calories * 0.55     # 55% des calories
        fats_calories = total_calories * 0.30      # 30% des calories
        
        return {
            'calories': round(total_calories, 0),
            'proteins': round(proteins_calories / 4, 1),  # 4 cal/g
            'carbs': round(carbs_calories / 4, 1),        # 4 cal/g
            'fats': round(fats_calories / 9, 1)           # 9 cal/g
        }
    
    def suggest_ingredients_for_target(self, target_calories: float, 
                                     current_analysis: MealAnalysis) -> List[Dict[str, Any]]:
        """Suggère des ingrédients pour atteindre un objectif calorique"""
        
        remaining_calories = target_calories - current_analysis.total_calories
        
        if remaining_calories <= 0:
            return []
        
        suggestions = []
        
        # Catégories d'ingrédients avec leurs caractéristiques
        categories = {
            'Protéines': {'max_calories': 300, 'type': 'proteins'},
            'Légumes': {'max_calories': 100, 'type': 'vegetables'},
            'Féculents': {'max_calories': 400, 'type': 'carbs'},
            'Fruits': {'max_calories': 150, 'type': 'fruits'}
        }
        
        for category, info in categories.items():
            if remaining_calories <= 0:
                break
                
            # Trouver des ingrédients de cette catégorie
            ingredients = self.data_manager.get_ingredients_by_category(category)
            
            for ingredient in ingredients[:3]:  # Limiter à 3 suggestions par catégorie
                if remaining_calories <= 0:
                    break
                    
                # Calculer la quantité suggérée
                max_portion_calories = min(info['max_calories'], remaining_calories)
                suggested_grams = (max_portion_calories / ingredient.calories_per_100g) * 100
                
                if suggested_grams > 0:
                    suggestions.append({
                        'name': ingredient.name,
                        'quantity': round(suggested_grams, 0),
                        'unit': 'g',
                        'calories': round(max_portion_calories, 0),
                        'category': category
                    })
                    
                    remaining_calories -= max_portion_calories
        
        return suggestions[:10]  # Limiter à 10 suggestions
    
    def export_analysis_to_dict(self, analysis: MealAnalysis) -> Dict[str, Any]:
        """Exporte l'analyse en dictionnaire pour affichage"""
        return {
            'summary': {
                'total_calories': analysis.total_calories,
                'total_proteins': analysis.total_proteins,
                'total_carbs': analysis.total_carbs,
                'total_fats': analysis.total_fats,
                'total_fiber': analysis.total_fiber,
                'macros_percentage': analysis.get_macros_percentage()
            },
            'ingredients': [
                {
                    'name': calc.ingredient_name,
                    'quantity': calc.quantity,
                    'unit': calc.unit,
                    'calories_per_100g': calc.calories_per_100g,
                    'total_calories': calc.total_calories,
                    'proteins': calc.proteins,
                    'carbs': calc.carbs,
                    'fats': calc.fats,
                    'fiber': calc.fiber
                }
                for calc in analysis.calculations
            ]
        }