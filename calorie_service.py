#!/usr/bin/env python3
"""
Service de calcul de calories avec llama3.2:1b
"""

import re
from typing import List, Dict, Any, Optional
from models import NutritionAnalysis, CalorieCalculation, Recipe, DataManager
from ollama_service import OllamaService
from config import Config

class CalorieService:
    """Service pour le calcul de calories avec IA uniquement"""
    
    def __init__(self, ollama_service: OllamaService, data_manager: DataManager, config: Config):
        self.ollama_service = ollama_service
        self.data_manager = data_manager
        self.config = config
        
        # Facteurs de conversion
        self.conversion_factors = {
            'g': 1.0, 'kg': 1000.0, 'ml': 1.0, 'l': 1000.0,
            'tasse': 240.0, 'cuillère': 15.0, 'c. à soupe': 15.0,
            'c. à café': 5.0, 'pincée': 2.0, 'portion': 150.0,
            'unité': 100.0, 'pièce': 100.0, 'gousse': 5.0,
            'tranche': 30.0, 'poignée': 50.0
        }
    
    def analyze_nutrition_with_ai(self, recipe: Recipe) -> Optional[NutritionAnalysis]:
        """Analyse nutritionnelle avec llama3.2:1b - OBLIGATOIRE"""
        # Vérifier que llama3.2:1b est disponible
        if not self.ollama_service.is_available():
            raise ConnectionError("❌ Ollama n'est pas disponible. Démarrez Ollama avec: ollama serve")
        
        if not self.ollama_service.is_model_available():
            raise ConnectionError("❌ llama3.2:1b n'est pas disponible. Installez avec: ollama pull llama3.2:1b")
        
        # Créer le prompt pour l'analyse nutritionnelle
        ingredients_str = ", ".join([f"{ing['name']} ({ing['quantity']} {ing['unit']})" 
                                   for ing in recipe.ingredients])
        
        prompt = self.config.PROMPTS['nutrition_prompt'].format(
            dish_name=recipe.title,
            ingredients=ingredients_str
        )
        
        # Générer l'analyse avec llama3.2:1b
        print(f"🤖 Analyse nutritionnelle avec llama3.2:1b...")
        response = self.ollama_service.generate_text(
            prompt,
            self.config.PROMPTS['calories_system']
        )
        
        if not response:
            raise RuntimeError("❌ llama3.2:1b n'a pas pu générer d'analyse nutritionnelle")
        
        # Parser la réponse
        analysis = self._parse_nutrition_response(response)
        
        if not analysis:
            # Si le parsing échoue, faire un calcul basique + IA pour les conseils
            basic_analysis = self._calculate_basic_nutrition(recipe)
            
            # Demander juste des conseils à l'IA
            advice_prompt = f"Donne des conseils santé courts pour ce plat: {recipe.title} ({basic_analysis.total_calories:.0f} kcal, {basic_analysis.total_proteins:.0f}g protéines)"
            advice = self.ollama_service.generate_text(advice_prompt, "Tu es nutritionniste. Réponds en 1-2 phrases.")
            
            return NutritionAnalysis(
                total_calories=basic_analysis.total_calories,
                total_proteins=basic_analysis.total_proteins,
                total_carbs=basic_analysis.total_carbs,
                total_fats=basic_analysis.total_fats,
                health_tips=advice or "Plat équilibré, à consommer avec modération."
            )
        
        return analysis
    
    def calculate_meal_calories(self, foods_data: List[Dict[str, Any]]) -> List[CalorieCalculation]:
        """Calcule les calories pour une liste d'aliments - avec IA pour conseils"""
        if not foods_data:
            raise ValueError("❌ Aucun aliment à analyser")
        
        calculations = []
        
        for item in foods_data:
            calc = self._calculate_single_ingredient(
                item.get('name', ''),
                item.get('quantity', 0),
                item.get('unit', 'g')
            )
            if calc:
                calculations.append(calc)
        
        # Si llama3.2:1b est disponible, ajouter des conseils IA
        if calculations and self.ollama_service.is_available() and self.ollama_service.is_model_available():
            total_calories = sum(calc.total_calories for calc in calculations)
            foods_list = ", ".join([calc.ingredient_name for calc in calculations])
            
            advice_prompt = f"Conseils nutritionnels courts pour ce repas: {foods_list} (Total: {total_calories:.0f} kcal)"
            advice = self.ollama_service.generate_text(
                advice_prompt, 
                "Tu es nutritionniste. Donne 1-2 conseils courts en français."
            )
            
            # Stocker les conseils pour utilisation ultérieure
            if advice and calculations:
                # Les conseils seront utilisés dans l'interface
                pass
        
        return calculations
    
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
    
    def _parse_nutrition_response(self, response: str) -> Optional[NutritionAnalysis]:
        """Parse la réponse nutritionnelle de llama3.2:1b"""
        try:
            lines = response.strip().split('\n')
            nutrition_data = {
                'calories': 0,
                'proteins': 0,
                'carbs': 0,
                'fats': 0,
                'tips': ''
            }
            
            for line in lines:
                line = line.strip()
                line_upper = line.upper()
                
                if 'CALORIES_TOTALES:' in line_upper or 'CALORIES:' in line_upper:
                    calories_match = re.search(r'(\d+(?:\.\d+)?)', line)
                    if calories_match:
                        nutrition_data['calories'] = float(calories_match.group(1))
                        
                elif 'PROTEINES:' in line_upper or 'PROTÉINES:' in line_upper:
                    proteins_match = re.search(r'(\d+(?:\.\d+)?)', line)
                    if proteins_match:
                        nutrition_data['proteins'] = float(proteins_match.group(1))
                        
                elif 'GLUCIDES:' in line_upper:
                    carbs_match = re.search(r'(\d+(?:\.\d+)?)', line)
                    if carbs_match:
                        nutrition_data['carbs'] = float(carbs_match.group(1))
                        
                elif 'LIPIDES:' in line_upper:
                    fats_match = re.search(r'(\d+(?:\.\d+)?)', line)
                    if fats_match:
                        nutrition_data['fats'] = float(fats_match.group(1))
                        
                elif 'CONSEILS_NUTRITION:' in line_upper:
                    nutrition_data['tips'] = line.split(':', 1)[1].strip()
            
            # Validation des données
            if nutrition_data['calories'] > 0:
                return NutritionAnalysis(
                    total_calories=nutrition_data['calories'],
                    total_proteins=nutrition_data['proteins'],
                    total_carbs=nutrition_data['carbs'],
                    total_fats=nutrition_data['fats'],
                    health_tips=nutrition_data['tips']
                )
            
            return None
            
        except Exception as e:
            print(f"Erreur parsing nutrition: {e}")
            return None
    
    def _calculate_basic_nutrition(self, recipe: Recipe) -> NutritionAnalysis:
        """Calcul nutritionnel de base à partir de la base de données"""
        total_calories = 0
        total_proteins = 0
        total_carbs = 0
        total_fats = 0
        
        for ingredient_info in recipe.ingredients:
            ingredient = self.data_manager.get_ingredient(ingredient_info['name'])
            if ingredient:
                quantity_g = self._convert_to_grams(
                    ingredient_info['quantity'], 
                    ingredient_info['unit']
                )
                factor = quantity_g / 100.0
                
                total_calories += ingredient.calories_per_100g * factor
                total_proteins += ingredient.proteins * factor
                total_carbs += ingredient.carbs * factor
                total_fats += ingredient.fats * factor
        
        return NutritionAnalysis(
            total_calories=total_calories,
            total_proteins=total_proteins,
            total_carbs=total_carbs,
            total_fats=total_fats,
            health_tips="Calcul basé sur la base de données nutritionnelles"
        )