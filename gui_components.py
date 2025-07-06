"""
Composants GUI réutilisables
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import List, Dict, Any, Callable, Optional
from models import Ingredient, Recipe
from calorie_service import CalorieService, MealAnalysis
import threading

class IngredientsSelector:
    """Sélecteur d'ingrédients avec recherche et catégories"""
    
    def __init__(self, parent, config, callback: Callable):
        self.parent = parent
        self.config = config
        self.callback = callback
        self.ingredients = []
        self.selected_ingredients = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """Crée les widgets du sélecteur"""
        # Recherche
        search_frame = ttk.Frame(self.parent)
        search_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(search_frame, text="Rechercher:").pack(side='left')
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        # Filtre par catégorie
        filter_frame = ttk.Frame(self.parent)
        filter_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Catégorie:").pack(side='left')
        
        self.category_var = tk.StringVar(value="Toutes")
        self.category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var,
                                          state='readonly')
        self.category_combo.pack(side='left', fill='x', expand=True, padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_changed)
        
        # Liste des ingrédients disponibles
        available_frame = ttk.LabelFrame(self.parent, text="Ingrédients disponibles")
        available_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Listbox avec scrollbar
        listbox_frame = ttk.Frame(available_frame)
        listbox_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.ingredients_listbox = tk.Listbox(listbox_frame, selectmode='extended')
        scrollbar_available = ttk.Scrollbar(listbox_frame, orient='vertical',
                                          command=self.ingredients_listbox.yview)
        self.ingredients_listbox.configure(yscrollcommand=scrollbar_available.set)
        
        self.ingredients_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_available.pack(side='right', fill='y')
        
        # Boutons d'action
        buttons_frame = ttk.Frame(available_frame)
        buttons_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(buttons_frame, text="Ajouter →", 
                  command=self.add_selected).pack(side='left', padx=2)
        ttk.Button(buttons_frame, text="Tout ajouter", 
                  command=self.add_all_visible).pack(side='left', padx=2)
        
        # Liste des ingrédients sélectionnés
        selected_frame = ttk.LabelFrame(self.parent, text="Ingrédients sélectionnés")
        selected_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Listbox sélectionnés
        selected_listbox_frame = ttk.Frame(selected_frame)
        selected_listbox_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.selected_listbox = tk.Listbox(selected_listbox_frame, selectmode='extended')
        scrollbar_selected = ttk.Scrollbar(selected_listbox_frame, orient='vertical',
                                         command=self.selected_listbox.yview)
        self.selected_listbox.configure(yscrollcommand=scrollbar_selected.set)
        
        self.selected_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_selected.pack(side='right', fill='y')
        
        # Boutons pour les sélectionnés
        selected_buttons_frame = ttk.Frame(selected_frame)
        selected_buttons_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(selected_buttons_frame, text="← Retirer", 
                  command=self.remove_selected).pack(side='left', padx=2)
        ttk.Button(selected_buttons_frame, text="Tout retirer", 
                  command=self.remove_all).pack(side='left', padx=2)
    
    def load_ingredients(self, ingredients: List[Ingredient]):
        """Charge la liste des ingrédients"""
        self.ingredients = ingredients
        
        # Extraire les catégories
        categories = sorted(set(ing.category for ing in ingredients))
        self.category_combo['values'] = ["Toutes"] + categories
        
        # Afficher tous les ingrédients
        self.update_ingredients_display()
    
    def on_search_changed(self, *args):
        """Appelé quand la recherche change"""
        self.update_ingredients_display()
    
    def on_category_changed(self, event=None):
        """Appelé quand la catégorie change"""
        self.update_ingredients_display()
    
    def update_ingredients_display(self):
        """Met à jour l'affichage des ingrédients"""
        self.ingredients_listbox.delete(0, tk.END)
        
        search_term = self.search_var.get().lower()
        selected_category = self.category_var.get()
        
        filtered_ingredients = []
        for ingredient in self.ingredients:
            # Filtrer par recherche
            if search_term and search_term not in ingredient.name.lower():
                continue
            
            # Filtrer par catégorie
            if selected_category != "Toutes" and ingredient.category != selected_category:
                continue
            
            # Éviter les doublons dans la sélection
            if ingredient.name not in self.selected_ingredients:
                filtered_ingredients.append(ingredient)
        
        # Trier et afficher
        filtered_ingredients.sort(key=lambda x: x.name)
        for ingredient in filtered_ingredients:
            self.ingredients_listbox.insert(tk.END, ingredient.name)
    
    def add_selected(self):
        """Ajoute les ingrédients sélectionnés"""
        selected_indices = self.ingredients_listbox.curselection()
        for index in selected_indices:
            ingredient_name = self.ingredients_listbox.get(index)
            if ingredient_name not in self.selected_ingredients:
                self.selected_ingredients.append(ingredient_name)
                self.selected_listbox.insert(tk.END, ingredient_name)
        
        self.update_ingredients_display()
        self.callback(self.selected_ingredients)
    
    def add_all_visible(self):
        """Ajoute tous les ingrédients visibles"""
        for i in range(self.ingredients_listbox.size()):
            ingredient_name = self.ingredients_listbox.get(i)
            if ingredient_name not in self.selected_ingredients:
                self.selected_ingredients.append(ingredient_name)
                self.selected_listbox.insert(tk.END, ingredient_name)
        
        self.update_ingredients_display()
        self.callback(self.selected_ingredients)
    
    def remove_selected(self):
        """Retire les ingrédients sélectionnés"""
        selected_indices = list(self.selected_listbox.curselection())
        selected_indices.reverse()  # Supprimer de la fin vers le début
        
        for index in selected_indices:
            ingredient_name = self.selected_listbox.get(index)
            self.selected_ingredients.remove(ingredient_name)
            self.selected_listbox.delete(index)
        
        self.update_ingredients_display()
        self.callback(self.selected_ingredients)
    
    def remove_all(self):
        """Retire tous les ingrédients"""
        self.selected_ingredients.clear()
        self.selected_listbox.delete(0, tk.END)
        self.update_ingredients_display()
        self.callback(self.selected_ingredients)
    
    def clear_selection(self):
        """Vide la sélection"""
        self.remove_all()
        self.search_var.set("")
        self.category_var.set("Toutes")

