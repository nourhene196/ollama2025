import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import pandas as pd
import json
import os
import sqlite3
import requests
import threading
from datetime import datetime
#!/usr/bin/env python3
"""
Assistant Culinaire & Calories
Application principale avec interface graphique

Génération de recettes avec TinyLlama via Ollama
Calcul de calories avec base de données nutritionnelles

Auteur: Assistant IA
Version: 1.0.0
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# Ajouter le répertoire courant au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
    from gui_main import MainApplication
    from ollama_client import test_ollama_connection
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print("Assurez-vous que tous les fichiers sont présents dans le même répertoire")
    sys.exit(1)

def setup_logging():
    """Configure le système de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_requirements():
    """Vérifie les dépendances requises"""
    required_packages = [
        'tkinter', 'requests', 'pandas', 'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'requests':
                import requests
            elif package == 'pandas':
                import pandas
            elif package == 'numpy':
                import numpy
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        error_msg = f"Packages manquants: {', '.join(missing_packages)}\n"
        error_msg += "Installez-les avec: pip install " + ' '.join(missing_packages)
        print(error_msg)
        return False
    
    return True

def create_sample_data():
    """Crée des données d'exemple si nécessaires"""
    config = Config()
    config.ensure_data_dir()
    
    # Créer un fichier CSV d'exemple s'il n'existe pas
    if not os.path.exists(config.CALORIES_CSV):
        import pandas as pd
        
        sample_data = [
            {"name": "tomate", "calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2, "fiber": 1.2, "category": "Légume"},
            {"name": "poulet", "calories": 239, "protein": 27.3, "carbs": 0, "fat": 13.6, "fiber": 0, "category": "Viande"},
            {"name": "riz", "calories": 365, "protein": 7.1, "carbs": 77.2, "fat": 0.7, "fiber": 1.3, "category": "Céréale"},
            {"name": "carotte", "calories": 41, "protein": 0.9, "carbs": 9.6, "fat": 0.2, "fiber": 2.8, "category": "Légume"},
            {"name": "oignon", "calories": 40, "protein": 1.1, "carbs": 9.3, "fat": 0.1, "fiber": 1.7, "category": "Légume"},
            {"name": "pomme de terre", "calories": 77, "protein": 2.1, "carbs": 17.6, "fat": 0.1, "fiber": 2.1, "category": "Légume"},
            {"name": "bœuf", "calories": 250, "protein": 26.1, "carbs": 0, "fat": 15.4, "fiber": 0, "category": "Viande"},
            {"name": "saumon", "calories": 208, "protein": 25.4, "carbs": 0, "fat": 10.4, "fiber": 0, "category": "Poisson"},
            {"name": "œuf", "calories": 155, "protein": 13.0, "carbs": 1.1, "fat": 11.0, "fiber": 0, "category": "Produit laitier"},
            {"name": "lait", "calories": 42, "protein": 3.4, "carbs": 5.0, "fat": 1.0, "fiber": 0, "category": "Produit laitier"},
            {"name": "fromage", "calories": 402, "protein": 25.0, "carbs": 1.3, "fat": 33.1, "fiber": 0, "category": "Produit laitier"},
            {"name": "pain", "calories": 265, "protein": 9.0, "carbs": 49.4, "fat": 3.2, "fiber": 2.7, "category": "Céréale"},
            {"name": "pâtes", "calories": 371, "protein": 13.0, "carbs": 74.7, "fat": 1.5, "fiber": 3.2, "category": "Céréale"},
            {"name": "huile d'olive", "calories": 884, "protein": 0, "carbs": 0, "fat": 100.0, "fiber": 0, "category": "Matière grasse"},
            {"name": "beurre", "calories": 717, "protein": 0.9, "carbs": 0.1, "fat": 81.1, "fiber": 0, "category": "Matière grasse"},
            {"name": "banane", "calories": 89, "protein": 1.1, "carbs": 22.8, "fat": 0.3, "fiber": 2.6, "category": "Fruit"},
            {"name": "pomme", "calories": 52, "protein": 0.3, "carbs": 13.8, "fat": 0.2, "fiber": 2.4, "category": "Fruit"},
            {"name": "épinard", "calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2, "category": "Légume"},
            {"name": "champignon", "calories": 22, "protein": 3.1, "carbs": 3.3, "fat": 0.3, "fiber": 1.0, "category": "Légume"},
            {"name": "ail", "calories": 149, "protein": 6.4, "carbs": 33.1, "fat": 0.5, "fiber": 2.1, "category": "Aromate"}
        ]
        
        df = pd.DataFrame(sample_data)
        df.to_csv(config.CALORIES_CSV, index=False, encoding='utf-8')
        print(f"Fichier de données créé: {config.CALORIES_CSV}")

def show_startup_info():
    """Affiche les informations de démarrage"""
    info_text = """
╔══════════════════════════════════════════════════════════════╗
║                 Assistant Culinaire & Calories               ║
║                         Version 1.0.0                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Fonctionnalités:                                           ║
║  • Génération de recettes avec TinyLlama                   ║
║  • Calcul détaillé des calories et nutriments              ║
║  • Interface graphique moderne                             ║
║  • Fonctionnement hors ligne                               ║
║                                                              ║
║  Prérequis:                                                 ║
║  • Python 3.7+                                             ║
║  • Ollama installé (optionnel)                             ║
║  • TinyLlama modèle (optionnel)                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(info_text)

def check_ollama_setup():
    """Vérifie la configuration d'Ollama"""
    print("Vérification de la configuration Ollama...")
    
    try:
        # Test de base sans importer l'application complète
        import requests
        
        # Test de connexion Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                print("✓ Ollama est disponible")
                
                # Vérifier TinyLlama
                models = response.json().get('models', [])
                tinyllama_found = any('tinyllama' in model.get('name', '') for model in models)
                
                if tinyllama_found:
                    print("✓ TinyLlama est disponible")
                    return "full"
                else:
                    print("⚠ TinyLlama non trouvé")
                    print("  Pour l'installer: ollama pull tinyllama")
                    return "partial"
            else:
                print("✗ Ollama ne répond pas correctement")
                return "offline"
                
        except requests.RequestException:
            print("✗ Ollama n'est pas accessible")
            print("  Pour le démarrer: ollama serve")
            return "offline"
            
    except ImportError:
        print("✗ Module requests non disponible")
        return "offline"

def show_usage_instructions():
    """Affiche les instructions d'utilisation"""
    instructions = """
═══════════════════════════════════════════════════════════════
                        GUIDE D'UTILISATION
═══════════════════════════════════════════════════════════════

🏠 INSTALLATION OLLAMA (Optionnel):
   1. Télécharger Ollama: https://ollama.ai/
   2. Installer Ollama sur votre système
   3. Démarrer Ollama: ollama serve
   4. Installer TinyLlama: ollama pull tinyllama

📱 UTILISATION DE L'APPLICATION:

   Onglet "Générateur de recettes":
   • Sélectionnez des ingrédients dans la liste
   • Choisissez le type de cuisine (optionnel)
   • Définissez la difficulté et le temps
   • Cliquez sur "Générer la recette"
   
   Onglet "Calculateur de calories":
   • Ajoutez des aliments avec leurs quantités
   • Cliquez sur "Calculer" pour l'analyse
   • Exportez les résultats en CSV
   • Comparez avec vos besoins quotidiens

   Onglet "Historique":
   • Consultez vos recettes générées
   • Supprimez les anciens éléments

📊 DONNÉES NUTRITIONNELLES:
   • Base de données intégrée avec 20+ aliments
   • Support des fichiers CSV Kaggle
   • Calculs précis des macronutriments

═══════════════════════════════════════════════════════════════
    """
    print(instructions)

def handle_startup_error(error):
    """Gère les erreurs de démarrage"""
    error_msg = f"""
Erreur lors du démarrage de l'application:
{str(error)}

Solutions possibles:
1. Vérifiez que Python 3.7+ est installé
2. Installez les dépendances: pip install requests pandas numpy
3. Vérifiez les permissions de fichier
4. Redémarrez l'application
    """
    
    print(error_msg)
    
    # Essayer d'afficher une messagebox si tkinter est disponible
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Masquer la fenêtre principale
        messagebox.showerror("Erreur de démarrage", error_msg)
        root.destroy()
    except:
        pass  # Si tkinter n'est pas disponible, on a déjà affiché l'erreur

def main():
    """Fonction principale"""
    try:
        # Configuration du logging
        setup_logging()
        logging.info("Démarrage de l'application Assistant Culinaire & Calories")
        
        # Affichage des informations de démarrage
        show_startup_info()
        
        # Vérification des dépendances
        print("Vérification des dépendances...")
        if not check_requirements():
            print("❌ Dépendances manquantes. Arrêt de l'application.")
            return 1
        print("✓ Toutes les dépendances sont installées")
        
        # Création des données d'exemple
        print("Vérification des données...")
        create_sample_data()
        print("✓ Données prêtes")
        
        # Vérification d'Ollama
        ollama_status = check_ollama_setup()
        if ollama_status == "offline":
            print("⚠ L'application fonctionnera en mode hors ligne")
            print("  Les recettes seront générées avec des modèles prédéfinis")
        
        # Instructions d'utilisation
        print("\n" + "="*60)
        print("APPLICATION PRÊTE À DÉMARRER")
        print("="*60)
        
        if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
            show_usage_instructions()
            return 0
        
        # Lancement de l'interface graphique
        print("Lancement de l'interface graphique...")
        logging.info("Lancement de l'interface utilisateur")
        
        app = MainApplication()
        app.run()
        
        logging.info("Application fermée normalement")
        print("Application fermée. Au revoir!")
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠ Application interrompue par l'utilisateur")
        logging.info("Application interrompue par l'utilisateur")
        return 0
        
    except Exception as e:
        logging.error(f"Erreur fatale: {e}", exc_info=True)
        handle_startup_error(e)
        return 1

def test_mode():
    """Mode test pour vérifier l'installation"""
    print("=== MODE TEST ===")
    
    print("1. Test des imports...")
    try:
        from config import Config
        from models import DataManager
        from ollama_client import OllamaClient
        print("   ✓ Imports réussis")
    except Exception as e:
        print(f"   ✗ Erreur d'import: {e}")
        return False
    
    print("2. Test de la configuration...")
    try:
        config = Config()
        config.ensure_data_dir()
        print("   ✓ Configuration OK")
    except Exception as e:
        print(f"   ✗ Erreur de configuration: {e}")
        return False
    
    print("3. Test du gestionnaire de données...")
    try:
        data_manager = DataManager(config)
        ingredients = data_manager.get_all_ingredients()
        print(f"   ✓ {len(ingredients)} ingrédients chargés")
    except Exception as e:
        print(f"   ✗ Erreur de données: {e}")
        return False
    
    print("4. Test du client Ollama...")
    try:
        ollama_client = OllamaClient(config)
        if ollama_client.is_available():
            print("   ✓ Ollama disponible")
            if ollama_client.is_model_available():
                print("   ✓ TinyLlama disponible")
            else:
                print("   ⚠ TinyLlama non disponible")
        else:
            print("   ⚠ Ollama non disponible (mode hors ligne)")
    except Exception as e:
        print(f"   ✗ Erreur Ollama: {e}")
    
    print("5. Test de l'interface...")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        print("   ✓ Interface graphique disponible")
    except Exception as e:
        print(f"   ✗ Erreur interface: {e}")
        return False
    
    print("\n=== TESTS TERMINÉS ===")
    print("L'application est prête à fonctionner!")
    return True

if __name__ == "__main__":
    # Gestion des arguments de ligne de commande
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--test', '-t', 'test']:
            sys.exit(0 if test_mode() else 1)
        elif arg in ['--help', '-h', 'help']:
            show_usage_instructions()
            sys.exit(0)
        elif arg in ['--ollama-test', 'ollama']:
            test_ollama_connection()
            sys.exit(0)
    
    # Lancement normal
    sys.exit(main())