#!/usr/bin/env python3
"""
Assistant Culinaire & Calories IA - Version 3.0
Application structurée avec onglets séparés et llama3.2:1b obligatoire

Version: 3.0.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import csv
from datetime import datetime
from typing import List, Dict, Any

# Imports locaux
from config import Config
from models import DataManager, Recipe, CalorieCalculation
from ollama_service import OllamaService
from recipe_service import RecipeService
from calorie_service import CalorieService

class LoadingDialog:
    """Dialogue de chargement pour les opérations IA"""
    def __init__(self, parent, message):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("⏳ llama3.2:1b en action")
        self.dialog.geometry("450x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrer
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 225
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 75
        self.dialog.geometry(f"450x150+{x}+{y}")
        
        # Interface
        tk.Label(self.dialog, text="🤖 llama3.2:1b travaille...", 
                font=('Segoe UI', 14, 'bold')).pack(pady=15)
        tk.Label(self.dialog, text=message, 
                font=('Segoe UI', 11)).pack(pady=5)
        
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate')
        self.progress.pack(pady=15, padx=30, fill='x')
        self.progress.start()
    
    def destroy(self):
        self.progress.stop()
        self.dialog.destroy()

class RecipeTab:
    """Onglet Générateur de Recettes"""
    
    def __init__(self, parent, config, recipe_service, data_manager):
        self.parent = parent
        self.config = config
        self.recipe_service = recipe_service
        self.data_manager = data_manager
        
        self.selected_ingredients = []
        self.current_recipe = None
        
        self.create_interface()
        self.load_ingredients()
    
    def create_interface(self):
        """Crée l'interface de l'onglet recettes"""
        # Configuration en colonnes
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=2)
        self.parent.grid_rowconfigure(0, weight=1)
        
        # Panneau gauche: Sélection d'ingrédients
        left_frame = tk.LabelFrame(self.parent, text="🛒 Sélection d'ingrédients",
                                  font=('Segoe UI', 12, 'bold'))
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)
        
        self.create_ingredients_panel(left_frame)
        
        # Panneau droit: Génération et affichage
        right_frame = tk.LabelFrame(self.parent, text="🍽️ Recette générée par llama3.2:1b",
                                   font=('Segoe UI', 12, 'bold'))
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)
        
        self.create_recipe_panel(right_frame)
    
    def create_ingredients_panel(self, parent):
        """Panneau de sélection d'ingrédients"""
        # Recherche
        search_frame = tk.Frame(parent)
        search_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(search_frame, text="🔍 Rechercher:", font=('Segoe UI', 10)).pack(anchor='w')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_changed)
        tk.Entry(search_frame, textvariable=self.search_var).pack(fill='x', pady=5)
        
        # Catégories
        category_frame = tk.Frame(parent)
        category_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(category_frame, text="📂 Catégorie:", font=('Segoe UI', 10)).pack(anchor='w')
        self.category_var = tk.StringVar(value="Toutes")
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, state='readonly')
        self.category_combo.pack(fill='x', pady=5)
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_changed)
        
        # Zone d'ingrédients avec scrollbar
        ingredients_container = tk.Frame(parent)
        ingredients_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(ingredients_container)
        scrollbar = ttk.Scrollbar(ingredients_container, orient="vertical", command=canvas.yview)
        self.ingredients_scroll_frame = tk.Frame(canvas)
        
        self.ingredients_scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.ingredients_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.ingredient_buttons = {}
        
        # Ingrédients sélectionnés
        selected_frame = tk.LabelFrame(parent, text="✅ Sélectionnés")
        selected_frame.pack(fill='x', padx=10, pady=10)
        
        self.selected_listbox = tk.Listbox(selected_frame, height=6)
        self.selected_listbox.pack(fill='x', padx=5, pady=5)
        
        # Boutons
        buttons_frame = tk.Frame(selected_frame)
        buttons_frame.pack(fill='x', pady=5)
        
        tk.Button(buttons_frame, text="🗑️ Vider", command=self.clear_selection,
                 bg='#6c757d', fg='white').pack(side='left', padx=5)
    
    def create_recipe_panel(self, parent):
        """Panneau de génération et affichage de recettes"""
        # Options de génération
        options_frame = tk.LabelFrame(parent, text="🎛️ Options de génération")
        options_frame.pack(fill='x', padx=10, pady=10)
        
        # Grille pour les options
        tk.Label(options_frame, text="🌍 Cuisine:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.cuisine_var = tk.StringVar()
        cuisine_combo = ttk.Combobox(options_frame, textvariable=self.cuisine_var,
                                   values=["", "🇫🇷 Française", "🇮🇹 Italienne", "🇨🇳 Asiatique", 
                                          "🇬🇷 Méditerranéenne", "🇲🇽 Mexicaine"])
        cuisine_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        
        tk.Label(options_frame, text="⭐ Difficulté:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.difficulty_var = tk.StringVar()
        difficulty_combo = ttk.Combobox(options_frame, textvariable=self.difficulty_var,
                                      values=["", "🟢 Facile", "🟡 Moyen", "🔴 Difficile"])
        difficulty_combo.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        tk.Label(options_frame, text="⏰ Temps:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.time_var = tk.StringVar()
        time_combo = ttk.Combobox(options_frame, textvariable=self.time_var,
                                values=["", "⚡ 15 min", "🕐 30 min", "🕑 1 heure"])
        time_combo.grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        
        options_frame.grid_columnconfigure(1, weight=1)
        
        # Bouton de génération
        self.generate_btn = tk.Button(options_frame, text="🤖 GÉNÉRER AVEC llama3.2:1b",
                                    command=self.generate_recipe,
                                    bg='#FF6B35', fg='white', 
                                    font=('Segoe UI', 12, 'bold'),
                                    height=2, cursor='hand2')
        self.generate_btn.grid(row=3, column=0, columnspan=2, pady=15, sticky='ew')
        
        # Zone d'affichage de la recette
        self.recipe_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, height=25)
        self.recipe_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tags pour le formatage
        self.recipe_text.tag_configure('title', font=('Segoe UI', 16, 'bold'), foreground='#FF6B35')
        self.recipe_text.tag_configure('heading', font=('Segoe UI', 12, 'bold'), foreground='#004E98')
        
        # Boutons d'action
        action_frame = tk.Frame(parent)
        action_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(action_frame, text="📄 Exporter", command=self.export_recipe,
                 bg='#004E98', fg='white').pack(side='left', padx=5)
        
        tk.Button(action_frame, text="🔄 Nouveau", command=self.clear_all,
                 bg='#6c757d', fg='white').pack(side='right', padx=5)
        
        # Message initial
        self.show_welcome_message()
    
    def load_ingredients(self):
        """Charge les ingrédients"""
        if not self.data_manager:
            return
        
        ingredients = self.data_manager.get_all_ingredients()
        
        # Catégories
        categories = sorted(set(ing.category for ing in ingredients))
        self.category_combo['values'] = ["Toutes"] + categories
        
        # Afficher les ingrédients
        self.display_ingredients(ingredients)
    
    def display_ingredients(self, ingredients):
        """Affiche les ingrédients comme boutons"""
        # Vider le frame
        for widget in self.ingredients_scroll_frame.winfo_children():
            widget.destroy()
        
        self.ingredient_buttons.clear()
        
        # Créer les boutons
        row, col = 0, 0
        for ingredient in sorted(ingredients, key=lambda x: x.name):
            # Emoji selon catégorie
            emoji_map = {
                "Légume": "🥬", "Viande": "🥩", "Poisson": "🐟",
                "Produit laitier": "🥛", "Fruit": "🍎", "Céréale": "🌾",
                "Matière grasse": "🧈", "Aromate": "🌿"
            }
            emoji = emoji_map.get(ingredient.category, "🍽️")
            
            btn_text = f"{emoji} {ingredient.name.title()}"
            
            btn = tk.Button(self.ingredients_scroll_frame, text=btn_text,
                          command=lambda ing=ingredient.name: self.toggle_ingredient(ing),
                          width=18, height=2, bg='lightgray', relief='raised', bd=2)
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
            
            self.ingredient_buttons[ingredient.name] = btn
            
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        # Configurer les colonnes
        self.ingredients_scroll_frame.grid_columnconfigure(0, weight=1)
        self.ingredients_scroll_frame.grid_columnconfigure(1, weight=1)
    
    def on_search_changed(self, *args):
        """Filtrage par recherche"""
        self.filter_ingredients()
    
    def on_category_changed(self, event=None):
        """Filtrage par catégorie"""
        self.filter_ingredients()
    
    def filter_ingredients(self):
        """Applique les filtres"""
        if not self.data_manager:
            return
        
        search_term = self.search_var.get().lower()
        selected_category = self.category_var.get()
        
        all_ingredients = self.data_manager.get_all_ingredients()
        filtered = []
        
        for ingredient in all_ingredients:
            if search_term and search_term not in ingredient.name.lower():
                continue
            if selected_category != "Toutes" and ingredient.category != selected_category:
                continue
            filtered.append(ingredient)
        
        self.display_ingredients(filtered)
    
    def toggle_ingredient(self, ingredient_name):
        """Ajoute/retire un ingrédient"""
        btn = self.ingredient_buttons.get(ingredient_name)
        if not btn:
            return
        
        if ingredient_name in self.selected_ingredients:
            self.selected_ingredients.remove(ingredient_name)
            btn.config(bg='lightgray', relief='raised')
        else:
            self.selected_ingredients.append(ingredient_name)
            btn.config(bg='lightgreen', relief='sunken')
        
        self.update_selected_display()
    
    def update_selected_display(self):
        """Met à jour l'affichage des sélectionnés"""
        self.selected_listbox.delete(0, tk.END)
        
        for ingredient in self.selected_ingredients:
            self.selected_listbox.insert(tk.END, f"✅ {ingredient.title()}")
        
        # Activer/désactiver le bouton
        if self.selected_ingredients:
            self.generate_btn.config(state='normal', bg='#FF6B35')
        else:
            self.generate_btn.config(state='disabled', bg='gray')
    
    def clear_selection(self):
        """Vide la sélection"""
        for ingredient_name in self.selected_ingredients.copy():
            btn = self.ingredient_buttons.get(ingredient_name)
            if btn:
                btn.config(bg='lightgray', relief='raised')
        
        self.selected_ingredients.clear()
        self.update_selected_display()
    
    def generate_recipe(self):
        """Génère une recette avec llama3.2:1b"""
        if not self.selected_ingredients:
            messagebox.showwarning("Attention", "🚨 Sélectionnez au moins un ingrédient !")
            return
        
        loading = LoadingDialog(self.parent, "Génération de la recette française...")
        
        def generate_thread():
            try:
                recipe = self.recipe_service.generate_recipe(
                    self.selected_ingredients,
                    self.cuisine_var.get(),
                    self.difficulty_var.get(),
                    self.time_var.get()
                )
                
                self.parent.after(0, lambda: self.on_recipe_generated(recipe, loading))
                
            except Exception as e:
                error_msg = str(e)
                self.parent.after(0, lambda msg=error_msg, l=loading: self.on_generation_error(msg, l))
        thread = threading.Thread(target=generate_thread, daemon=True)
        thread.start()
    
    def on_recipe_generated(self, recipe, loading_dialog):
        """Affiche la recette générée"""
        loading_dialog.destroy()
        
        self.current_recipe = recipe
        self.display_recipe(recipe)
        messagebox.showinfo("Succès", "🎉 Recette générée avec succès par llama3.2:1b !")
    
    def on_generation_error(self, error, loading_dialog):
        """Gestion des erreurs"""
        loading_dialog.destroy()
        messagebox.showerror("Erreur", error)
    
    def display_recipe(self, recipe):
        """Affiche une recette"""
        self.recipe_text.delete(1.0, tk.END)
        
        # Titre
        self.recipe_text.insert(tk.END, f"🍽️ {recipe.title}\n", 'title')
        self.recipe_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # Informations
        self.recipe_text.insert(tk.END, "📋 INFORMATIONS\n", 'heading')
        self.recipe_text.insert(tk.END, f"⏰ Temps: {recipe.prep_time}\n")
        self.recipe_text.insert(tk.END, f"⭐ Difficulté: {recipe.difficulty}\n")
        if recipe.tips:
            self.recipe_text.insert(tk.END, f"💡 Conseil: {recipe.tips}\n")
        self.recipe_text.insert(tk.END, "\n")
        
        # Ingrédients
        self.recipe_text.insert(tk.END, "🛒 INGRÉDIENTS\n", 'heading')
        for ingredient in recipe.ingredients:
            self.recipe_text.insert(tk.END, f"• {ingredient['name']}: {ingredient['quantity']} {ingredient['unit']}\n")
        self.recipe_text.insert(tk.END, "\n")
        
        # Préparation
        self.recipe_text.insert(tk.END, "👨‍🍳 PRÉPARATION\n", 'heading')
        for i, step in enumerate(recipe.steps, 1):
            self.recipe_text.insert(tk.END, f"{i}. {step}\n")
    
    def show_welcome_message(self):
        """Message de bienvenue"""
        welcome = """🎉 Générateur de Recettes IA

🤖 FONCTIONNEMENT:
✅ Sélectionnez vos ingrédients à gauche
✅ Choisissez vos options (cuisine, difficulté, temps)
✅ Cliquez sur "GÉNÉRER AVEC llama3.2:1b"
✅ Obtenez une recette française personnalisée !

🔧 PRÉREQUIS:
⚠️ Ollama doit être démarré: ollama serve
⚠️ llama3.2:1b doit être installé: ollama pull llama3.2:1b

💡 ASTUCE: Plus d'ingrédients = recette plus créative !"""

        self.recipe_text.delete(1.0, tk.END)
        self.recipe_text.insert(tk.END, welcome)
    
    def export_recipe(self):
        """Exporte la recette"""
        if not self.current_recipe:
            messagebox.showwarning("Aucune recette", "Générez d'abord une recette !")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self._format_recipe_for_export())
                messagebox.showinfo("Export", f"✅ Recette exportée vers {filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"❌ Erreur d'export: {e}")
    
    def _format_recipe_for_export(self):
        """Formate la recette pour l'export"""
        recipe = self.current_recipe
        lines = [
            f"🍽️ {recipe.title}",
            "=" * 60,
            "",
            "📋 INFORMATIONS:",
            f"⏰ Temps: {recipe.prep_time}",
            f"⭐ Difficulté: {recipe.difficulty}",
            f"💡 Conseil: {recipe.tips}",
            "",
            "🛒 INGRÉDIENTS:"
        ]
        
        for ing in recipe.ingredients:
            lines.append(f"• {ing['name']}: {ing['quantity']} {ing['unit']}")
        
        lines.extend(["", "👨‍🍳 PRÉPARATION:"])
        for i, step in enumerate(recipe.steps, 1):
            lines.append(f"{i}. {step}")
        
        lines.extend([
            "",
            "=" * 60,
            f"Généré par llama3.2:1b - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ])
        
        return "\n".join(lines)
    
    def clear_all(self):
        """Remet à zéro"""
        self.clear_selection()
        self.cuisine_var.set("")
        self.difficulty_var.set("")
        self.time_var.set("")
        self.current_recipe = None
        self.show_welcome_message()

class CalorieTab:
    """Onglet Calculateur de Calories"""
    
    def __init__(self, parent, config, calorie_service, data_manager):
        self.parent = parent
        self.config = config
        self.calorie_service = calorie_service
        self.data_manager = data_manager
        
        self.foods_data = []
        self.current_calculations = []
        
        self.create_interface()
    
    def create_interface(self):
        """Crée l'interface de l'onglet calories"""
        # Configuration en colonnes
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)
        
        # Panneau gauche: Saisie
        left_frame = tk.LabelFrame(self.parent, text="🍽️ Saisie des aliments",
                                  font=('Segoe UI', 12, 'bold'))
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)
        
        self.create_input_panel(left_frame)
        
        # Panneau droit: Analyse
        right_frame = tk.LabelFrame(self.parent, text="📊 Analyse nutritionnelle IA",
                                   font=('Segoe UI', 12, 'bold'))
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)
        
        self.create_analysis_panel(right_frame)
    
    def create_input_panel(self, parent):
        """Panneau de saisie des aliments"""
        # Sélection d'aliment
        input_frame = tk.Frame(parent)
        input_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(input_frame, text="🥘 Aliment:", font=('Segoe UI', 10)).grid(row=0, column=0, sticky='w')
        
        self.food_var = tk.StringVar()
        self.food_combo = ttk.Combobox(input_frame, textvariable=self.food_var, width=25)
        self.food_combo.grid(row=0, column=1, sticky='ew', padx=5)
        
        tk.Label(input_frame, text="📏 Quantité:", font=('Segoe UI', 10)).grid(row=1, column=0, sticky='w')
        
        quantity_frame = tk.Frame(input_frame)
        quantity_frame.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        self.quantity_var = tk.StringVar(value="100")
        tk.Entry(quantity_frame, textvariable=self.quantity_var, width=10).pack(side='left')
        
        self.unit_var = tk.StringVar(value="g")
        unit_combo = ttk.Combobox(quantity_frame, textvariable=self.unit_var,
                                 values=["g", "kg", "ml", "l", "tasse", "cuillère", "portion", "unité"],
                                 width=10, state='readonly')
        unit_combo.pack(side='left', padx=5)
        
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Boutons
        btn_frame = tk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="➕ Ajouter", command=self.add_food,
                 bg='#2ECC71', fg='white', font=('Segoe UI', 10, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="🤖 ANALYSER AVEC IA", command=self.analyze_with_ai,
                 bg='#FF6B35', fg='white', font=('Segoe UI', 10, 'bold')).pack(side='left', padx=5)
        
        # Liste des aliments ajoutés
        list_frame = tk.LabelFrame(parent, text="📋 Aliments ajoutés")
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview
        columns = ('Aliment', 'Quantité', 'Unité', 'Calories')
        self.foods_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.foods_tree.heading(col, text=col)
            self.foods_tree.column(col, width=80)
        
        # Scrollbar
        tree_scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.foods_tree.yview)
        self.foods_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.foods_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        tree_scroll.pack(side='right', fill='y', pady=5)
        
        # Boutons de gestion
        manage_frame = tk.Frame(list_frame)
        manage_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Button(manage_frame, text="🗑️ Supprimer", command=self.remove_food,
                 bg='#dc3545', fg='white').pack(side='left', padx=5)
        tk.Button(manage_frame, text="🧹 Vider tout", command=self.clear_foods,
                 bg='#6c757d', fg='white').pack(side='left', padx=5)
        
        # Charger les aliments disponibles
        self.load_available_foods()
    
    def create_analysis_panel(self, parent):
        """Panneau d'analyse nutritionnelle"""
        # Résumé des totaux
        summary_frame = tk.LabelFrame(parent, text="📊 Totaux nutritionnels")
        summary_frame.pack(fill='x', padx=10, pady=10)
        
        # Variables d'affichage
        self.total_calories_var = tk.StringVar(value="0 kcal")
        self.total_proteins_var = tk.StringVar(value="0 g")
        self.total_carbs_var = tk.StringVar(value="0 g")
        self.total_fats_var = tk.StringVar(value="0 g")
        
        # Affichage en grille
        tk.Label(summary_frame, text="🔥 Calories:", font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        tk.Label(summary_frame, textvariable=self.total_calories_var, font=('Segoe UI', 14, 'bold'), fg='#FF6B35').grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        tk.Label(summary_frame, text="🥩 Protéines:", font=('Segoe UI', 10)).grid(row=1, column=0, sticky='w', padx=5, pady=2)
        tk.Label(summary_frame, textvariable=self.total_proteins_var, font=('Segoe UI', 10)).grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        tk.Label(summary_frame, text="🍞 Glucides:", font=('Segoe UI', 10)).grid(row=2, column=0, sticky='w', padx=5, pady=2)
        tk.Label(summary_frame, textvariable=self.total_carbs_var, font=('Segoe UI', 10)).grid(row=2, column=1, sticky='w', padx=5, pady=2)
        
        tk.Label(summary_frame, text="🥑 Lipides:", font=('Segoe UI', 10)).grid(row=3, column=0, sticky='w', padx=5, pady=2)
        tk.Label(summary_frame, textvariable=self.total_fats_var, font=('Segoe UI', 10)).grid(row=3, column=1, sticky='w', padx=5, pady=2)
        
        summary_frame.grid_columnconfigure(1, weight=1)
        
 # Analyse détaillée avec IA
        details_frame = tk.LabelFrame(parent, text="🤖 Analyse détaillée par llama3.2:1b")
        details_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.analysis_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, height=20)
        self.analysis_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tags pour formatage
        self.analysis_text.tag_configure('title', font=('Segoe UI', 12, 'bold'), foreground='#FF6B35')
        self.analysis_text.tag_configure('heading', font=('Segoe UI', 10, 'bold'), foreground='#004E98')
        
        # Boutons d'export
        export_frame = tk.Frame(details_frame)
        export_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Button(export_frame, text="📊 Exporter CSV", command=self.export_analysis,
                 bg='#004E98', fg='white').pack(side='left', padx=5)
        tk.Button(export_frame, text="🔄 Nouvelle analyse", command=self.clear_analysis,
                 bg='#6c757d', fg='white').pack(side='right', padx=5)
        
        # Message initial
        self.show_welcome_analysis()
    
    def load_available_foods(self):
        """Charge les aliments disponibles"""
        if self.data_manager:
            ingredients = self.data_manager.get_all_ingredients()
            food_names = sorted([ing.name for ing in ingredients])
            self.food_combo['values'] = food_names
    
    def add_food(self):
        """Ajoute un aliment à la liste"""
        food_name = self.food_var.get().strip()
        if not food_name:
            messagebox.showwarning("Aliment manquant", "Sélectionnez un aliment")
            return
        
        try:
            quantity = float(self.quantity_var.get())
            if quantity <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Quantité invalide", "Saisissez une quantité valide")
            return
        
        unit = self.unit_var.get()
        
        # Vérifier que l'aliment existe
        if self.data_manager and not self.data_manager.get_ingredient(food_name):
            messagebox.showerror("Aliment non trouvé", f"'{food_name}' n'est pas dans la base")
            return
        
        # Ajouter aux données
        food_data = {"name": food_name, "quantity": quantity, "unit": unit}
        self.foods_data.append(food_data)
        
        # Ajouter à l'affichage
        self.foods_tree.insert('', 'end', values=(food_name, quantity, unit, "..."))
        
        # Vider les champs
        self.food_var.set("")
        self.quantity_var.set("100")
        
        # Calculer les totaux de base
        self.calculate_basic_totals()
    
    def remove_food(self):
        """Supprime l'aliment sélectionné"""
        selected = self.foods_tree.selection()
        if selected:
            for item in selected:
                # Récupérer l'index
                index = self.foods_tree.index(item)
                # Supprimer des données
                if 0 <= index < len(self.foods_data):
                    del self.foods_data[index]
                # Supprimer de l'affichage
                self.foods_tree.delete(item)
            
            self.calculate_basic_totals()
    
    def clear_foods(self):
        """Vide la liste des aliments"""
        self.foods_data.clear()
        for item in self.foods_tree.get_children():
            self.foods_tree.delete(item)
        self.clear_analysis()
    
    def calculate_basic_totals(self):
        """Calcule les totaux de base"""
        if not self.foods_data:
            self.total_calories_var.set("0 kcal")
            self.total_proteins_var.set("0 g")
            self.total_carbs_var.set("0 g")
            self.total_fats_var.set("0 g")
            return
        
        try:
            calculations = self.calorie_service.calculate_meal_calories(self.foods_data)
            self.current_calculations = calculations
            
            # Calculer les totaux
            total_calories = sum(calc.total_calories for calc in calculations)
            total_proteins = sum(calc.proteins for calc in calculations)
            total_carbs = sum(calc.carbs for calc in calculations)
            total_fats = sum(calc.fats for calc in calculations)
            
            # Mettre à jour l'affichage
            self.total_calories_var.set(f"{total_calories:.0f} kcal")
            self.total_proteins_var.set(f"{total_proteins:.1f} g")
            self.total_carbs_var.set(f"{total_carbs:.1f} g")
            self.total_fats_var.set(f"{total_fats:.1f} g")
            
            # Mettre à jour les calories dans la liste
            for i, item in enumerate(self.foods_tree.get_children()):
                if i < len(calculations):
                    calc = calculations[i]
                    values = list(self.foods_tree.item(item)['values'])
                    values[3] = f"{calc.total_calories:.0f}"
                    self.foods_tree.item(item, values=values)
        
        except Exception as e:
            print(f"Erreur calcul: {e}")
    
    def analyze_with_ai(self):
        """Lance l'analyse complète avec llama3.2:1b"""
        if not self.foods_data:
            messagebox.showwarning("Aucun aliment", "Ajoutez au moins un aliment à analyser")
            return
        
        loading = LoadingDialog(self.parent, "Analyse nutritionnelle approfondie en cours...")
        
        def analyze_thread():
            try:
                # Créer une recette temporaire pour l'analyse IA
                from models import Recipe
                
                temp_recipe = Recipe(
                    title="Analyse nutritionnelle",
                    ingredients=[{"name": food["name"], "quantity": food["quantity"], "unit": food["unit"]} 
                               for food in self.foods_data],
                    steps=["Analyse des aliments"],
                    prep_time="",
                    difficulty=""
                )
                
                # Analyser avec IA
                analysis = self.calorie_service.analyze_nutrition_with_ai(temp_recipe)
                
                self.parent.after(0, lambda: self.on_analysis_completed(analysis, loading))
                
            except Exception as e:
                self.parent.after(0, lambda: self.on_analysis_error(str(e), loading))
        
        thread = threading.Thread(target=analyze_thread, daemon=True)
        thread.start()
    
    def on_analysis_completed(self, analysis, loading_dialog):
        """Affiche l'analyse terminée"""
        loading_dialog.destroy()
        
        if analysis:
            self.display_ai_analysis(analysis)
            messagebox.showinfo("Succès", "🎉 Analyse nutritionnelle terminée avec llama3.2:1b !")
        else:
            messagebox.showerror("Erreur", "❌ Impossible de réaliser l'analyse IA")
    
    def on_analysis_error(self, error, loading_dialog):
        """Gestion des erreurs d'analyse"""
        loading_dialog.destroy()
        messagebox.showerror("Erreur", error)
    
    def display_ai_analysis(self, analysis):
        """Affiche l'analyse IA complète"""
        self.analysis_text.delete(1.0, tk.END)
        
        # Titre
        self.analysis_text.insert(tk.END, "🤖 ANALYSE NUTRITIONNELLE IA\n", 'title')
        self.analysis_text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Résumé global
        self.analysis_text.insert(tk.END, "📊 RÉSUMÉ NUTRITIONNEL\n", 'heading')
        self.analysis_text.insert(tk.END, f"🔥 Calories totales: {analysis.total_calories:.0f} kcal\n")
        self.analysis_text.insert(tk.END, f"🥩 Protéines: {analysis.total_proteins:.1f} g\n")
        self.analysis_text.insert(tk.END, f"🍞 Glucides: {analysis.total_carbs:.1f} g\n")
        self.analysis_text.insert(tk.END, f"🥑 Lipides: {analysis.total_fats:.1f} g\n\n")
        
        # Conseils IA
        if analysis.health_tips:
            self.analysis_text.insert(tk.END, "💡 CONSEILS NUTRITIONNELS IA\n", 'heading')
            self.analysis_text.insert(tk.END, f"{analysis.health_tips}\n\n")
        
        # Répartition des macronutriments
        total_macros = analysis.total_proteins + analysis.total_carbs + analysis.total_fats
        if total_macros > 0:
            self.analysis_text.insert(tk.END, "📈 RÉPARTITION DES MACRONUTRIMENTS\n", 'heading')
            protein_pct = (analysis.total_proteins / total_macros) * 100
            carbs_pct = (analysis.total_carbs / total_macros) * 100
            fats_pct = (analysis.total_fats / total_macros) * 100
            
            self.analysis_text.insert(tk.END, f"🥩 Protéines: {protein_pct:.1f}%\n")
            self.analysis_text.insert(tk.END, f"🍞 Glucides: {carbs_pct:.1f}%\n")
            self.analysis_text.insert(tk.END, f"🥑 Lipides: {fats_pct:.1f}%\n\n")
        
        # Détail par aliment
        if self.current_calculations:
            self.analysis_text.insert(tk.END, "🔍 DÉTAIL PAR ALIMENT\n", 'heading')
            self.analysis_text.insert(tk.END, "-" * 40 + "\n")
            
            for calc in self.current_calculations:
                self.analysis_text.insert(tk.END, f"\n📍 {calc.ingredient_name.upper()}\n")
                self.analysis_text.insert(tk.END, f"   Quantité: {calc.quantity} {calc.unit}\n")
                self.analysis_text.insert(tk.END, f"   Calories: {calc.total_calories:.0f} kcal\n")
                self.analysis_text.insert(tk.END, f"   Protéines: {calc.proteins:.1f} g\n")
                self.analysis_text.insert(tk.END, f"   Glucides: {calc.carbs:.1f} g\n")
                self.analysis_text.insert(tk.END, f"   Lipides: {calc.fats:.1f} g\n")
                if calc.fiber > 0:
                    self.analysis_text.insert(tk.END, f"   Fibres: {calc.fiber:.1f} g\n")
    
    def show_welcome_analysis(self):
        """Message de bienvenue pour l'analyse"""
        welcome = """🎉 Calculateur de Calories IA

🤖 FONCTIONNEMENT:
✅ Ajoutez vos aliments avec leurs quantités
✅ Cliquez sur "ANALYSER AVEC IA" 
✅ llama3.2:1b analysera votre repas complet
✅ Obtenez des conseils nutritionnels personnalisés !

🔧 PRÉREQUIS:
⚠️ Ollama doit être démarré: ollama serve
⚠️ llama3.2:1b doit être installé: ollama pull llama3.2:1b

📊 ANALYSES DISPONIBLES:
• Calories et macronutriments détaillés
• Conseils santé personnalisés par IA
• Répartition nutritionnelle optimale
• Export des résultats en CSV"""

        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, welcome)
    
    def export_analysis(self):
        """Exporte l'analyse en CSV"""
        if not self.current_calculations:
            messagebox.showwarning("Aucune analyse", "Réalisez d'abord une analyse")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # En-têtes
                    writer.writerow(['Aliment', 'Quantité', 'Unité', 'Calories', 'Protéines', 'Glucides', 'Lipides', 'Fibres'])
                    
                    # Données
                    for calc in self.current_calculations:
                        writer.writerow([
                            calc.ingredient_name,
                            calc.quantity,
                            calc.unit,
                            f"{calc.total_calories:.1f}",
                            f"{calc.proteins:.1f}",
                            f"{calc.carbs:.1f}",
                            f"{calc.fats:.1f}",
                            f"{calc.fiber:.1f}"
                        ])
                    
                    # Totaux
                    total_calories = sum(calc.total_calories for calc in self.current_calculations)
                    total_proteins = sum(calc.proteins for calc in self.current_calculations)
                    total_carbs = sum(calc.carbs for calc in self.current_calculations)
                    total_fats = sum(calc.fats for calc in self.current_calculations)
                    
                    writer.writerow([])
                    writer.writerow(['TOTAL', '', '', 
                                   f"{total_calories:.1f}",
                                   f"{total_proteins:.1f}",
                                   f"{total_carbs:.1f}",
                                   f"{total_fats:.1f}",
                                   ""])
                
                messagebox.showinfo("Export", f"✅ Analyse exportée vers {filename}")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"❌ Erreur d'export: {e}")
    
    def clear_analysis(self):
        """Remet à zéro l'analyse"""
        self.total_calories_var.set("0 kcal")
        self.total_proteins_var.set("0 g")
        self.total_carbs_var.set("0 g")
        self.total_fats_var.set("0 g")
        self.current_calculations.clear()
        self.show_welcome_analysis()