class RecipeDisplay:
    """Affichage d'une recette générée"""
    
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.current_recipe = None
        
        self.create_widgets()
    
    def pack(self, **kwargs):
        """Méthode pack pour le widget principal"""
        self.main_frame.pack(**kwargs)
    
    def create_widgets(self):
        """Crée les widgets d'affichage"""
        # Frame principal avec scrollbar
        self.main_frame = ttk.LabelFrame(self.parent, text="Recette générée")
        # Ne pas faire pack() ici, sera fait par la méthode pack()
        
        # Zone de texte avec scrollbar
        text_frame = ttk.Frame(self.main_frame)
        text_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.recipe_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            width=50,
            height=20,
            font=self.config.FONTS['default']
        )
        self.recipe_text.pack(fill='both', expand=True)
        
        # Configurer les tags pour le formatage
        self.recipe_text.tag_configure('title', font=self.config.FONTS['title'])
        self.recipe_text.tag_configure('heading', font=self.config.FONTS['heading'])
        self.recipe_text.tag_configure('bold', font=self.config.FONTS['default'] + ('bold',))
        
        # Boutons d'action
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(buttons_frame, text="Copier", 
                  command=self.copy_recipe).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Calculer calories", 
                  command=self.calculate_calories).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Nouvelle recette", 
                  command=self.clear).pack(side='right', padx=5)
    
    def display_recipe(self, recipe: Recipe):
        """Affiche une recette"""
        self.current_recipe = recipe
        self.recipe_text.delete(1.0, tk.END)
        
        # Titre
        self.recipe_text.insert(tk.END, f"{recipe.title}\n", 'title')
        self.recipe_text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Informations générales
        self.recipe_text.insert(tk.END, "INFORMATIONS\n", 'heading')
        self.recipe_text.insert(tk.END, f"Temps de préparation: ", 'bold')
        self.recipe_text.insert(tk.END, f"{recipe.prep_time}\n")
        self.recipe_text.insert(tk.END, f"Difficulté: ", 'bold')
        self.recipe_text.insert(tk.END, f"{recipe.difficulty}\n")
        self.recipe_text.insert(tk.END, f"Calories totales: ", 'bold')
        self.recipe_text.insert(tk.END, f"{recipe.total_calories:.1f} kcal\n\n")
        
        # Ingrédients
        self.recipe_text.insert(tk.END, "INGRÉDIENTS\n", 'heading')
        for ingredient in recipe.ingredients:
            self.recipe_text.insert(tk.END, 
                f"• {ingredient['name']}: {ingredient['quantity']} {ingredient['unit']}\n")
        self.recipe_text.insert(tk.END, "\n")
        
        # Préparation
        self.recipe_text.insert(tk.END, "PRÉPARATION\n", 'heading')
        for i, step in enumerate(recipe.steps, 1):
            self.recipe_text.insert(tk.END, f"{i}. {step}\n")
        
        # Rendre en lecture seule
        self.recipe_text.configure(state='disabled')
    
    def copy_recipe(self):
        """Copie la recette dans le presse-papiers"""
        if self.current_recipe:
            recipe_text = self.recipe_text.get(1.0, tk.END)
            self.parent.clipboard_clear()
            self.parent.clipboard_append(recipe_text)
            messagebox.showinfo("Copié", "Recette copiée dans le presse-papiers")
    
    def calculate_calories(self):
        """Calcule les calories de la recette actuelle"""
        if self.current_recipe:
            # Basculer vers l'onglet calculateur avec les données de la recette
            messagebox.showinfo("Calcul", "Fonctionnalité à implémenter")
    
    def clear(self):
        """Vide l'affichage"""
        self.current_recipe = None
        self.recipe_text.configure(state='normal')
        self.recipe_text.delete(1.0, tk.END)
        self.recipe_text.insert(tk.END, "Aucune recette générée.\n\nSélectionnez des ingrédients et cliquez sur 'Générer la recette' pour commencer.")
        self.recipe_text.configure(state='disabled')

