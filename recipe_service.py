#!/usr/bin/env python3
"""
Service de génération de recettes avec llama3.2:1b
"""

import re
from typing import List, Dict, Any, Optional
from models import Recipe
from ollama_service import OllamaService
from config import Config

class RecipeService:
    """Service pour la génération de recettes avec IA uniquement"""
    
    def __init__(self, ollama_service: OllamaService, config: Config):
        self.ollama_service = ollama_service
        self.config = config
    
    def generate_recipe(self, ingredients: List[str], cuisine_type: str = "", 
                       difficulty: str = "", prep_time: str = "") -> Optional[Recipe]:
        """Génère une recette avec llama3.2:1b - OBLIGATOIRE"""
        if not ingredients:
            raise ValueError("❌ Aucun ingrédient sélectionné")
        
        # Vérifier que llama3.2:1b est disponible
        if not self.ollama_service.is_available():
            raise ConnectionError("❌ Ollama n'est pas disponible. Démarrez Ollama avec: ollama serve")
        
        if not self.ollama_service.is_model_available():
            raise ConnectionError("❌ llama3.2:1b n'est pas disponible. Installez avec: ollama pull llama3.2:1b")
        
        # Créer le prompt
        ingredient_list = "\n".join([f"- {ing}" for ing in ingredients])
        prompt = self.config.PROMPTS['recipe_prompt'].format(
            ingredients=", ".join(ingredients),
            ingredient_list=ingredient_list
        )
        
        # Ajouter les options
        if cuisine_type:
            prompt += f"\nStyle de cuisine: {cuisine_type}"
        if difficulty:
            prompt += f"\nDifficulté souhaitée: {difficulty}"
        if prep_time:
            prompt += f"\nTemps maximum: {prep_time}"
        
        # Générer avec llama3.2:1b
        print(f"🤖 Génération avec llama3.2:1b...")
        response = self.ollama_service.generate_text(
            prompt, 
            self.config.PROMPTS['recipe_system']
        )
        
        if not response:
            raise RuntimeError("❌ llama3.2:1b n'a pas pu générer de réponse")
        
        # Parser la réponse
        recipe = self._parse_recipe_response(response, ingredients)
        
        if not recipe:
            raise RuntimeError("❌ Impossible de parser la réponse de llama3.2:1b")
        
        return recipe
    
    def _parse_recipe_response(self, response: str, ingredients: List[str]) -> Optional[Recipe]:
        """Parse la réponse de llama3.2:1b pour extraire la recette"""
        try:
            lines = response.strip().split('\n')
            recipe_data = {
                'title': '',
                'ingredients': [],
                'steps': [],
                'prep_time': '30 minutes',
                'difficulty': 'Moyen',
                'tips': ''
            }
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Identifier les sections
                line_upper = line.upper()
                if line_upper.startswith('TITRE:'):
                    recipe_data['title'] = line[6:].strip()
                elif line_upper.startswith('INGRÉDIENTS:') or line_upper.startswith('INGREDIENTS:'):
                    current_section = 'ingredients'
                elif line_upper.startswith('PRÉPARATION:') or line_upper.startswith('PREPARATION:'):
                    current_section = 'steps'
                elif line_upper.startswith('TEMPS:'):
                    recipe_data['prep_time'] = line[6:].strip()
                elif line_upper.startswith('DIFFICULTÉ:') or line_upper.startswith('DIFFICULTE:'):
                    recipe_data['difficulty'] = line.split(':', 1)[1].strip()
                elif line_upper.startswith('CONSEILS:'):
                    recipe_data['tips'] = line[9:].strip()
                elif current_section == 'ingredients' and (line.startswith('-') or line.startswith('•')):
                    ing_text = line[1:].strip()
                    parsed_ing = self._parse_ingredient_line(ing_text)
                    if parsed_ing:
                        recipe_data['ingredients'].append(parsed_ing)
                elif current_section == 'steps' and (line[0].isdigit() or line.startswith('-')):
                    step = re.sub(r'^\d+\.?\s*', '', line)
                    step = re.sub(r'^-\s*', '', step)
                    if step:
                        recipe_data['steps'].append(step.strip())
            
            # Validation et fallbacks
            if not recipe_data['title']:
                recipe_data['title'] = f"Délicieux plat aux {', '.join(ingredients[:3])}"
            
            if not recipe_data['ingredients']:
                recipe_data['ingredients'] = [
                    {"name": ing, "quantity": 200, "unit": "g"} 
                    for ing in ingredients
                ]
            
            if not recipe_data['steps']:
                recipe_data['steps'] = [
                    "Préparer tous les ingrédients",
                    "Suivre les techniques culinaires appropriées",
                    "Assaisonner selon le goût",
                    "Servir chaud"
                ]
            
            return Recipe(
                title=recipe_data['title'],
                ingredients=recipe_data['ingredients'],
                steps=recipe_data['steps'],
                prep_time=recipe_data['prep_time'],
                difficulty=recipe_data['difficulty'],
                tips=recipe_data['tips']
            )
            
        except Exception as e:
            print(f"Erreur parsing recette: {e}")
            return None
    
    def _parse_ingredient_line(self, ingredient_text: str) -> Optional[Dict[str, Any]]:
        """Parse une ligne d'ingrédient"""
        try:
            # Nettoyer le texte
            ingredient_text = ingredient_text.strip()
            
            # Patterns pour extraire quantité et unité
            patterns = [
                r'([^:]+):\s*(\d+(?:\.\d+)?)\s*([a-zA-Zàâäéèêëïîôöùûüÿç]*)',  # nom: quantité unité
                r'(\d+(?:\.\d+)?)\s*([a-zA-Zàâäéèêëïîôöùûüÿç]+)\s+(.+)',      # quantité unité nom
                r'([^-]+)-\s*(\d+(?:\.\d+)?)\s*([a-zA-Zàâäéèêëïîôöùûüÿç]*)',  # nom - quantité unité
            ]
            
            for pattern in patterns:
                match = re.search(pattern, ingredient_text, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 3:
                        # Déterminer l'ordre: nom/quantité/unité
                        if match.group(1).replace('.', '').replace(',', '').isdigit():
                            # Pattern: quantité unité nom
                            quantity = float(match.group(1).replace(',', '.'))
                            unit = match.group(2).strip()
                            name = match.group(3).strip()
                        else:
                            # Pattern: nom : quantité unité
                            name = match.group(1).strip()
                            quantity = float(match.group(2).replace(',', '.'))
                            unit = match.group(3).strip() if match.group(3) else "g"
                        
                        return {
                            "name": name,
                            "quantity": quantity,
                            "unit": unit if unit else "g"
                        }
            
            # Fallback: juste le nom
            return {
                "name": ingredient_text.strip(),
                "quantity": 200,
                "unit": "g"
            }
            
        except Exception as e:
            print(f"Erreur parsing ingrédient '{ingredient_text}': {e}")
            return {
                "name": ingredient_text.strip(),
                "quantity": 200,
                "unit": "g"
            }