class MainApplication:
    """Application principale avec onglets séparés"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.config = Config()
        self.setup_window()
        
        # Services
        self.data_manager = None
        self.ollama_service = None
        self.recipe_service = None
        self.calorie_service = None
        
        # Interface
        self.create_interface()
        self.initialize_services()
    
    def setup_window(self):
        """Configuration de la fenêtre"""
        self.root.title(self.config.APP_TITLE)
        self.root.geometry(self.config.APP_GEOMETRY)
        self.root.configure(bg='#F8F9FA')
        
        # Centrer
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
    
    def create_interface(self):
        """Crée l'interface principale"""
        # En-tête
        header_frame = tk.Frame(self.root, bg='#FF6B35', height=80)
        header_frame.pack(fill='x', side='top')
        header_frame.pack_propagate(False)
        
        # Titre et statut
        title_label = tk.Label(header_frame, text=self.config.APP_TITLE,
                              font=('Segoe UI', 18, 'bold'),
                              bg='#FF6B35', fg='white')
        title_label.pack(side='left', padx=20, pady=25)
        
        self.status_label = tk.Label(header_frame, text="🔄 Initialisation...",
                                   font=('Segoe UI', 12),
                                   bg='#FF6B35', fg='white')
        self.status_label.pack(side='right', padx=20, pady=25)
        
        # Notebook avec onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Onglet Générateur de recettes
        self.recipe_frame = tk.Frame(self.notebook)
        self.notebook.add(self.recipe_frame, text="🍽️ Générateur de Recettes")
        
        # Onglet Calculateur de calories
        self.calorie_frame = tk.Frame(self.notebook)
        self.notebook.add(self.calorie_frame, text="📊 Calculateur de Calories")
        
        # Onglet Status/Test
        self.status_frame = tk.Frame(self.notebook)
        self.notebook.add(self.status_frame, text="🤖 Statut IA")
        self.create_status_tab()
        
        # Barre de statut
        status_bar = tk.Frame(self.root, bg='#FFE066', height=30)
        status_bar.pack(fill='x', side='bottom')
        status_bar.pack_propagate(False)
        
        self.bottom_status = tk.Label(status_bar, text="Application prête",
                                    bg='#FFE066', font=('Segoe UI', 10))
        self.bottom_status.pack(side='left', padx=10, pady=5)
    
    def create_status_tab(self):
        """Onglet de statut et test de l'IA"""
        # Titre
        title_label = tk.Label(self.status_frame, text="🤖 Statut llama3.2:1b",
                              font=('Segoe UI', 16, 'bold'))
        title_label.pack(pady=20)
        
        # Zone de statut
        status_info_frame = tk.LabelFrame(self.status_frame, text="📊 État des services",
                                        font=('Segoe UI', 12, 'bold'))
        status_info_frame.pack(fill='x', padx=50, pady=20)
        
        self.ollama_status_var = tk.StringVar(value="🔄 Vérification en cours...")
        self.model_status_var = tk.StringVar(value="🔄 Vérification en cours...")
        
        tk.Label(status_info_frame, text="🌐 Ollama:", font=('Segoe UI', 11)).grid(row=0, column=0, sticky='w', padx=10, pady=5)
        tk.Label(status_info_frame, textvariable=self.ollama_status_var, font=('Segoe UI', 11)).grid(row=0, column=1, sticky='w', padx=10, pady=5)
        
        tk.Label(status_info_frame, text="🤖 llama3.2:1b:", font=('Segoe UI', 11)).grid(row=1, column=0, sticky='w', padx=10, pady=5)
        tk.Label(status_info_frame, textvariable=self.model_status_var, font=('Segoe UI', 11)).grid(row=1, column=1, sticky='w', padx=10, pady=5)
        
        status_info_frame.grid_columnconfigure(1, weight=1)
        
        # Bouton de test
        tk.Button(self.status_frame, text="🧪 TESTER llama3.2:1b",
                 command=self.test_ai_full,
                 bg='#FF6B35', fg='white',
                 font=('Segoe UI', 12, 'bold'),
                 height=2, width=20).pack(pady=20)
        
        # Zone de résultats de test
        test_frame = tk.LabelFrame(self.status_frame, text="📝 Résultats des tests")
        test_frame.pack(fill='both', expand=True, padx=50, pady=20)
        
        self.test_text = scrolledtext.ScrolledText(test_frame, height=15)
        self.test_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Instructions
        instructions = """🔧 INSTRUCTIONS POUR llama3.2:1b:

1️⃣ INSTALLER OLLAMA:
   • Windows/Mac: https://ollama.ai/download
   • Linux: curl -fsSL https://ollama.ai/install.sh | sh

2️⃣ DÉMARRER OLLAMA:
   ollama serve

3️⃣ INSTALLER LE MODÈLE:
   ollama pull llama3.2:1b

4️⃣ TESTER:
   ollama run llama3.2:1b "Bonjour"

✅ Une fois ces étapes terminées, l'application fonctionnera pleinement !"""
        
        self.test_text.insert(tk.END, instructions)
    
    def initialize_services(self):
        """Initialise les services"""
        def init_thread():
            try:
                self.root.after(0, lambda: self.status_label.config(text="🔄 Initialisation..."))
                
                # Configuration
                Config.ensure_data_dir()
                
                # Services
                self.data_manager = DataManager(self.config)
                self.ollama_service = OllamaService(self.config)
                self.recipe_service = RecipeService(self.ollama_service, self.config)
                self.calorie_service = CalorieService(self.ollama_service, self.data_manager, self.config)
                
                self.root.after(0, self.on_services_ready)
                
            except Exception as e:
                self.root.after(0, lambda: self.on_init_error(str(e)))
        
        threading.Thread(target=init_thread, daemon=True).start()
    
    def on_services_ready(self):
        """Services prêts"""
        # Créer les onglets
        self.recipe_tab = RecipeTab(self.recipe_frame, self.config, self.recipe_service, self.data_manager)
        self.calorie_tab = CalorieTab(self.calorie_frame, self.config, self.calorie_service, self.data_manager)
        
        # Tester la connexion
        self.test_ai_connection()
        
        self.status_label.config(text="✅ Services prêts")
        self.bottom_status.config(text="✅ Application prête - Sélectionnez un onglet pour commencer")
    
    def on_init_error(self, error):
        """Erreur d'initialisation"""
        self.status_label.config(text="❌ Erreur")
        messagebox.showerror("Erreur", f"❌ Erreur d'initialisation: {error}")
    
    def test_ai_connection(self):
        """Test silencieux de la connexion"""
        def test_thread():
            try:
                result = self.ollama_service.test_connection()
                self.root.after(0, lambda: self.update_ai_status(result))
            except Exception:
                self.root.after(0, lambda: self.update_ai_status({
                    'ollama_available': False,
                    'model_available': False,
                    'error': 'Erreur de connexion'
                }))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def update_ai_status(self, result):
        """Met à jour le statut IA"""
        if result['ollama_available']:
            self.ollama_status_var.set("✅ Disponible")
            if result['model_available']:
                self.model_status_var.set("✅ Disponible")
                self.status_label.config(text="🤖 llama3.2:1b prêt")
            else:
                self.model_status_var.set("❌ Non installé")
                self.status_label.config(text="⚠️ llama3.2:1b manquant")
        else:
            self.ollama_status_var.set("❌ Non disponible")
            self.model_status_var.set("❌ Non accessible")
            self.status_label.config(text="❌ Ollama non disponible")
    
    def test_ai_full(self):
        """Test complet avec affichage"""
        def test_thread():
            try:
                result = self.ollama_service.test_connection()
                self.root.after(0, lambda: self.show_test_results(result))
            except Exception as e:
                self.root.after(0, lambda: self.show_test_results({
                    'ollama_available': False,
                    'model_available': False,
                    'error': str(e)
                }))
        
        # Vider et démarrer le test
        self.test_text.delete(1.0, tk.END)
        self.test_text.insert(tk.END, "🧪 Test en cours...\n\n")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def show_test_results(self, result):
        """Affiche les résultats du test"""
        self.test_text.delete(1.0, tk.END)
        
        # Résultats
        self.test_text.insert(tk.END, "🧪 RÉSULTATS DU TEST llama3.2:1b\n")
        self.test_text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Ollama
        ollama_status = "✅ Disponible" if result['ollama_available'] else "❌ Non disponible"
        self.test_text.insert(tk.END, f"🌐 Ollama: {ollama_status}\n")
        
        # Modèle
        model_status = "✅ Disponible" if result['model_available'] else "❌ Non installé"
        self.test_text.insert(tk.END, f"🤖 llama3.2:1b: {model_status}\n\n")
        
        # Test de génération
        if result['test_response']:
            self.test_text.insert(tk.END, "📝 TEST DE GÉNÉRATION:\n")
            self.test_text.insert(tk.END, f"Réponse: {result['test_response']}\n\n")
            self.test_text.insert(tk.END, "🎉 llama3.2:1b fonctionne parfaitement !\n\n")
        
        # Instructions selon l'état
        self.test_text.insert(tk.END, "🔧 ACTIONS RECOMMANDÉES:\n")
        
        if not result['ollama_available']:
            self.test_text.insert(tk.END, "❌ Ollama n'est pas disponible\n")
            self.test_text.insert(tk.END, "   → Démarrez Ollama: ollama serve\n")
            self.test_text.insert(tk.END, "   → Ou installez Ollama: https://ollama.ai/\n\n")
        
        elif not result['model_available']:
            self.test_text.insert(tk.END, "❌ llama3.2:1b n'est pas installé\n")
            self.test_text.insert(tk.END, "   → Installez le modèle: ollama pull llama3.2:1b\n\n")
        
        else:
            self.test_text.insert(tk.END, "✅ Tout fonctionne ! Vous pouvez utiliser l'application.\n\n")
        
        # Erreurs
        if result.get('error'):
            self.test_text.insert(tk.END, f"⚠️ Erreur détectée: {result['error']}\n")
        
        # Mettre à jour le statut
        self.update_ai_status(result)
    
    def run(self):
        """Lance l'application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()

# ===== FONCTION PRINCIPALE =====
def main():
    """Point d'entrée principal"""
    try:
        print("🚀 Lancement de l'Assistant Culinaire & Calories IA v3.0")
        print("=" * 60)
        print("🔧 Vérification des dépendances...")
        
        # Vérifier les modules
        required_modules = ['tkinter', 'requests', 'pandas']
        missing = []
        
        for module in required_modules:
            try:
                if module == 'tkinter':
                    import tkinter
                elif module == 'requests':
                    import requests
                elif module == 'pandas':
                    import pandas
            except ImportError:
                missing.append(module)
        
        if missing:
            print(f"❌ Modules manquants: {', '.join(missing)}")
            print(f"💡 Installez: pip install {' '.join(missing)}")
            return 1
        
        print("✅ Dépendances OK")
        print("🎨 Lancement de l'interface...")
        
        app = MainApplication()
        
        print("✅ Application prête !")
        print("=" * 60)
        print("💡 GUIDE D'UTILISATION:")
        print("• Onglet 'Générateur': Sélectionnez ingrédients → Générez avec IA")
        print("• Onglet 'Calculateur': Ajoutez aliments → Analysez avec IA")
        print("• Onglet 'Statut IA': Testez llama3.2:1b")
        print("• OBLIGATOIRE: ollama serve + ollama pull llama3.2:1b")
        print("=" * 60)
        
        app.run()
        
        print("👋 Application fermée !")
        return 0
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Erreur", f"Impossible de démarrer:\n\n{e}")
            root.destroy()
        except:
            pass
        
        return 1

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print("""
🍽️ Assistant Culinaire & Calories IA v3.0

UTILISATION:
    python main.py              # Lancer l'application
    python main.py --help       # Afficher cette aide

FONCTIONNALITÉS:
• Génération de recettes avec llama3.2:1b (OBLIGATOIRE)
• Calcul de calories avec analyse IA
• Onglets séparés pour chaque fonction
• Interface moderne et intuitive
• Export des résultats

PRÉREQUIS OBLIGATOIRES:
• Python 3.7+
• Modules: tkinter, requests, pandas
• Ollama installé et démarré: ollama serve
• Modèle llama3.2:1b: ollama pull llama3.2:1b

INSTALLATION:
1. Installer Ollama: https://ollama.ai/
2. Démarrer: ollama serve
3. Installer modèle: ollama pull llama3.2:1b
4. Lancer: python main.py

L'application ne fonctionnera PAS sans llama3.2:1b !
            """)
            sys.exit(0)
    
    sys.exit(main())
        #!/usr/bin/env python3