class CalorieCalculator:
    """Calculateur de calories avec interface"""
    
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.data_manager = None
        self.calorie_service = None
        self.current_analysis = None
        
        self.create_widgets()
    
    def pack(self, **kwargs):
        """Méthode pack pour le widget principal"""
        self.parent.pack(**kwargs)
    
    def create_widgets(self):
        """Crée l'interface du calculateur"""
        # Configuration en colonnes
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)
        
        # Panneau de saisie
        input_frame = ttk.LabelFrame(self.parent, text="Saisie des aliments")
        input_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        self.create_input_panel(input_frame)
        
        # Panneau de résultats
        results_frame = ttk.LabelFrame(self.parent, text="Analyse nutritionnelle")
        results_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        
        self.create_results_panel(results_frame)
    
    def create_input_panel(self, parent):
        """Crée le panneau de saisie"""
        # Sélection d'aliment
        selection_frame = ttk.Frame(parent)
        selection_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(selection_frame, text="Aliment:").grid(row=0, column=0, sticky='w')
        
        self.food_var = tk.StringVar()
        self.food_combo = ttk.Combobox(selection_frame, textvariable=self.food_var,
                                      width=20)
        self.food_combo.grid(row=0, column=1, sticky='ew', padx=5)
        selection_frame.grid_columnconfigure(1, weight=1)
        
        # Quantité
        ttk.Label(selection_frame, text="Quantité:").grid(row=1, column=0, sticky='w')
        
        quantity_frame = ttk.Frame(selection_frame)
        quantity_frame.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        self.quantity_var = tk.StringVar(value="100")
        quantity_entry = ttk.Entry(quantity_frame, textvariable=self.quantity_var, width=10)
        quantity_entry.pack(side='left')
        
        self.unit_var = tk.StringVar(value="g")
        unit_combo = ttk.Combobox(quantity_frame, textvariable=self.unit_var,
                                 values=["g", "kg", "ml", "l", "tasse", "cuillère", "portion", "unité"],
                                 width=10, state='readonly')
        unit_combo.pack(side='left', padx=5)
        
        # Boutons
        buttons_frame = ttk.Frame(selection_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(buttons_frame, text="Ajouter", 
                  command=self.add_food).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Calculer", style='Primary.TButton',
                  command=self.calculate_total).pack(side='left', padx=5)
        
        # Liste des aliments ajoutés
        list_frame = ttk.LabelFrame(parent, text="Aliments ajoutés")
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Treeview pour les aliments
        columns = ('Aliment', 'Quantité', 'Unité', 'Calories')
        self.foods_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.foods_tree.heading(col, text=col)
            self.foods_tree.column(col, width=80)
        
        # Scrollbar pour la liste
        foods_scrollbar = ttk.Scrollbar(list_frame, orient='vertical',
                                       command=self.foods_tree.yview)
        self.foods_tree.configure(yscrollcommand=foods_scrollbar.set)
        
        self.foods_tree.pack(side='left', fill='both', expand=True)
        foods_scrollbar.pack(side='right', fill='y')
        
        # Boutons pour la liste
        list_buttons = ttk.Frame(list_frame)
        list_buttons.pack(side='bottom', fill='x', pady=5)
        
        ttk.Button(list_buttons, text="Supprimer", 
                  command=self.remove_food).pack(side='left', padx=5)
        ttk.Button(list_buttons, text="Vider", 
                  command=self.clear_foods).pack(side='left', padx=5)
    
    def create_results_panel(self, parent):
        """Crée le panneau de résultats"""
        # Résumé nutritionnel
        summary_frame = ttk.LabelFrame(parent, text="Résumé")
        summary_frame.pack(fill='x', padx=5, pady=5)
        
        # Variables pour l'affichage
        self.total_calories_var = tk.StringVar(value="0 kcal")
        self.total_proteins_var = tk.StringVar(value="0 g")
        self.total_carbs_var = tk.StringVar(value="0 g")
        self.total_fats_var = tk.StringVar(value="0 g")
        
        # Affichage des totaux
        ttk.Label(summary_frame, text="Calories totales:", font=self.config.FONTS['default']).grid(row=0, column=0, sticky='w', padx=5)
        ttk.Label(summary_frame, textvariable=self.total_calories_var, font=self.config.FONTS['heading']).grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(summary_frame, text="Protéines:").grid(row=1, column=0, sticky='w', padx=5)
        ttk.Label(summary_frame, textvariable=self.total_proteins_var).grid(row=1, column=1, sticky='w', padx=5)
        
        ttk.Label(summary_frame, text="Glucides:").grid(row=2, column=0, sticky='w', padx=5)
        ttk.Label(summary_frame, textvariable=self.total_carbs_var).grid(row=2, column=1, sticky='w', padx=5)
        
        ttk.Label(summary_frame, text="Lipides:").grid(row=3, column=0, sticky='w', padx=5)
        ttk.Label(summary_frame, textvariable=self.total_fats_var).grid(row=3, column=1, sticky='w', padx=5)
        
        # Analyse détaillée
        details_frame = ttk.LabelFrame(parent, text="Analyse détaillée")
        details_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.analysis_text = scrolledtext.ScrolledText(
            details_frame,
            wrap=tk.WORD,
            height=15,
            font=self.config.FONTS['small']
        )
        self.analysis_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Boutons d'export
        export_frame = ttk.Frame(parent)
        export_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(export_frame, text="Exporter CSV",
                  command=self.export_csv).pack(side='left', padx=5)
        ttk.Button(export_frame, text="Comparer besoins",
                  command=self.compare_needs).pack(side='left', padx=5)
    
    def set_data_manager(self, data_manager):
        """Définit le gestionnaire de données"""
        self.data_manager = data_manager
        if data_manager:
            # Charger les noms d'aliments dans le combobox
            ingredients = data_manager.get_all_ingredients()
            food_names = [ing.name for ing in ingredients]
            self.food_combo['values'] = sorted(food_names)
    
    def set_calorie_service(self, calorie_service):
        """Définit le service de calcul de calories"""
        self.calorie_service = calorie_service
    
    def add_food(self):
        """Ajoute un aliment à la liste"""
        food_name = self.food_var.get().strip()
        if not food_name:
            messagebox.showwarning("Aliment manquant", "Veuillez sélectionner un aliment")
            return
        
        try:
            quantity = float(self.quantity_var.get())
            if quantity <= 0:
                raise ValueError("Quantité invalide")
        except ValueError:
            messagebox.showerror("Quantité invalide", "Veuillez saisir une quantité valide")
            return
        
        unit = self.unit_var.get()
        
        # Vérifier que l'aliment existe
        if self.data_manager:
            ingredient = self.data_manager.get_ingredient(food_name)
            if not ingredient:
                messagebox.showerror("Aliment non trouvé", f"L'aliment '{food_name}' n'est pas dans la base de données")
                return
        
        # Ajouter à la liste
        self.foods_tree.insert('', 'end', values=(food_name, quantity, unit, "..."))
        
        # Vider les champs
        self.food_var.set("")
        self.quantity_var.set("100")
        self.unit_var.set("g")
    
    def remove_food(self):
        """Supprime l'aliment sélectionné"""
        selected = self.foods_tree.selection()
        if selected:
            for item in selected:
                self.foods_tree.delete(item)
    
    def clear_foods(self):
        """Vide la liste des aliments"""
        for item in self.foods_tree.get_children():
            self.foods_tree.delete(item)
        self.clear_results()
    
    def calculate_total(self):
        """Calcule le total des calories et nutriments"""
        if not self.calorie_service:
            messagebox.showerror("Erreur", "Service de calcul non disponible")
            return
        
        # Récupérer les données de la liste
        foods_data = []
        for item in self.foods_tree.get_children():
            values = self.foods_tree.item(item)['values']
            foods_data.append({
                'name': values[0],
                'quantity': float(values[1]),
                'unit': values[2]
            })
        
        if not foods_data:
            messagebox.showwarning("Aucun aliment", "Veuillez ajouter au moins un aliment")
            return
        
        # Calculer
        try:
            analysis = self.calorie_service.calculate_calories(foods_data)
            self.current_analysis = analysis
            self.display_analysis(analysis)
            
            # Mettre à jour les calories dans la liste
            for i, item in enumerate(self.foods_tree.get_children()):
                if i < len(analysis.calculations):
                    calc = analysis.calculations[i]
                    values = list(self.foods_tree.item(item)['values'])
                    values[3] = f"{calc.total_calories:.1f}"
                    self.foods_tree.item(item, values=values)
            
        except Exception as e:
            messagebox.showerror("Erreur de calcul", f"Erreur: {e}")
    
    def display_analysis(self, analysis: MealAnalysis):
        """Affiche l'analyse nutritionnelle"""
        # Mettre à jour les totaux
        self.total_calories_var.set(f"{analysis.total_calories:.1f} kcal")
        self.total_proteins_var.set(f"{analysis.total_proteins:.1f} g")
        self.total_carbs_var.set(f"{analysis.total_carbs:.1f} g")
        self.total_fats_var.set(f"{analysis.total_fats:.1f} g")
        
        # Affichage détaillé
        self.analysis_text.delete(1.0, tk.END)
        
        # En-tête
        self.analysis_text.insert(tk.END, "ANALYSE NUTRITIONNELLE DÉTAILLÉE\n")
        self.analysis_text.insert(tk.END, "=" * 40 + "\n\n")
        
        # Résumé
        self.analysis_text.insert(tk.END, "RÉSUMÉ NUTRITIONNEL\n")
        self.analysis_text.insert(tk.END, f"Calories totales: {analysis.total_calories:.1f} kcal\n")
        self.analysis_text.insert(tk.END, f"Protéines: {analysis.total_proteins:.1f} g\n")
        self.analysis_text.insert(tk.END, f"Glucides: {analysis.total_carbs:.1f} g\n")
        self.analysis_text.insert(tk.END, f"Lipides: {analysis.total_fats:.1f} g\n")
        self.analysis_text.insert(tk.END, f"Fibres: {analysis.total_fiber:.1f} g\n\n")
        
        # Répartition des macronutriments
        macros = analysis.get_macros_percentage()
        self.analysis_text.insert(tk.END, "RÉPARTITION DES MACRONUTRIMENTS\n")
        self.analysis_text.insert(tk.END, f"Protéines: {macros['proteins']:.1f}%\n")
        self.analysis_text.insert(tk.END, f"Glucides: {macros['carbs']:.1f}%\n")
        self.analysis_text.insert(tk.END, f"Lipides: {macros['fats']:.1f}%\n\n")
        
        # Détail par aliment
        self.analysis_text.insert(tk.END, "DÉTAIL PAR ALIMENT\n")
        self.analysis_text.insert(tk.END, "-" * 40 + "\n")
        
        for calc in analysis.calculations:
            self.analysis_text.insert(tk.END, f"\n{calc.ingredient_name.upper()}\n")
            self.analysis_text.insert(tk.END, f"Quantité: {calc.quantity} {calc.unit}\n")
            self.analysis_text.insert(tk.END, f"Calories: {calc.total_calories:.1f} kcal\n")
            self.analysis_text.insert(tk.END, f"Protéines: {calc.proteins:.1f} g\n")
            self.analysis_text.insert(tk.END, f"Glucides: {calc.carbs:.1f} g\n")
            self.analysis_text.insert(tk.END, f"Lipides: {calc.fats:.1f} g\n")
            if calc.fiber > 0:
                self.analysis_text.insert(tk.END, f"Fibres: {calc.fiber:.1f} g\n")
    
    def clear_results(self):
        """Vide les résultats"""
        self.total_calories_var.set("0 kcal")
        self.total_proteins_var.set("0 g")
        self.total_carbs_var.set("0 g")
        self.total_fats_var.set("0 g")
        
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, "Aucune analyse disponible.\n\nAjoutez des aliments et cliquez sur 'Calculer' pour voir l'analyse nutritionnelle.")
        
        self.current_analysis = None
    
    def export_csv(self):
        """Exporte l'analyse en CSV"""
        if not self.current_analysis:
            messagebox.showwarning("Aucune analyse", "Aucune analyse à exporter")
            return
        
        from tkinter import filedialog
        import csv
        
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
                    for calc in self.current_analysis.calculations:
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
                    writer.writerow([])
                    writer.writerow(['TOTAL', '', '', 
                                   f"{self.current_analysis.total_calories:.1f}",
                                   f"{self.current_analysis.total_proteins:.1f}",
                                   f"{self.current_analysis.total_carbs:.1f}",
                                   f"{self.current_analysis.total_fats:.1f}",
                                   f"{self.current_analysis.total_fiber:.1f}"])
                
                messagebox.showinfo("Export réussi", f"Analyse exportée vers {filename}")
                
            except Exception as e:
                messagebox.showerror("Erreur d'export", f"Erreur: {e}")
    
    def compare_needs(self):
        """Compare avec les besoins nutritionnels"""
        if not self.current_analysis or not self.calorie_service:
            messagebox.showwarning("Aucune analyse", "Aucune analyse disponible")
            return
        
        # Dialogue simple pour les paramètres
        dialog = NeedsDialog(self.parent, self.config)
        if dialog.result:
            age, gender, activity = dialog.result
            
            comparison = self.calorie_service.get_daily_needs_comparison(
                self.current_analysis, age, gender, activity
            )
            
            self.show_needs_comparison(comparison)
    
    def show_needs_comparison(self, comparison):
        """Affiche la comparaison avec les besoins"""
        message = f"""COMPARAISON AVEC LES BESOINS QUOTIDIENS
        
Calories recommandées: {comparison['recommended_calories']:.0f} kcal
Calories actuelles: {comparison['current_calories']:.1f} kcal
Pourcentage des besoins: {comparison['percentage_of_needs']:.1f}%
Calories restantes: {comparison['remaining_calories']:.0f} kcal

MACRONUTRIMENTS:
Protéines: {comparison['macros_comparison']['proteins']['percentage']:.1f}% des besoins
Glucides: {comparison['macros_comparison']['carbs']['percentage']:.1f}% des besoins
Lipides: {comparison['macros_comparison']['fats']['percentage']:.1f}% des besoins
"""
        
        messagebox.showinfo("Comparaison nutritionnelle", message)
    
    def clear(self):
        """Vide complètement le calculateur"""
        self.clear_foods()
        self.food_var.set("")
        self.quantity_var.set("100")
        self.unit_var.set("g")

