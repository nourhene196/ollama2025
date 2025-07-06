#!/usr/bin/env python3
"""
Service Ollama pour la communication avec llama3.2:1b
"""

import requests
import json
from typing import Optional
from config import Config

class OllamaService:
    """Service pour communiquer avec Ollama/llama3.2:1b"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = 120  # Plus de temps pour le modèle compact
        
    def is_available(self) -> bool:
        """Vérifie si Ollama est disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def is_model_available(self) -> bool:
        """Vérifie si llama3.2:1b est disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(self.model in model.get('name', '') for model in models)
            return False
        except requests.RequestException:
            return False
    
    def generate_text(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Génère du texte avec llama3.2:1b"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,        # Plus déterministe pour la cuisine
                    "top_p": 0.8,             # Réponses plus focalisées
                    "max_tokens": 800,        # Limiter la longueur
                    "repeat_penalty": 1.1     # Éviter répétitions
                }
            }
            
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
            print(f"Erreur Ollama: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Erreur JSON: {e}")
            return None
    
    def test_connection(self) -> dict:
        """Teste la connexion et retourne le statut"""
        result = {
            'ollama_available': False,
            'model_available': False,
            'test_response': None,
            'error': None
        }
        
        try:
            # Test Ollama
            result['ollama_available'] = self.is_available()
            
            if result['ollama_available']:
                # Test modèle
                result['model_available'] = self.is_model_available()
                
                if result['model_available']:
                    # Test génération
                    test_response = self.generate_text(
                        "Dis bonjour en français et confirme que tu peux créer des recettes",
                        "Tu es un chef cuisinier français expert"
                    )
                    result['test_response'] = test_response
            
        except Exception as e:
            result['error'] = str(e)
        
        return result