"""
Assistant Culinaire & Calories IA - Version 3.0
Application structurée avec onglets séparés et llama3.2:1b obligatoire

Version: 3.0.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import csv
from datetime import datetime
from typing import List, Dict, Any

# Imports locaux
from config import Config
from models import DataManager, Recipe, CalorieCalculation
from ollama_service import OllamaService
from recipe_service import RecipeService
from calorie_service import CalorieService

class LoadingDialog:
    """Dialogue de chargement pour les opérations IA"""
    def __init__(self, parent, message):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("⏳ llama3.2:1b en action")
        self.dialog.geometry("450x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrer
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 225
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 75
        self.dialog.geometry(f"450x150+{x}+{y}")
        
        # Interface
        tk.Label(self.dialog, text="🤖 llama3.2:1b travaille...", 
                font=('Segoe UI', 14, 'bold')).pack(pady=15)
        tk.Label(self.dialog, text=message, 
                font=('Segoe UI', 11)).pack(pady=5)
        
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate')
        self.progress.pack(pady=15, padx=30, fill='x')
        self.progress.start()
    
    def destroy(self):
        self.progress.stop()
        self.dialog.destroy()

class RecipeTab:
    """Onglet Générateur de Recettes"""
    
    def __init__(self, parent, config, recipe_service, data_manager):
        self.parent = parent
        self.config = config
        self.recipe_service = recipe_service
        self.data_manager = data_manager
        
        self.selected_ingredients = []
        self.current_recipe = None
        
        self.create_interface()
        self.load_ingredients()
    
    def create_interface(self):
        """Crée l'interface de l'onglet recettes"""
        # Configuration en colonnes
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=2)
        self.parent.grid_rowconfigure(0, weight=1)
        
        # Panneau gauche: Sélection d'ingrédients
        left_frame = tk.LabelFrame(self.parent, text="🛒 Sélection d'ingrédients",
                                  font=('Segoe UI', 12, 'bold'))
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)
        
        self.create_ingredients_panel(left_frame)
        
        # Panneau droit: Génération et affichage
        right_frame = tk.LabelFrame(self.parent, text="🍽️ Recette générée par llama3.2:1b",
                                   font=('Segoe UI', 12, 'bold'))
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)
        
        self.create_recipe_panel(right_frame)
    
    def create_ingredients_panel(self, parent):
        """Panneau de sélection d'ingrédients"""
        # Recherche
        search_frame = tk.Frame(parent)
        search_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(search_frame, text="🔍 Rechercher:", font=('Segoe UI', 10)).pack(anchor='w')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_changed)
        tk.Entry(search_frame, textvariable=self.search_var).pack(fill='x', pady=5)
        
        # Catégories
        category_frame = tk.Frame(parent)
        category_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(category_frame, text="📂 Catégorie:", font=('Segoe UI', 10)).pack(anchor='w')
        self.category_var = tk.StringVar(value="Toutes")
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, state='readonly')
        self.category_combo.pack(fill='x', pady=5)
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_changed)
        
        # Zone d'ingrédients avec scrollbar
        ingredients_container = tk.Frame(parent)
        ingredients_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(ingredients_container)
        scrollbar = ttk.Scrollbar(ingredients_container, orient="vertical", command=canvas.yview)
        self.ingredients_scroll_frame = tk.Frame(canvas)
        
        self.ingredients_scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.ingredients_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.ingredient_buttons = {}
        
        # Ingrédients sélectionnés
        selected_frame = tk.LabelFrame(parent, text="✅ Sélectionnés")
        selected_frame.pack(fill='x', padx=10, pady=10)
        
        self.selected_listbox = tk.Listbox(selected_frame, height=6)
        self.selected_listbox.pack(fill='x', padx=5, pady=5)
        
        # Boutons
        buttons_frame = tk.Frame(selected_frame)
        buttons_frame.pack(fill='x', pady=5)
        
        tk.Button(buttons_frame, text="🗑️ Vider", command=self.clear_selection,
                 bg='#6c757d', fg='white').pack(side='left', padx=5)
    
    def create_recipe_panel(self, parent):
        """Panneau de génération et affichage de recettes"""
        # Options de génération
        options_frame = tk.LabelFrame(parent, text="🎛️ Options de génération")
        options_frame.pack(fill='x', padx=10, pady=10)
        
        # Grille pour les options
        tk.Label(options_frame, text="🌍 Cuisine:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.cuisine_var = tk.StringVar()
        cuisine_combo = ttk.Combobox(options_frame, textvariable=self.cuisine_var,
                                   values=["", "🇫🇷 Française", "🇮🇹 Italienne", "🇨🇳 Asiatique", 
                                          "🇬🇷 Méditerranéenne", "🇲🇽 Mexicaine"])
        cuisine_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        
        tk.Label(options_frame, text="⭐ Difficulté:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.difficulty_var = tk.StringVar()
        difficulty_combo = ttk.Combobox(options_frame, textvariable=self.difficulty_var,
                                      values=["", "🟢 Facile", "🟡 Moyen", "🔴 Difficile"])
        difficulty_combo.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        tk.Label(options_frame, text="⏰ Temps:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.time_var = tk.StringVar()
        time_combo = ttk.Combobox(options_frame, textvariable=self.time_var,
                                values=["", "⚡ 15 min", "🕐 30 min", "🕑 1 heure"])
        time_combo.grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        
        options_frame.grid_columnconfigure(1, weight=1)
        
        # Bouton de génération
        self.generate_btn = tk.Button(options_frame, text="🤖 GÉNÉRER AVEC llama3.2:1b",
                                    command=self.generate_recipe,
                                    bg='#FF6B35', fg='white', 
                                    font=('Segoe UI', 12, 'bold'),
                                    height=2, cursor='hand2')
        self.generate_btn.grid(row=3, column=0, columnspan=2, pady=15, sticky='ew')
        
        # Zone d'affichage de la recette
        self.recipe_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, height=25)
        self.recipe_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tags pour le formatage
        self.recipe_text.tag_configure('title', font=('Segoe UI', 16, 'bold'), foreground='#FF6B35')
        self.recipe_text.tag_configure('heading', font=('Segoe UI', 12, 'bold'), foreground='#004E98')
        
        # Boutons d'action
        action_frame = tk.Frame(parent)
        action_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(action_frame, text="📄 Exporter", command=self.export_recipe,
                 bg='#004E98', fg='white').pack(side='left', padx=5)
        
        tk.Button(action_frame, text="🔄 Nouveau", command=self.clear_all,
                 bg='#6c757d', fg='white').pack(side='right', padx=5)
        
        # Message initial
        self.show_welcome_message()
    
    def load_ingredients(self):
        """Charge les ingrédients"""
        if not self.data_manager:
            return
        
        ingredients = self.data_manager.get_all_ingredients()
        
        # Catégories
        categories = sorted(set(ing.category for ing in ingredients))
        self.category_combo['values'] = ["Toutes"] + categories
        
        # Afficher les ingrédients
        self.display_ingredients(ingredients)
    
    def display_ingredients(self, ingredients):
        """Affiche les ingrédients comme boutons"""
        # Vider le frame
        for widget in self.ingredients_scroll_frame.winfo_children():
            widget.destroy()
        
        self.ingredient_buttons.clear()
        
        # Créer les boutons
        row, col = 0, 0
        for ingredient in sorted(ingredients, key=lambda x: x.name):
            # Emoji selon catégorie
            emoji_map = {
                "Légume": "🥬", "Viande": "🥩", "Poisson": "🐟",
                "Produit laitier": "🥛", "Fruit": "🍎", "Céréale": "🌾",
                "Matière grasse": "🧈", "Aromate": "🌿"
            }
            emoji = emoji_map.get(ingredient.category, "🍽️")
            
            btn_text = f"{emoji} {ingredient.name.title()}"
            
            btn = tk.Button(self.ingredients_scroll_frame, text=btn_text,
                          command=lambda ing=ingredient.name: self.toggle_ingredient(ing),
                          width=18, height=2, bg='lightgray', relief='raised', bd=2)
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
            
            self.ingredient_buttons[ingredient.name] = btn
            
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        # Configurer les colonnes
        self.ingredients_scroll_frame.grid_columnconfigure(0, weight=1)
        self.ingredients_scroll_frame.grid_columnconfigure(1, weight=1)
    
    def on_search_changed(self, *args):
        """Filtrage par recherche"""
        self.filter_ingredients()
    
    def on_category_changed(self, event=None):
        """Filtrage par catégorie"""
        self.filter_ingredients()
    
    def filter_ingredients(self):
        """Applique les filtres"""
        if not self.data_manager:
            return
        
        search_term = self.search_var.get().lower()
        selected_category = self.category_var.get()
        
        all_ingredients = self.data_manager.get_all_ingredients()
        filtered = []
        
        for ingredient in all_ingredients:
            if search_term and search_term not in ingredient.name.lower():
                continue
            if selected_category != "Toutes" and ingredient.category != selected_category:
                continue
            filtered.append(ingredient)
        
        self.display_ingredients(filtered)
    
    def toggle_ingredient(self, ingredient_name):
        """Ajoute/retire un ingrédient"""
        btn = self.ingredient_buttons.get(ingredient_name)
        if not btn:
            return
        
        if ingredient_name in self.selected_ingredients:
            self.selected_ingredients.remove(ingredient_name)
            btn.config(bg='lightgray', relief='raised')
        else:
            self.selected_ingredients.append(ingredient_name)
            btn.config(bg='lightgreen', relief='sunken')
        
        self.update_selected_display()
    
    def update_selected_display(self):
        """Met à jour l'affichage des sélectionnés"""
        self.selected_listbox.delete(0, tk.END)
        
        for ingredient in self.selected_ingredients:
            self.selected_listbox.insert(tk.END, f"✅ {ingredient.title()}")
        
        # Activer/désactiver le bouton
        if self.selected_ingredients:
            self.generate_btn.config(state='normal', bg='#FF6B35')
        else:
            self.generate_btn.config(state='disabled', bg='gray')
    
    def clear_selection(self):
        """Vide la sélection"""
        for ingredient_name in self.selected_ingredients.copy():
            btn = self.ingredient_buttons.get(ingredient_name)
            if btn:
                btn.config(bg='lightgray', relief='raised')
        
        self.selected_ingredients.clear()
        self.update_selected_display()
    
    def generate_recipe(self):
        """Génère une recette avec llama3.2:1b"""
        if not self.selected_ingredients:
            messagebox.showwarning("Attention", "🚨 Sélectionnez au moins un ingrédient !")
            return
        
        loading = LoadingDialog(self.parent, "Génération de la recette française...")
        
        def generate_thread():
            try:
                recipe = self.recipe_service.generate_recipe(
                    self.selected_ingredients,
                    self.cuisine_var.get(),
                    self.difficulty_var.get(),
                    self.time_var.get()
                )
                
                self.parent.after(0, lambda: self.on_recipe_generated(recipe, loading))
                
            except Exception as e:
                self.parent.after(0, lambda: self.on_generation_error(str(e), loading))
        
        thread = threading.Thread(target=generate_thread, daemon=True)
        thread.start()
    
    def on_recipe_generated(self, recipe, loading_dialog):
        """Affiche la recette générée"""
        loading_dialog.destroy()
        
        self.current_recipe = recipe
        self.display_recipe(recipe)
        messagebox.showinfo("Succès", "🎉 Recette générée avec succès par llama3.2:1b !")
    
    def on_generation_error(self, error, loading_dialog):
        """Gestion des erreurs"""
        loading_dialog.destroy()
        messagebox.showerror("Erreur", error)
    
    def display_recipe(self, recipe):
        """Affiche une recette"""
        self.recipe_text.delete(1.0, tk.END)
        
        # Titre
        self.recipe_text.insert(tk.END, f"🍽️ {recipe.title}\n", 'title')
        self.recipe_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # Informations
        self.recipe_text.insert(tk.END, "📋 INFORMATIONS\n", 'heading')
        self.recipe_text.insert(tk.END, f"⏰ Temps: {recipe.prep_time}\n")
        self.recipe_text.insert(tk.END, f"⭐ Difficulté: {recipe.difficulty}\n")
        if recipe.tips:
            self.recipe_text.insert(tk.END, f"💡 Conseil: {recipe.tips}\n")
        self.recipe_text.insert(tk.END, "\n")
        
        # Ingrédients
        self.recipe_text.insert(tk.END, "🛒 INGRÉDIENTS\n", 'heading')
        for ingredient in recipe.ingredients:
            self.recipe_text.insert(tk.END, f"• {ingredient['name']}: {ingredient['quantity']} {ingredient['unit']}\n")
        self.recipe_text.insert(tk.END, "\n")
        
        # Préparation
        self.recipe_text.insert(tk.END, "👨‍🍳 PRÉPARATION\n", 'heading')
        for i, step in enumerate(recipe.steps, 1):
            self.recipe_text.insert(tk.END, f"{i}. {step}\n")
    
    def show_welcome_message(self):
        """Message de bienvenue"""
        welcome = """🎉 Générateur de Recettes IA

🤖 FONCTIONNEMENT:
✅ Sélectionnez vos ingrédients à gauche
✅ Choisissez vos options (cuisine, difficulté, temps)
✅ Cliquez sur "GÉNÉRER AVEC llama3.2:1b"
✅ Obtenez une recette française personnalisée !

🔧 PRÉREQUIS:
⚠️ Ollama doit être démarré: ollama serve
⚠️ llama3.2:1b doit être installé: ollama pull llama3.2:1b

💡 ASTUCE: Plus d'ingrédients = recette plus créative !"""

        self.recipe_text.delete(1.0, tk.END)
        self.recipe_text.insert(tk.END, welcome)
    
    def export_recipe(self):
        """Exporte la recette"""
        if not self.current_recipe:
            messagebox.showwarning("Aucune recette", "Générez d'abord une recette !")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self._format_recipe_for_export())
                messagebox.showinfo("Export", f"✅ Recette exportée vers {filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"❌ Erreur d'export: {e}")
    
    def _format_recipe_for_export(self):
        """Formate la recette pour l'export"""
        recipe = self.current_recipe
        lines = [
            f"🍽️ {recipe.title}",
            "=" * 60,
            "",
            "📋 INFORMATIONS:",
            f"⏰ Temps: {recipe.prep_time}",
            f"⭐ Difficulté: {recipe.difficulty}",
            f"💡 Conseil: {recipe.tips}",
            "",
            "🛒 INGRÉDIENTS:"
        ]
        
        for ing in recipe.ingredients:
            lines.append(f"• {ing['name']}: {ing['quantity']} {ing['unit']}")
        
        lines.extend(["", "👨‍🍳 PRÉPARATION:"])
        for i, step in enumerate(recipe.steps, 1):
            lines.append(f"{i}. {step}")
        
        lines.extend([
            "",
            "=" * 60,
            f"Généré par llama3.2:1b - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ])
        
        return "\n".join(lines)
    
    def clear_all(self):
        """Remet à zéro"""
        self.clear_selection()
        self.cuisine_var.set("")
        self.difficulty_var.set("")
        self.time_var.set("")
        self.current_recipe = None
        self.show_welcome_message()

class CalorieTab:
    """Onglet Calculateur de Calories"""
    
    def __init__(self, parent, config, calorie_service, data_manager):
        self.parent = parent
        self.config = config
        self.calorie_service = calorie_service
        self.data_manager = data_manager
        
        self.foods_data = []
        self.current_calculations = []
        
        self.create_interface()
    
    def create_interface(self):
        """Crée l'interface de l'onglet calories"""
        # Configuration en colonnes
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)
        
        # Panneau gauche: Saisie
        left_frame = tk.LabelFrame(self.parent, text="🍽️ Saisie des aliments",
                                  font=('Segoe UI', 12, 'bold'))
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)
        
        self.create_input_panel(left_frame)
        
        # Panneau droit: Analyse
        right_frame = tk.LabelFrame(self.parent, text="📊 Analyse nutritionnelle IA",
                                   font=('Segoe UI', 12, 'bold'))
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)
        
        self.create_analysis_panel(right_frame)
    
    def create_input_panel(self, parent):
        """Panneau de saisie des aliments"""
        # Sélection d'aliment
        input_frame = tk.Frame(parent)
        input_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(input_frame, text="🥘 Aliment:", font=('Segoe UI', 10)).grid(row=0, column=0, sticky='w')
        
        self.food_var = tk.StringVar()
        self.food_combo = ttk.Combobox(input_frame, textvariable=self.food_var, width=25)
        self.food_combo.grid(row=0, column=1, sticky='ew', padx=5)
        
        tk.Label(input_frame, text="📏 Quantité:", font=('Segoe UI', 10)).grid(row=1, column=0, sticky='w')
        
        quantity_frame = tk.Frame(input_frame)
        quantity_frame.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        self.quantity_var = tk.StringVar(value="100")
        tk.Entry(quantity_frame, textvariable=self.quantity_var, width=10).pack(side='left')
        
        self.unit_var = tk.StringVar(value="g")
        unit_combo = ttk.Combobox(quantity_frame, textvariable=self.unit_var,
                                 values=["g", "kg", "ml", "l", "tasse", "cuillère", "portion", "unité"],
                                 width=10, state='readonly')
        unit_combo.pack(side='left', padx=5)
        
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Boutons
        btn_frame = tk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="➕ Ajouter", command=self.add_food,
                 bg='#2ECC71', fg='white', font=('Segoe UI', 10, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="🤖 ANALYSER AVEC IA", command=self.analyze_with_ai,
                 bg='#FF6B35', fg='white', font=('Segoe UI', 10, 'bold')).pack(side='left', padx=5)
        
        # Liste des aliments ajoutés
        list_frame = tk.LabelFrame(parent, text="📋 Aliments ajoutés")
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview
        columns = ('Aliment', 'Quantité', 'Unité', 'Calories')
        self.foods_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.foods_tree.heading(col, text=col)
            self.foods_tree.column(col, width=80)
        
        # Scrollbar
        tree_scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.foods_tree.yview)
        self.foods_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.foods_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        tree_scroll.pack(side='right', fill='y', pady=5)
        
        # Boutons de gestion
        manage_frame = tk.Frame(list_frame)
        manage_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Button(manage_frame, text="🗑️ Supprimer", command=self.remove_food,
                 bg='#dc3545', fg='white').pack(side='left', padx=5)
        tk.Button(manage_frame, text="🧹 Vider tout", command=self.clear_foods,
                 bg='#6c757d', fg='white').pack(side='left', padx=5)
        
        # Charger les aliments disponibles
        self.load_available_foods()
    
    def create_analysis_panel(self, parent):
        """Panneau d'analyse nutritionnelle"""
        # Résumé des totaux
        summary_frame = tk.LabelFrame(parent, text="📊 Totaux nutritionnels")
        summary_frame.pack(fill='x', padx=10, pady=10)
        
        # Variables d'affichage
        self.total_calories_var = tk.StringVar(value="0 kcal")
        self.total_proteins_var = tk.StringVar(value="0 g")
        self.total_carbs_var = tk.StringVar(value="0 g")
        self.total_fats_var = tk.StringVar(value="0 g")
        
        # Affichage en grille
        tk.Label(summary_frame, text="🔥 Calories:", font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        tk.Label(summary_frame, textvariable=self.total_calories_var, font=('Segoe UI', 14, 'bold'), fg='#FF6B35').grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        tk.Label(summary_frame, text="🥩 Protéines:", font=('Segoe UI', 10)).grid(row=1, column=0, sticky='w', padx=5, pady=2)
        tk.Label(summary_frame, textvariable=self.total_proteins_var, font=('Segoe UI', 10)).grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        tk.Label(summary_frame, text="🍞 Glucides:", font=('Segoe UI', 10)).grid(row=2, column=0, sticky='w', padx=5, pady=2)
        tk.Label(summary_frame, textvariable=self.total_carbs_var, font=('Segoe UI', 10)).grid(row=2, column=1, sticky='w', padx=5, pady=2)
        
        tk.Label(summary_frame, text="🥑 Lipides:", font=('Segoe UI', 10)).grid(row=3, column=0, sticky='w', padx=5, pady=2)
        tk.Label(summary_frame, textvariable=self.total_fats_var, font=('Segoe UI', 10)).grid(row=3, column=1, sticky='w', padx=5, pady=2)
        
        summary_frame.grid_columnconfigure(1, weight=1)
        
        # Analyse détaillée avec IA
        details_frame = tk.LabelFrame