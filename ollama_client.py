"""
Client pour communiquer avec Ollama et TinyLlama
"""

import requests
import json
import time
from typing import Optional, Dict, Any
from config import Config

class OllamaClient:
    """Client pour interagir avec Ollama"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = 30
        
    def is_available(self) -> bool:
        """Vérifie si Ollama est disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def is_model_available(self) -> bool:
        """Vérifie si le modèle TinyLlama est disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(self.model in model.get('name', '') for model in models)
            return False
        except requests.RequestException:
            return False
    
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Génère du texte avec TinyLlama"""
        try:
            # Préparer le payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000,
                    "stop": ["</s>", "[/INST]"]
                }
            }
            
            # Ajouter le prompt système si fourni
            if system_prompt:
                payload["system"] = system_prompt
            
            # Faire la requête
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                print(f"Erreur API Ollama: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"Erreur de connexion Ollama: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON: {e}")
            return None
    
    def generate_recipe(self, ingredients: list) -> Optional[str]:
        """Génère une recette avec les ingrédients donnés"""
        ingredients_str = ", ".join(ingredients)
        
        prompt = self.config.PROMPTS['recipe_template'].format(
            ingredients=ingredients_str
        )
        
        system_prompt = self.config.PROMPTS['recipe_system']
        
        return self.generate_text(prompt, system_prompt)
    
    def pull_model(self) -> bool:
        """Télécharge le modèle TinyLlama si nécessaire"""
        try:
            payload = {"name": self.model}
            response = requests.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=300  # 5 minutes pour le téléchargement
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Récupère les informations sur le modèle"""
        try:
            payload = {"name": self.model}
            response = requests.post(
                f"{self.base_url}/api/show",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException:
            return None

class RecipeGenerator:
    """Générateur de recettes utilisant TinyLlama"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
    
    def generate_recipe(self, ingredients: list, cuisine_type: str = "", 
                       difficulty: str = "", prep_time: str = "") -> Optional[str]:
        """Génère une recette personnalisée"""
        
        # Construire le prompt personnalisé
        prompt_parts = [f"Crée une recette avec ces ingrédients: {', '.join(ingredients)}"]
        
        if cuisine_type:
            prompt_parts.append(f"Style de cuisine: {cuisine_type}")
        
        if difficulty:
            prompt_parts.append(f"Difficulté souhaitée: {difficulty}")
        
        if prep_time:
            prompt_parts.append(f"Temps de préparation maximum: {prep_time}")
        
        prompt_parts.append("""
        Format de réponse souhaité:
        TITRE: [nom accrocheur de la recette]
        
        INGRÉDIENTS:
        - [ingrédient] : [quantité précise]
        
        PRÉPARATION:
        1. [étape détaillée]
        2. [étape suivante]
        
        TEMPS: [temps de préparation]
        DIFFICULTÉ: [facile/moyen/difficile]
        CONSEILS: [astuces optionnelles]
        """)
        
        prompt = "\n".join(prompt_parts)
        
        return self.ollama_client.generate_text(
            prompt, 
            self.ollama_client.config.PROMPTS['recipe_system']
        )
    
    def parse_recipe_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse la réponse de TinyLlama en structure de données"""
        if not response:
            return None
        
        try:
            lines = response.strip().split('\n')
            recipe_data = {
                'title': '',
                'ingredients': [],
                'steps': [],
                'prep_time': '',
                'difficulty': '',
                'tips': ''
            }
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Identifier les sections
                if line.startswith('TITRE:'):
                    recipe_data['title'] = line.replace('TITRE:', '').strip()
                elif line.startswith('INGRÉDIENTS:'):
                    current_section = 'ingredients'
                elif line.startswith('PRÉPARATION:'):
                    current_section = 'steps'
                elif line.startswith('TEMPS:'):
                    recipe_data['prep_time'] = line.replace('TEMPS:', '').strip()
                elif line.startswith('DIFFICULTÉ:'):
                    recipe_data['difficulty'] = line.replace('DIFFICULTÉ:', '').strip()
                elif line.startswith('CONSEILS:'):
                    recipe_data['tips'] = line.replace('CONSEILS:', '').strip()
                elif current_section == 'ingredients' and line.startswith('-'):
                    recipe_data['ingredients'].append(line[1:].strip())
                elif current_section == 'steps' and (line.startswith(tuple('123456789'))):
                    recipe_data['steps'].append(line.strip())
            
            return recipe_data
            
        except Exception as e:
            print(f"Erreur lors du parsing de la recette: {e}")
            return None

def test_ollama_connection():
    """Fonction utilitaire pour tester la connexion Ollama"""
    config = Config()
    client = OllamaClient(config)
    
    print("Test de connexion Ollama...")
    if client.is_available():
        print("✓ Ollama est disponible")
        
        if client.is_model_available():
            print("✓ TinyLlama est disponible")
            
            # Test de génération
            test_response = client.generate_text("Dis bonjour en français")
            if test_response:
                print(f"✓ Test de génération réussi: {test_response[:50]}...")
            else:
                print("✗ Erreur lors du test de génération")
        else:
            print("✗ TinyLlama n'est pas disponible")
            print("Tentative de téléchargement...")
            if client.pull_model():
                print("✓ TinyLlama téléchargé avec succès")
            else:
                print("✗ Erreur lors du téléchargement")
    else:
        print("✗ Ollama n'est pas disponible")
        print("Assurez-vous qu'Ollama est installé et démarré")

if __name__ == "__main__":
    test_ollama_connection()