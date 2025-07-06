import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    """Gestionnaire de la base de données SQLite"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données avec toutes les tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des recettes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ingredients TEXT NOT NULL,
                instructions TEXT NOT NULL,
                cuisine_type TEXT,
                dietary_restrictions TEXT,
                prep_time INTEGER,
                portions INTEGER,
                calories_per_portion INTEGER,
                total_calories INTEGER,
                nutritional_info TEXT,
                difficulty_level TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_favorite BOOLEAN DEFAULT 0,
                rating INTEGER DEFAULT 0
            )
        ''')
        
        # Table du planificateur de repas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meal_planner (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                meal_type TEXT NOT NULL,
                recipe_id INTEGER,
                portions INTEGER DEFAULT 1,
                notes TEXT,
                completed BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id)
            )
        ''')
        
        # Table des ingrédients favoris
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorite_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_name TEXT UNIQUE NOT NULL,
                category TEXT,
                usage_count INTEGER DEFAULT 1,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des préférences utilisateur
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_key TEXT UNIQUE NOT NULL,
                preference_value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table de l'historique des générations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredients_input TEXT NOT NULL,
                cuisine_type TEXT,
                restrictions TEXT,
                generated_recipe_id INTEGER,
                generation_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_rating INTEGER,
                FOREIGN KEY (generated_recipe_id) REFERENCES recipes (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_recipe(self, recipe_data: Dict) -> int:
        """Sauvegarde une recette et retourne son ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO recipes (
                name, ingredients, instructions, cuisine_type, 
                dietary_restrictions, prep_time, portions, 
                calories_per_portion, total_calories, nutritional_info,
                difficulty_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            recipe_data.get('name', ''),
            json.dumps(recipe_data.get('ingredients', [])),
            recipe_data.get('instructions', ''),
            recipe_data.get('cuisine_type', ''),
            json.dumps(recipe_data.get('dietary_restrictions', [])),
            recipe_data.get('prep_time', 0),
            recipe_data.get('portions', 2),
            recipe_data.get('calories_per_portion', 0),
            recipe_data.get('total_calories', 0),
            json.dumps(recipe_data.get('nutritional_info', {})),
            recipe_data.get('difficulty_level', 'Facile')
        ))
        
        recipe_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return recipe_id
    
    def get_recipes(self, limit: int = 50, cuisine_type: str = None, 
                   dietary_restrictions: List[str] = None) -> List[Dict]:
        """Récupère les recettes avec filtres optionnels"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM recipes WHERE 1=1"
        params = []
        
        if cuisine_type and cuisine_type != 'Tous':
            query += " AND cuisine_type = ?"
            params.append(cuisine_type)
        
        if dietary_restrictions:
            for restriction in dietary_restrictions:
                query += " AND dietary_restrictions LIKE ?"
                params.append(f'%{restriction}%')
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        recipes = cursor.fetchall()
        conn.close()
        
        return [self._row_to_recipe_dict(row) for row in recipes]
    
    def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict]:
        """Récupère une recette par son ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        row = cursor.fetchone()
        conn.close()
        
        return self._row_to_recipe_dict(row) if row else None
    
    def update_recipe_rating(self, recipe_id: int, rating: int):
        """Met à jour la note d'une recette"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE recipes 
            SET rating = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (rating, recipe_id))
        
        conn.commit()
        conn.close()
    
    def toggle_favorite(self, recipe_id: int) -> bool:
        """Bascule le statut favori d'une recette"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Récupérer le statut actuel
        cursor.execute("SELECT is_favorite FROM recipes WHERE id = ?", (recipe_id,))
        current_status = cursor.fetchone()[0]
        
        # Inverser le statut
        new_status = not current_status
        cursor.execute('''
            UPDATE recipes 
            SET is_favorite = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (new_status, recipe_id))
        
        conn.commit()
        conn.close()
        
        return new_status
    
    def save_meal_plan(self, date: str, meal_type: str, recipe_id: int, 
                      portions: int = 1, notes: str = ""):
        """Sauvegarde un élément du planificateur de repas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Supprimer l'ancien planning pour cette date/repas
        cursor.execute('''
            DELETE FROM meal_planner 
            WHERE date = ? AND meal_type = ?
        ''', (date, meal_type))
        
        # Ajouter le nouveau planning
        cursor.execute('''
            INSERT INTO meal_planner (date, meal_type, recipe_id, portions, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, meal_type, recipe_id, portions, notes))
        
        conn.commit()
        conn.close()
    
    def get_meal_plan(self, start_date: str, end_date: str) -> List[Dict]:
        """Récupère le planning des repas pour une période"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT mp.*, r.name as recipe_name, r.calories_per_portion
            FROM meal_planner mp
            LEFT JOIN recipes r ON mp.recipe_id = r.id
            WHERE mp.date BETWEEN ? AND ?
            ORDER BY mp.date, mp.meal_type
        ''', (start_date, end_date))
        
        meals = cursor.fetchall()
        conn.close()
        
        return [self._row_to_meal_dict(row) for row in meals]
    
    def get_shopping_list(self, start_date: str, end_date: str) -> Dict[str, float]:
        """Génère une liste de courses basée sur le planning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.ingredients, mp.portions
            FROM meal_planner mp
            JOIN recipes r ON mp.recipe_id = r.id
            WHERE mp.date BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        results = cursor.fetchall()
        conn.close()
        
        shopping_list = {}
        
        for ingredients_json, portions in results:
            ingredients = json.loads(ingredients_json)
            for ingredient in ingredients:
                name = ingredient['name']
                quantity = ingredient['quantity'] * portions
                unit = ingredient.get('unit', '')
                
                key = f"{name} ({unit})" if unit else name
                shopping_list[key] = shopping_list.get(key, 0) + quantity
        
        return shopping_list
    
    def add_favorite_ingredient(self, ingredient_name: str, category: str = ""):
        """Ajoute ou met à jour un ingrédient favori"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO favorite_ingredients (
                ingredient_name, category, usage_count, last_used
            ) VALUES (
                ?, ?, 
                COALESCE((SELECT usage_count FROM favorite_ingredients WHERE ingredient_name = ?) + 1, 1),
                CURRENT_TIMESTAMP
            )
        ''', (ingredient_name, category, ingredient_name))
        
        conn.commit()
        conn.close()
    
    def get_favorite_ingredients(self, limit: int = 20) -> List[str]:
        """Récupère les ingrédients favoris les plus utilisés"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ingredient_name 
            FROM favorite_ingredients 
            ORDER BY usage_count DESC, last_used DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in results]
    
    def save_generation_history(self, ingredients_input: str, cuisine_type: str,
                               restrictions: str, recipe_id: int):
        """Sauvegarde l'historique des générations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO generation_history (
                ingredients_input, cuisine_type, restrictions, generated_recipe_id
            ) VALUES (?, ?, ?, ?)
        ''', (ingredients_input, cuisine_type, restrictions, recipe_id))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> Dict:
        """Récupère les statistiques d'utilisation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Nombre total de recettes
        cursor.execute("SELECT COUNT(*) FROM recipes")
        stats['total_recipes'] = cursor.fetchone()[0]
        
        # Nombre de recettes favorites
        cursor.execute("SELECT COUNT(*) FROM recipes WHERE is_favorite = 1")
        stats['favorite_recipes'] = cursor.fetchone()[0]
        
        # Cuisine la plus populaire
        cursor.execute('''
            SELECT cuisine_type, COUNT(*) as count 
            FROM recipes 
            WHERE cuisine_type IS NOT NULL 
            GROUP BY cuisine_type 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        stats['most_popular_cuisine'] = result[0] if result else "Aucune"
        
        # Moyenne des calories par recette
        cursor.execute("SELECT AVG(calories_per_portion) FROM recipes WHERE calories_per_portion > 0")
        avg_calories = cursor.fetchone()[0]
        stats['avg_calories'] = round(avg_calories, 0) if avg_calories else 0
        
        # Nombre de planifications cette semaine
        cursor.execute('''
            SELECT COUNT(*) FROM meal_planner 
            WHERE date >= date('now', '-7 days')
        ''')
        stats['weekly_plans'] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats
    
    def _row_to_recipe_dict(self, row) -> Dict:
        """Convertit une ligne de la table recipes en dictionnaire"""
        if not row:
            return {}
        
        return {
            'id': row[0],
            'name': row[1],
            'ingredients': json.loads(row[2]) if row[2] else [],
            'instructions': row[3],
            'cuisine_type': row[4],
            'dietary_restrictions': json.loads(row[5]) if row[5] else [],
            'prep_time': row[6],
            'portions': row[7],
            'calories_per_portion': row[8],
            'total_calories': row[9],
            'nutritional_info': json.loads(row[10]) if row[10] else {},
            'difficulty_level': row[11],
            'created_at': row[12],
            'updated_at': row[13],
            'is_favorite': bool(row[14]),
            'rating': row[15]
        }
    
    def _row_to_meal_dict(self, row) -> Dict:
        """Convertit une ligne de la table meal_planner en dictionnaire"""
        return {
            'id': row[0],
            'date': row[1],
            'meal_type': row[2],
            'recipe_id': row[3],
            'portions': row[4],
            'notes': row[5],
            'completed': bool(row[6]),
            'created_at': row[7],
            'recipe_name': row[8],
            'calories_per_portion': row[9]
        }