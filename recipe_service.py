"""
Service de génération de recettes
"""

from typing import List, Optional, Dict, Any
from models import Recipe, DataManager
from ollama_client import OllamaClient, RecipeGenerator
import re

class RecipeService:
    """Service principal pour la génération de recettes"""
    
    def __init__(self, data_manager: DataManager, ollama_client: OllamaClient):
        self.data_manager = data_manager
        self.ollama_client = ollama_client
        self.recipe_generator = RecipeGenerator(ollama_client)
        
    def generate_recipe(self, selected_ingredients: List[str], 
                       cuisine_type: str = "", difficulty: str = "", 
                       prep_time: str = "") -> Optional[Recipe]:
        """Génère une recette complète"""
        
        if not selected_ingredients:
            return None
        
        # Vérifier la disponibilité d'Ollama
        if not self.ollama_client.is_available():
            return self._generate_fallback_recipe(selected_ingredients)
        
        # Générer la recette avec TinyLlama
        raw_response = self.recipe_generator.generate_recipe(
            selected_ingredients, cuisine_type, difficulty, prep_time
        )
        
        if not raw_response:
            return self._generate_fallback_recipe(selected_ingredients)
        
        # Parser la réponse
        parsed_recipe = self.recipe_generator.parse_recipe_response(raw_response)
        
        if not parsed_recipe:
            return self._generate_fallback_recipe(selected_ingredients)
        
        # Créer l'objet Recipe
        recipe = self._create_recipe_object(parsed_recipe, selected_ingredients)
        
        # Calculer les calories
        recipe.calculate_total_calories(self.data_manager.ingredients_db)
        
        return recipe
    
    def _create_recipe_object(self, parsed_data: Dict[str, Any], 
                            selected_ingredients: List[str]) -> Recipe:
        """Crée un objet Recipe à partir des données parsées"""
        
        # Traiter les ingrédients
        ingredients_list = []
        for ingredient_text in parsed_data.get('ingredients', []):
            parsed_ingredient = self._parse_ingredient_line(ingredient_text)
            if parsed_ingredient:
                ingredients_list.append(parsed_ingredient)
        
        # Si pas d'ingrédients parsés, utiliser les ingrédients sélectionnés
        if not ingredients_list:
            ingredients_list = [
                {"name": ing, "quantity": 1, "unit": "portion"} 
                for ing in selected_ingredients
            ]
        
        return Recipe(
            title=parsed_data.get('title', 'Recette délicieuse'),
            ingredients=ingredients_list,
            steps=parsed_data.get('steps', ['Préparer les ingrédients']),
            prep_time=parsed_data.get('prep_time', '30 minutes'),
            difficulty=parsed_data.get('difficulty', 'Facile'),
            total_calories=0.0
        )
    
    def _parse_ingredient_line(self, ingredient_text: str) -> Optional[Dict[str, Any]]:
        """Parse une ligne d'ingrédient du format 'nom : quantité unité'"""
        try:
            # Nettoyer le texte
            ingredient_text = ingredient_text.strip()
            
            # Patterns pour extraire quantité et unité
            patterns = [
                r'([^:]+):\s*(\d+(?:\.\d+)?)\s*([a-zA-Zàâäéèêëïîôöùûüÿç]*)',
                r'([^:]+):\s*(\d+(?:\.\d+)?)',
                r'([^-]+)-\s*(\d+(?:\.\d+)?)\s*([a-zA-Zàâäéèêëïîôöùûüÿç]*)',
            ]
            
            for pattern in patterns:
                match = re.match(pattern, ingredient_text, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    quantity = float(match.group(2))
                    unit = match.group(3).strip() if len(match.groups()) > 2 else "g"
                    
                    return {
                        "name": name,
                        "quantity": quantity,
                        "unit": unit if unit else "g"
                    }
            
            # Si aucun pattern ne fonctionne, retourner l'ingrédient avec quantité par défaut
            return {
                "name": ingredient_text,
                "quantity": 1,
                "unit": "portion"
            }
            
        except Exception as e:
            print(f"Erreur lors du parsing de l'ingrédient '{ingredient_text}': {e}")
            return None
    
    def _generate_fallback_recipe(self, selected_ingredients: List[str]) -> Recipe:
        """Génère une recette de base si Ollama n'est pas disponible"""
        
        # Recettes prédéfinies selon les ingrédients
        fallback_recipes = self._get_fallback_recipes()
        
        # Chercher une recette qui correspond aux ingrédients
        best_match = None
        max_matches = 0
        
        for recipe_template in fallback_recipes:
            matches = sum(1 for ing in selected_ingredients 
                         if ing.lower() in recipe_template['ingredients_needed'])
            if matches > max_matches:
                max_matches = matches
                best_match = recipe_template
        
        if best_match:
            # Adapter la recette aux ingrédients sélectionnés
            ingredients_list = []
            for ing in selected_ingredients:
                ingredients_list.append({
                    "name": ing,
                    "quantity": 1,
                    "unit": "portion"
                })
            
            recipe = Recipe(
                title=best_match['title'],
                ingredients=ingredients_list,
                steps=best_match['steps'],
                prep_time=best_match['prep_time'],
                difficulty=best_match['difficulty']
            )
            
            # Calculer les calories
            recipe.calculate_total_calories(self.data_manager.ingredients_db)
            return recipe
        
        # Recette générique
        return Recipe(
            title=f"Plat aux {', '.join(selected_ingredients[:3])}",
            ingredients=[{"name": ing, "quantity": 1, "unit": "portion"} 
                        for ing in selected_ingredients],
            steps=[
                "Préparer et nettoyer tous les ingrédients",
                "Faire revenir les ingrédients dans une poêle",
                "Assaisonner selon votre goût",
                "Cuire jusqu'à ce que ce soit tendre",
                "Servir chaud"
            ],
            prep_time="30 minutes",
            difficulty="Facile"
        )
    
    def _get_fallback_recipes(self) -> List[Dict[str, Any]]:
        """Retourne des recettes prédéfinies"""
        return [
            {
                'title': 'Sauté de légumes',
                'ingredients_needed': ['carotte', 'oignon', 'tomate', 'courgette'],
                'steps': [
                    'Couper tous les légumes en dés',
                    'Faire chauffer l\'huile dans une poêle',
                    'Faire revenir l\'oignon jusqu\'à transparence',
                    'Ajouter les autres légumes et cuire 15 minutes',
                    'Assaisonner et servir'
                ],
                'prep_time': '25 minutes',
                'difficulty': 'Facile'
            },
            {
                'title': 'Omelette aux légumes',
                'ingredients_needed': ['œuf', 'tomate', 'oignon', 'fromage'],
                'steps': [
                    'Battre les œufs dans un bol',
                    'Faire revenir les légumes dans une poêle',
                    'Verser les œufs battus sur les légumes',
                    'Ajouter le fromage et plier l\'omelette',
                    'Servir immédiatement'
                ],
                'prep_time': '15 minutes',
                'difficulty': 'Facile'
            },
            {
                'title': 'Riz sauté',
                'ingredients_needed': ['riz', 'œuf', 'carotte', 'oignon'],
                'steps': [
                    'Cuire le riz à l\'eau bouillante',
                    'Faire revenir les légumes dans une poêle',
                    'Ajouter le riz cuit et mélanger',
                    'Incorporer les œufs battus',
                    'Cuire en remuant jusqu\'à ce que les œufs soient pris'
                ],
                'prep_time': '30 minutes',
                'difficulty': 'Moyen'
            },
            {
                'title': 'Salade complète',
                'ingredients_needed': ['tomate', 'carotte', 'œuf', 'fromage'],
                'steps': [
                    'Laver et couper les légumes',
                    'Cuire les œufs durs',
                    'Disposer tous les ingrédients dans un saladier',
                    'Assaisonner avec huile et vinaigre',
                    'Mélanger et servir frais'
                ],
                'prep_time': '20 minutes',
                'difficulty': 'Facile'
            }
        ]