class StatusBar:
    """Barre de statut"""
    
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        
        self.frame = ttk.Frame(parent, relief='sunken')
        
        self.status_var = tk.StringVar(value="Prêt")
        self.status_label = ttk.Label(self.frame, textvariable=self.status_var)
        self.status_label.pack(side='left', padx=5)
        
        # Indicateur de connexion Ollama
        self.ollama_var = tk.StringVar(value="Ollama: Non testé")
        self.ollama_label = ttk.Label(self.frame, textvariable=self.ollama_var, 
                                     font=self.config.FONTS['small'])
        self.ollama_label.pack(side='right', padx=5)
    
    def pack(self, **kwargs):
        """Empaquetage de la barre de statut"""
        self.frame.pack(**kwargs)
    
    def set_status(self, message):
        """Met à jour le message de statut"""
        self.status_var.set(message)
    
    def set_ollama_status(self, status):
        """Met à jour le statut Ollama"""
        self.ollama_var.set(f"Ollama: {status}")

class LoadingDialog:
    """Dialogue de chargement"""
    
    def __init__(self, parent, message):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Chargement")
        self.dialog.geometry("300x100")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 150
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 50
        self.dialog.geometry(f"300x100+{x}+{y}")
        
        # Message
        ttk.Label(self.dialog, text=message).pack(pady=20)
        
        # Barre de progression
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate')
        self.progress.pack(pady=10, padx=20, fill='x')
        self.progress.start()
    
    def destroy(self):
        """Ferme le dialogue"""
        self.progress.stop()
        self.dialog.destroy()

