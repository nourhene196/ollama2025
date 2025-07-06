#!/usr/bin/env python3
"""
Version simplifiée avec onglets forcés
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import DataManager
from ollama_client import OllamaClient
from recipe_service import RecipeService

class SimpleApp:
    """Application simplifiée avec onglets visibles"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Assistant Culinaire & Calories")
        self.root.geometry("1400x900")
        
        # Forcer l'affichage au premier plan
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)
        
        self.create_interface()
        self.init_services()
    
    def create_interface(self):
        """Crée l'interface avec onglets forcés"""
        
        # Titre principal
        title_frame = tk.Frame(self.root, bg='lightblue', height=60)
        title_frame.pack(fill='x', side='top')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🍽️ Assistant Culinaire & Calories", 
                              font=('Arial', 16, 'bold'), bg='lightblue')
        title_label.pack(pady=15)
        
        # Notebook avec style forcé
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[20, 10])
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Onglet 1 : Générateur de recettes
        self.recipe_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.recipe_frame, text="🍳 Générateur de Recettes")
        self.create_recipe_interface()
        
        # Onglet 2 : Calculateur de calories  
        self.calorie_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.calorie_frame, text="📊 Calculateur de Calories")
        self.create_calorie_interface()
        
        # Onglet 3 : Test Ollama
        self.test_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.test_frame, text="🤖 Test IA")
        self.create_test_interface()
        
        # Forcer la sélection du premier onglet
        self.notebook.select(0)
    
    def create_recipe_interface(self):
        """Interface du générateur de recettes"""
        
        # Configuration en 2 colonnes
        self.recipe_frame.grid_columnconfigure(0, weight=1)
        self.recipe_frame.grid_columnconfigure(1, weight=2)
        
        # Panneau gauche : Sélection d'ingrédients
        left_panel = tk.LabelFrame(self.recipe_frame, text="Sélection d'ingrédients", 
                                  bg='white', font=('Arial', 12, 'bold'))
        left_panel.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        # Liste des ingrédients
        ingredients_label = tk.Label(left_panel, text="Cliquez sur les ingrédients :", 
                                   bg='white', font=('Arial', 10))
        ingredients_label.pack(pady=5)
        
        # Frame pour les ingrédients
        self.ingredients_frame = tk.Frame(left_panel, bg='white')
        self.ingredients_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Liste des ingrédients sélectionnés
        self.selected_label = tk.Label(left_panel, text="Ingrédients sélectionnés :", 
                                     bg='white', font=('Arial', 10, 'bold'))
        self.selected_label.pack(pady=(20, 5))
        
        self.selected_text = tk.Text(left_panel, height=4, width=30)
        self.selected_text.pack(pady=5, padx=10, fill='x')
        
        # Bouton de génération - FORCER L'AFFICHAGE
        button_frame = tk.Frame(left_panel, bg='white', height=60)
        button_frame.pack(fill='x', pady=10)
        button_frame.pack_propagate(False)  # Empêcher le rétrécissement
        
        self.generate_btn = tk.Button(button_frame, text="🍳 GÉNÉRER LA RECETTE", 
                                    bg='orange', fg='white', font=('Arial', 12, 'bold'),
                                    command=self.generate_recipe, height=2, width=20)
        self.generate_btn.pack(pady=10)
        
        # Panneau droit : Recette générée
        right_panel = tk.LabelFrame(self.recipe_frame, text="Recette générée", 
                                   bg='white', font=('Arial', 12, 'bold'))
        right_panel.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)
        
        # Instructions et bouton de génération supplémentaire
        instructions_frame = tk.Frame(right_panel, bg='white', height=80)
        instructions_frame.pack(fill='x', pady=5)
        instructions_frame.pack_propagate(False)
        
        instruction_label = tk.Label(instructions_frame, 
                                   text="Sélectionnez des ingrédients à gauche, puis générez votre recette !", 
                                   bg='white', font=('Arial', 11), wraplength=400)
        instruction_label.pack(pady=5)
        
        # Bouton de génération dans le panneau droit aussi
        self.generate_btn2 = tk.Button(instructions_frame, text="🍳 GÉNÉRER RECETTE", 
                                     bg='green', fg='white', font=('Arial', 11, 'bold'),
                                     command=self.generate_recipe, width=25)
        self.generate_btn2.pack(pady=5)
        
        # Zone de texte pour la recette
        self.recipe_text = tk.Text(right_panel, wrap=tk.WORD, font=('Arial', 11))
        self.recipe_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Texte initial
        initial_text = """Bienvenue dans le Générateur de Recettes ! 🍽️

ÉTAPES :
1️⃣ Cliquez sur les ingrédients à gauche (ils deviennent verts)
2️⃣ Cliquez sur "GÉNÉRER RECETTE" 
3️⃣ TinyLlama va créer votre recette personnalisée !

Ingrédients disponibles :
🍅 Légumes : Tomate, Oignon, Carotte, Pomme de terre, Épinard...
🥩 Viandes : Poulet, Bœuf, Saumon...
🥚 Autres : Œuf, Fromage, Lait...
🍚 Féculents : Riz, Pâtes, Pain...

Sélectionnez au moins 2-3 ingrédients pour une meilleure recette !"""
        
        self.recipe_text.insert(tk.END, initial_text)
        
        # Variables
        self.selected_ingredients = []
        
        # Charger les ingrédients
        self.load_ingredients()
        
        # Initialiser l'affichage
        self.update_selected_display()
    
    def create_calorie_interface(self):
        """Interface du calculateur de calories"""
        label = tk.Label(self.calorie_frame, text="Calculateur de calories\n(Utilisez l'autre onglet)", 
                        font=('Arial', 16), bg='white')
        label.pack(expand=True)
        
        note = tk.Label(self.calorie_frame, 
                       text="Pour le calculateur complet, fermez cette fenêtre et relancez :\npython main.py", 
                       font=('Arial', 12), bg='white', fg='gray')
        note.pack(pady=20)
    
    def create_test_interface(self):
        """Interface de test de l'IA"""
        test_label = tk.Label(self.test_frame, text="Test de TinyLlama", 
                            font=('Arial', 16, 'bold'), bg='white')
        test_label.pack(pady=20)
        
        test_btn = tk.Button(self.test_frame, text="🤖 Tester TinyLlama", 
                           bg='blue', fg='white', font=('Arial', 12),
                           command=self.test_ollama)
        test_btn.pack(pady=10)
        
        self.test_result = tk.Text(self.test_frame, height=20, width=80)
        self.test_result.pack(pady=20, padx=20, fill='both', expand=True)
    
    def load_ingredients(self):
        """Charge les ingrédients comme boutons"""
        ingredients_list = [
            "🍅 Tomate", "🧅 Oignon", "🥕 Carotte", "🥔 Pomme de terre",
            "🐔 Poulet", "🥩 Bœuf", "🐟 Saumon", "🥚 Œuf",
            "🍚 Riz", "🍝 Pâtes", "🥖 Pain", "🧀 Fromage",
            "🥛 Lait", "🧈 Beurre", "🫒 Huile d'olive", "🍌 Banane",
            "🍎 Pomme", "🍄 Champignon", "🥬 Épinard", "🧄 Ail"
        ]
        
        # Variables pour suivre l'état des boutons
        self.ingredient_buttons = {}
        
        # Créer des boutons pour chaque ingrédient
        row, col = 0, 0
        for ingredient in ingredients_list:
            btn = tk.Button(self.ingredients_frame, text=ingredient,
                          command=lambda ing=ingredient: self.toggle_ingredient(ing),
                          width=15, height=2, relief='raised', bd=2,
                          bg='lightgray', activebackground='lightblue')
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
            
            # Stocker la référence du bouton
            self.ingredient_buttons[ingredient] = btn
            
            col += 1
            if col >= 2:  # 2 colonnes
                col = 0
                row += 1
    
    def toggle_ingredient(self, ingredient):
        """Ajoute/retire un ingrédient avec feedback visuel"""
        clean_name = ingredient.split(' ', 1)[1]  # Enlever l'emoji
        btn = self.ingredient_buttons[ingredient]
        
        if clean_name in self.selected_ingredients:
            # Retirer l'ingrédient
            self.selected_ingredients.remove(clean_name)
            btn.config(bg='lightgray', relief='raised')
            print(f"❌ Retiré: {clean_name}")
        else:
            # Ajouter l'ingrédient
            self.selected_ingredients.append(clean_name)
            btn.config(bg='lightgreen', relief='sunken')
            print(f"✅ Ajouté: {clean_name}")
        
        # Mettre à jour l'affichage
        self.update_selected_display()
    
    def update_selected_display(self):
        """Met à jour l'affichage des ingrédients sélectionnés"""
        self.selected_text.delete(1.0, tk.END)
        
        if self.selected_ingredients:
            display_text = "Ingrédients choisis:\n\n"
            for i, ingredient in enumerate(self.selected_ingredients, 1):
                display_text += f"{i}. {ingredient}\n"
            display_text += f"\nTotal: {len(self.selected_ingredients)} ingrédient(s)"
        else:
            display_text = "Aucun ingrédient sélectionné.\n\nCliquez sur les boutons ci-dessus pour choisir vos ingrédients."
        
        self.selected_text.insert(tk.END, display_text)
        
        # Activer/désactiver les boutons de génération
        if self.selected_ingredients:
            self.generate_btn.config(state='normal', bg='orange')
            self.generate_btn2.config(state='normal', bg='green')
        else:
            self.generate_btn.config(state='disabled', bg='gray')
            self.generate_btn2.config(state='disabled', bg='gray')
    
    def init_services(self):
        """Initialise les services"""
        try:
            self.config = Config()
            self.data_manager = DataManager(self.config)
            self.ollama_client = OllamaClient(self.config)
            self.recipe_service = RecipeService(self.data_manager, self.ollama_client)
            print("✅ Services initialisés")
        except Exception as e:
            print(f"❌ Erreur services: {e}")
    
    def generate_recipe(self):
        """Génère une recette"""
        if not self.selected_ingredients:
            messagebox.showwarning("Attention", "Sélectionnez au moins un ingrédient !")
            return
        
        self.recipe_text.delete(1.0, tk.END)
        self.recipe_text.insert(tk.END, "🔄 Génération en cours avec TinyLlama...\n\n")
        self.root.update()
        
        try:
            # Générer avec le service
            recipe = self.recipe_service.generate_recipe(self.selected_ingredients)
            
            if recipe:
                # Afficher la recette
                result = f"🍽️ {recipe.title}\n"
                result += "=" * 50 + "\n\n"
                
                result += "📋 INGRÉDIENTS:\n"
                for ing in recipe.ingredients:
                    result += f"• {ing['name']}: {ing['quantity']} {ing['unit']}\n"
                
                result += f"\n⏱️ PRÉPARATION ({recipe.prep_time}):\n"
                for i, step in enumerate(recipe.steps, 1):
                    result += f"{i}. {step}\n"
                
                result += f"\n🎯 Difficulté: {recipe.difficulty}\n"
                result += f"🔥 Calories: {recipe.total_calories:.0f} kcal\n"
                
                self.recipe_text.delete(1.0, tk.END)
                self.recipe_text.insert(tk.END, result)
                
            else:
                self.recipe_text.delete(1.0, tk.END)
                self.recipe_text.insert(tk.END, "❌ Erreur lors de la génération")
                
        except Exception as e:
            self.recipe_text.delete(1.0, tk.END)
            self.recipe_text.insert(tk.END, f"❌ Erreur: {e}")
    
    def test_ollama(self):
        """Test direct de TinyLlama"""
        self.test_result.delete(1.0, tk.END)
        self.test_result.insert(tk.END, "🧪 Test de TinyLlama en cours...\n\n")
        self.root.update()
        
        try:
            if hasattr(self, 'ollama_client'):
                response = self.ollama_client.generate_text("Dis bonjour en français et explique ce que tu fais")
                self.test_result.insert(tk.END, f"✅ Réponse de TinyLlama:\n{response}\n\n")
            else:
                self.test_result.insert(tk.END, "❌ Client Ollama non initialisé\n")
        except Exception as e:
            self.test_result.insert(tk.END, f"❌ Erreur: {e}\n")
    
    def run(self):
        """Lance l'application"""
        self.root.mainloop()

if __name__ == "__main__":
    print("🚀 Lancement de la version simplifiée avec onglets forcés...")
    app = SimpleApp()
    app.run()