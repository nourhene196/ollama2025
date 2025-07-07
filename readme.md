# 🍽️ Assistant Culinaire & Calories IA
![image](https://github.com/user-attachments/assets/31df8e83-47af-43ab-b9b2-39f614b6a3b2)
![image](https://github.com/user-attachments/assets/97a11e72-3cc0-4ad4-9a33-a7f7d6563347)


[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-Required-green.svg)](https://ollama.ai/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-3.0.0-red.svg)]((https://github.com/nourhene196/ollama2025))

> **Application moderne de génération de recettes et calcul de calories utilisant l'IA llama3.2:1b via Ollama**

Une application Python avec interface graphique qui combine la génération intelligente de recettes et l'analyse nutritionnelle approfondie, alimentée par le modèle d'IA llama3.2:1b.

## ✨ Fonctionnalités

Génération de Recettes IA
- Sélection intuitive d'ingrédients avec interface moderne
- Options de personnalisation (cuisine, difficulté, temps)
- Génération 100% IA avec llama3.2:1b (1.3GB)
- Recettes françaises créatives et détaillées
- Export des recettes en format TXT

 Calculateur de Calories IA
- Base de données nutritionnelle intégrée (25+ aliments)
- Calcul précis des calories et macronutriments
- Analyse nutritionnelle approfondie par IA
- Conseils santé personnalisés par llama3.2:1b
- Export des analyses en format CSV

Interface Moderne
- Design moderne avec onglets séparés
- Interface intuitive et réactive
- Feedback visuel temps réel
- Messages d'aide intégrés
- Diagnostic automatique des problèmes

## 🚀 Installation

### Prérequis

- **Python 3.7+** ([Télécharger](https://www.python.org/downloads/))
- **Ollama** ([Télécharger](https://ollama.ai/download))
- **Connexion Internet** (pour télécharger le modèle)

### Étape 1: Cloner le projet

```bash    

git clone https://github.com/nourhene196/ollama2025.git
cd assistant-culinaire-ia
```

### Étape 2: Installer les dépendances Python

```bash
# Installer les modules requis
pip install requests pandas

# Vérifier l'installation
python --version  # Doit être 3.7+
```

### Étape 3: Installer et configurer Ollama

#### Windows
1. Téléchargez depuis [ollama.ai/download/windows](https://ollama.ai/download/windows)
2. Installez le fichier `.exe`
3. Redémarrez votre ordinateur

#### macOS
1. Téléchargez depuis [ollama.ai/download/mac](https://ollama.ai/download/mac)
2. Installez le fichier `.dmg`

#### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Étape 4: Démarrer Ollama

```bash
# Dans un terminal (gardez-le ouvert)
ollama serve
```

Vous devriez voir : `Ollama is running on http://localhost:11434`

### Étape 5: Installer le modèle llama3.2:1b

```bash
# Dans un NOUVEAU terminal
ollama pull llama3.2:1b
```

⏳ **Téléchargement :** ~1.3GB, patientez quelques minutes selon votre connexion.

### Étape 6: Vérifier l'installation

```bash
# Lister les modèles installés
ollama list

# Tester le modèle
ollama run llama3.2:1b "Bonjour, peux-tu créer une recette française ?"
```

## 🎯 Utilisation

### Lancement de l'application

```bash
# Assurez-vous qu'Ollama tourne (ollama serve)
python main.py
```

### Interface

L'application s'ouvre avec 3 onglets :

#### 🍽️ **Générateur de Recettes**
1. **Sélectionnez vos ingrédients** dans la liste à gauche
2. **Choisissez vos options** (cuisine, difficulté, temps)
3. **Cliquez sur "GÉNÉRER AVEC llama3.2:1b"**
4. **Consultez votre recette** française personnalisée
5. **Exportez** si souhaité

#### 📊 **Calculateur de Calories**
1. **Ajoutez vos aliments** avec leurs quantités
2. **Visualisez les totaux** nutritionnels en temps réel
3. **Cliquez sur "ANALYSER AVEC IA"** pour l'analyse approfondie
4. **Consultez les conseils** santé de llama3.2:1b
5. **Exportez en CSV** si souhaité

#### 🤖 **Statut IA**
1. **Vérifiez l'état** d'Ollama et llama3.2:1b
2. **Testez la génération** IA
3. **Consultez les instructions** de dépannage

## 📁 Structure du Projet

```
assistant-culinaire-ia/
├── config.py              # Configuration de l'application
├── models.py               # Modèles de données et gestionnaire
├── ollama_service.py       # Service de communication Ollama
├── recipe_service.py       # Service de génération de recettes
├── calorie_service.py      # Service de calcul de calories
├── main.py                 # Application principale
├── README.md               # Documentation
├── LICENSE                 # Licence MIT
├── requirements.txt        # Dépendances Python
├── .gitignore             # Fichiers à ignorer
└── data/                  # Données (créé automatiquement)
    └── calories.csv       # Base nutritionnelle
```

## ⚙️ Configuration

### Paramètres par défaut

```python
# Dans config.py
OLLAMA_MODEL = "llama3.2:1b"    # Modèle IA utilisé
OLLAMA_BASE_URL = "http://localhost:11434"  # URL Ollama
APP_GEOMETRY = "1600x1000"      # Taille de fenêtre
```

### Base de données nutritionnelle

L'application inclut une base de données de 25+ aliments avec :
- Calories par 100g
- Protéines, glucides, lipides
- Fibres et catégories
- Extensible via CSV

## 🛠️ Dépannage

### Problèmes courants

#### ❌ "Ollama n'est pas disponible"
```bash
# Solution 1: Démarrer Ollama
ollama serve

# Solution 2: Vérifier le port
curl http://localhost:11434/api/tags

# Solution 3: Redémarrer proprement
pkill ollama  # Linux/Mac
taskkill /F /IM ollama.exe  # Windows
ollama serve
```

#### ❌ "llama3.2:1b n'est pas disponible"
```bash
# Installer le modèle
ollama pull llama3.2:1b

# Vérifier l'installation
ollama list
```

#### ❌ "Module 'requests' not found"
```bash
# Installer les dépendances
pip install requests pandas
```

#### ❌ Erreurs de timeout
```bash
# Redémarrer Ollama et l'application
ollama serve
python main.py
```

### Mode diagnostic

```bash
# Test complet de l'installation
python main.py --help

# Test manuel du modèle
ollama run llama3.2:1b "test"
```

## 🔧 Développement

### Prérequis développement

```bash
pip install requests pandas tkinter
```

### Architecture

L'application suit une architecture modulaire :

- **`config.py`** : Configuration centralisée
- **`models.py`** : Modèles de données (Ingredient, Recipe, etc.)
- **`ollama_service.py`** : Abstraction de l'API Ollama
- **`recipe_service.py`** : Logique de génération de recettes
- **`calorie_service.py`** : Logique de calcul nutritionnel
- **`main.py`** : Interface graphique et orchestration

### Ajout d'aliments

Pour ajouter des aliments à la base de données :

1. Modifiez `_create_sample_data()` dans `models.py`
2. Ou créez un fichier `data/calories.csv` avec les colonnes :
   ```
   name,calories,protein,carbs,fat,fiber,category
   ```

### Personnalisation des prompts

Modifiez les prompts IA dans `config.py` :

```python
PROMPTS = {
    'recipe_system': "Tu es un chef cuisinier...",
    'recipe_prompt': "Crée une recette avec...",
    # ...
}
```

## 📈 Performances

### Ressources système

- **RAM** : ~200MB en fonctionnement
- **Espace disque** : ~1.5GB (modèle llama3.2:1b)
- **CPU** : Modéré pendant la génération IA
- **Réseau** : Uniquement pour télécharger le modèle

### Temps de réponse

- **Génération de recette** : 5-15 secondes
- **Analyse nutritionnelle** : 3-10 secondes
- **Calculs de base** : Instantané

## 🤝 Contribution

Les contributions sont les bienvenues ! 

### Comment contribuer

1. **Fork** le projet
2. **Créez** une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. **Commitez** vos changements (`git commit -m 'Ajouter nouvelle fonctionnalité'`)
4. **Pushez** vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. **Ouvrez** une Pull Request

### Idées de contributions

- 🌍 Support d'autres langues
- 🥘 Nouvelles cuisines et styles
- 📊 Graphiques nutritionnels
- 🔄 Autres modèles IA (Mistral, etc.)
- 📱 Interface mobile
- 🗄️ Base de données étendue

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👥 Auteurs

- **Votre Nom** - *Développement initial* - [VotreGitHub](https://github.com/votre-username)

## 🙏 Remerciements

- **Ollama** pour l'infrastructure IA locale
- **Meta** pour le modèle Llama 3.2
- **Communauté Python** pour les outils et bibliothèques
- **Contributors** pour les améliorations et suggestions

## 📞 Support

- **Issues GitHub** : [Signaler un problème][(https://github.com/nourhene196/ollama2025))
- **Documentation** : Ce README et commentaires dans le code
- **Ollama Support** : [ollama.ai](https://ollama.ai/)

## 🔗 Liens Utiles

- [Documentation Ollama](https://github.com/ollama/ollama)
- [Modèle Llama 3.2](https://ollama.ai/library/llama3.2)
- [Python Tkinter](https://docs.python.org/3/library/tkinter.html)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

---

⭐ **N'oubliez pas de donner une étoile au projet si vous l'appréciez !** ⭐