class NeedsDialog:
    """Dialogue pour saisir les paramètres des besoins nutritionnels"""
    
    def __init__(self, parent, config):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Paramètres personnels")
        self.dialog.geometry("300x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Variables
        self.age_var = tk.StringVar(value="30")
        self.gender_var = tk.StringVar(value="M")
        self.activity_var = tk.StringVar(value="modéré")
        
        # Interface
        ttk.Label(self.dialog, text="Âge:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        ttk.Entry(self.dialog, textvariable=self.age_var, width=10).grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(self.dialog, text="Sexe:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        gender_frame = ttk.Frame(self.dialog)
        gender_frame.grid(row=1, column=1, padx=10, pady=5)
        ttk.Radiobutton(gender_frame, text="Homme", variable=self.gender_var, value="M").pack(side='left')
        ttk.Radiobutton(gender_frame, text="Femme", variable=self.gender_var, value="F").pack(side='left')
        
        ttk.Label(self.dialog, text="Activité:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        activity_combo = ttk.Combobox(self.dialog, textvariable=self.activity_var,
                                     values=["sédentaire", "léger", "modéré", "intense", "très intense"],
                                     state='readonly')
        activity_combo.grid(row=2, column=1, padx=10, pady=5)
        
        # Boutons
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(buttons_frame, text="OK", command=self.ok_clicked).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Annuler", command=self.cancel_clicked).pack(side='left', padx=5)
        
        # Centrer
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 150
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
        self.dialog.geometry(f"300x200+{x}+{y}")
        
        self.dialog.wait_window()
    
    def ok_clicked(self):
        """Validation des données"""
        try:
            age = int(self.age_var.get())
            if age < 1 or age > 120:
                raise ValueError("Âge invalide")
            
            self.result = (age, self.gender_var.get(), self.activity_var.get())
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez saisir un âge valide")
    
    def cancel_clicked(self):
        """Annulation"""
        self.dialog.destroy()