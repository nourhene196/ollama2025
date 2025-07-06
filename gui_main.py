"""
Interface graphique principale
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Dict, Any
import threading
import queue
from config import Config
from models import DataManager
from ollama_client import OllamaClient
from recipe_service import RecipeService
from calorie_service import CalorieService
from gui_components import (
    IngredientsSelector, RecipeDisplay, CalorieCalculator, 
    StatusBar, LoadingDialog
)

class MainApplication:
    """Application principale"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.config = Config()
        self.setup_window()
        
        # Initialiser les services
        self.data_manager = None
        self.ollama_client = None
        self.recipe_service = None
        self.calorie_service = None
        
        # Queue pour les tâches asynchrones
        self.task_queue = queue.Queue()
        
        # Variables d'état
        self.selected_ingredients = []
        self.current_recipe = None
        self.current_analysis = None
        
        # Créer l'interface
        self.create_interface()
        
        # Initialiser les services en arrière-plan
        self.initialize_services()
    
    def setup_window(self):
        """Configure la fenêtre principale"""
        self.root.title(self.config.APP_TITLE)
        self.root.geometry(self.config.APP_GEOMETRY)
        self.root.configure(bg=self.config.COLORS['background'])
        
        # Centrer la fenêtre
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Configurer les styles
        self.setup_styles()
    
    def setup_styles(self):
        """Configure les styles ttk"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Style pour les boutons
        style.configure('Primary.TButton',
                       background=self.config.COLORS['primary'],
                       foreground='white',
                       font=self.config.FONTS['default'])
        
        style.configure('Success.TButton',
                       background=self.config.COLORS['success'],
                       foreground='white',
                       font=self.config.FONTS['default'])
        
        # Style pour les frames
        style.configure('Card.TFrame',
                       background='white',
                       relief='solid',
                       borderwidth=1)
    
    def create_interface(self):
        """Crée l'interface utilisateur"""
        # Menu principal
        self.create_menu()
        
        # Barre d'outils
        self.create_toolbar()
        
        # Zone principale avec onglets
        self.create_main_tabs()
        
        # Barre de statut
        self.status_bar = StatusBar(self.root, self.config)
        self.status_bar.pack(side='bottom', fill='x')
        
        # Configurer la grille
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
    
    def create_menu(self):
        """Crée le menu principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau", command=self.new_session)
        file_menu.add_command(label="Exporter recette", command=self.export_recipe)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        
        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="Tester Ollama", command=self.test_ollama)
        tools_menu.add_command(label="Recharger données", command=self.reload_data)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self.show_about)
    
    def create_toolbar(self):
        """Crée la barre d'outils"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side='top', fill='x', padx=5, pady=5)
        
        # Titre
        title_label = ttk.Label(toolbar, text=self.config.APP_TITLE, 
                               font=self.config.FONTS['title'])
        title_label.pack(side='left')
        
        # Boutons rapides
        ttk.Button(toolbar, text="Nouvelle session", 
                  command=self.new_session).pack(side='right', padx=5)
        
        ttk.Button(toolbar, text="Exporter", 
                  command=self.export_recipe).pack(side='right', padx=5)
    
    def create_main_tabs(self):
        """Crée les onglets principaux"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Onglet Générateur de recettes
        self.recipe_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.recipe_frame, text="Générateur de recettes")
        self.create_recipe_tab()
        
        # Onglet Calculateur de calories
        self.calorie_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.calorie_frame, text="Calculateur de calories")
        self.create_calorie_tab()
        
        # Onglet Historique
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text="Historique")
        self.create_history_tab()
    
    def create_recipe_tab(self):
        """Crée l'onglet générateur de recettes"""
        # Configuration en colonnes
        self.recipe_frame.grid_columnconfigure(0, weight=1)
        self.recipe_frame.grid_columnconfigure(1, weight=2)
        self.recipe_frame.grid_rowconfigure(0, weight=1)
        
        # Panneau de sélection d'ingrédients
        ingredients_frame = ttk.LabelFrame(self.recipe_frame, 
                                          text="Sélection d'ingrédients")
        ingredients_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        self.ingredients_selector = IngredientsSelector(
            ingredients_frame, self.config, self.on_ingredients_changed
        )
        
        # Panneau de génération et affichage
        recipe_panel = ttk.Frame(self.recipe_frame)
        recipe_panel.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        
        # Options de génération
        options_frame = ttk.LabelFrame(recipe_panel, text="Options de génération")
        options_frame.pack(fill='x', pady=5)
        
        # Cuisine
        ttk.Label(options_frame, text="Type de cuisine:").grid(row=0, column=0, sticky='w')
        self.cuisine_var = tk.StringVar()
        cuisine_combo = ttk.Combobox(options_frame, textvariable=self.cuisine_var,
                                   values=["", "Française", "Italienne", "Asiatique", "Méditerranéenne"])
        cuisine_combo.grid(row=0, column=1, sticky='w', padx=5)
        
        # Difficulté
        ttk.Label(options_frame, text="Difficulté:").grid(row=1, column=0, sticky='w')
        self.difficulty_var = tk.StringVar()
        difficulty_combo = ttk.Combobox(options_frame, textvariable=self.difficulty_var,
                                      values=["", "Facile", "Moyen", "Difficile"])
        difficulty_combo.grid(row=1, column=1, sticky='w', padx=5)
        
        # Temps
        ttk.Label(options_frame, text="Temps max:").grid(row=2, column=0, sticky='w')
        self.time_var = tk.StringVar()
        time_combo = ttk.Combobox(options_frame, textvariable=self.time_var,
                                values=["", "15 min", "30 min", "1 heure", "2 heures"])
        time_combo.grid(row=2, column=1, sticky='w', padx=5)
        
        # Bouton de génération
        generate_btn = ttk.Button(options_frame, text="Générer la recette",
                                 style='Primary.TButton',
                                 command=self.generate_recipe)
        generate_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Affichage de la recette
        self.recipe_display = RecipeDisplay(recipe_panel, self.config)
        self.recipe_display.pack(fill='both', expand=True, pady=5)
    
    def create_calorie_tab(self):
        """Crée l'onglet calculateur de calories"""
        self.calorie_calculator = CalorieCalculator(self.calorie_frame, self.config)
        self.calorie_calculator.pack(fill='both', expand=True)
    
    def create_history_tab(self):
        """Crée l'onglet historique"""
        # Liste des recettes générées
        history_label = ttk.Label(self.history_frame, text="Historique des recettes",
                                 font=self.config.FONTS['heading'])
        history_label.pack(pady=10)
        
        # Treeview pour l'historique
        columns = ('Date', 'Nom', 'Ingrédients', 'Calories')
        self.history_tree = ttk.Treeview(self.history_frame, columns=columns, show='headings')
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.history_frame, orient='vertical', 
                                 command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetage
        self.history_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Boutons d'action
        history_buttons = ttk.Frame(self.history_frame)
        history_buttons.pack(side='bottom', fill='x', pady=5)
        
        ttk.Button(history_buttons, text="Recharger",
                  command=self.reload_history).pack(side='left', padx=5)
        
        ttk.Button(history_buttons, text="Supprimer",
                  command=self.delete_history_item).pack(side='left', padx=5)
    
    def initialize_services(self):
        """Initialise les services en arrière-plan"""
        def init_thread():
            try:
                self.status_bar.set_status("Initialisation des services...")
                
                # Initialiser le gestionnaire de données
                self.data_manager = DataManager(self.config)
                
                # Initialiser le client Ollama
                self.ollama_client = OllamaClient(self.config)
                
                # Initialiser les services
                self.recipe_service = RecipeService(self.data_manager, self.ollama_client)
                self.calorie_service = CalorieService(self.data_manager)
                
                # Mettre à jour l'interface
                self.root.after(0, self.on_services_initialized)
                
            except Exception as e:
                self.root.after(0, lambda: self.on_initialization_error(str(e)))
        
        thread = threading.Thread(target=init_thread, daemon=True)
        thread.start()
    
    def on_services_initialized(self):
        """Appelé quand les services sont initialisés"""
        self.status_bar.set_status("Services initialisés")
        
        # Charger les ingrédients dans le sélecteur
        if self.data_manager:
            ingredients = self.data_manager.get_all_ingredients()
            self.ingredients_selector.load_ingredients(ingredients)
            
            # Initialiser le calculateur de calories
            self.calorie_calculator.set_data_manager(self.data_manager)
            self.calorie_calculator.set_calorie_service(self.calorie_service)
        
        # Tester Ollama
        self.test_ollama_connection()
    
    def on_initialization_error(self, error_message):
        """Appelé en cas d'erreur d'initialisation"""
        self.status_bar.set_status(f"Erreur: {error_message}")
        messagebox.showerror("Erreur d'initialisation", error_message)
    
    def test_ollama_connection(self):
        """Teste la connexion à Ollama"""
        if not self.ollama_client:
            return
        
        if self.ollama_client.is_available():
            if self.ollama_client.is_model_available():
                self.status_bar.set_status("Ollama et TinyLlama disponibles")
            else:
                self.status_bar.set_status("Ollama disponible, TinyLlama manquant")
        else:
            self.status_bar.set_status("Ollama non disponible - mode hors ligne")
    
    def on_ingredients_changed(self, selected_ingredients):
        """Appelé quand la sélection d'ingrédients change"""
        self.selected_ingredients = selected_ingredients
        self.status_bar.set_status(f"{len(selected_ingredients)} ingrédient(s) sélectionné(s)")
    
    def generate_recipe(self):
        """Génère une recette avec les ingrédients sélectionnés"""
        if not self.selected_ingredients:
            messagebox.showwarning("Aucun ingrédient", 
                                 self.config.MESSAGES['no_ingredients'])
            return
        
        if not self.recipe_service:
            messagebox.showerror("Erreur", "Services non initialisés")
            return
        
        # Afficher un dialogue de chargement
        loading = LoadingDialog(self.root, "Génération de la recette en cours...")
        
        def generate_thread():
            try:
                recipe = self.recipe_service.generate_recipe(
                    self.selected_ingredients,
                    self.cuisine_var.get(),
                    self.difficulty_var.get(),
                    self.time_var.get()
                )
                
                self.root.after(0, lambda: self.on_recipe_generated(recipe, loading))
                
            except Exception as e:
                self.root.after(0, lambda: self.on_recipe_error(str(e), loading))
        
        thread = threading.Thread(target=generate_thread, daemon=True)
        thread.start()
    
    def on_recipe_generated(self, recipe, loading_dialog):
        """Appelé quand une recette est générée"""
        loading_dialog.destroy()
        
        if recipe:
            self.current_recipe = recipe
            self.recipe_display.display_recipe(recipe)
            self.status_bar.set_status(self.config.MESSAGES['success_recipe'])
            
            # Ajouter à l'historique
            self.add_to_history(recipe)
        else:
            messagebox.showerror("Erreur", "Impossible de générer la recette")
    
    def on_recipe_error(self, error_message, loading_dialog):
        """Appelé en cas d'erreur lors de la génération"""
        loading_dialog.destroy()
        messagebox.showerror("Erreur", f"Erreur lors de la génération: {error_message}")
        self.status_bar.set_status("Erreur de génération")
    
    def new_session(self):
        """Démarre une nouvelle session"""
        # Réinitialiser les sélections
        self.selected_ingredients = []
        self.current_recipe = None
        self.current_analysis = None
        
        # Vider les affichages
        self.ingredients_selector.clear_selection()
        self.recipe_display.clear()
        self.calorie_calculator.clear()
        
        # Réinitialiser les variables
        self.cuisine_var.set("")
        self.difficulty_var.set("")
        self.time_var.set("")
        
        self.status_bar.set_status("Nouvelle session")
    
    def export_recipe(self):
        """Exporte la recette actuelle"""
        if not self.current_recipe:
            messagebox.showwarning("Aucune recette", "Aucune recette à exporter")
            return
        
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.format_recipe_for_export(self.current_recipe))
                
                messagebox.showinfo("Export réussi", f"Recette exportée vers {filename}")
                
            except Exception as e:
                messagebox.showerror("Erreur d'export", f"Erreur: {e}")
    
    def format_recipe_for_export(self, recipe):
        """Formate une recette pour l'export"""
        lines = []
        lines.append(f"RECETTE: {recipe.title}")
        lines.append("=" * 50)
        lines.append("")
        
        lines.append("INGRÉDIENTS:")
        for ingredient in recipe.ingredients:
            lines.append(f"- {ingredient['name']}: {ingredient['quantity']} {ingredient['unit']}")
        lines.append("")
        
        lines.append("PRÉPARATION:")
        for i, step in enumerate(recipe.steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")
        
        lines.append(f"TEMPS DE PRÉPARATION: {recipe.prep_time}")
        lines.append(f"DIFFICULTÉ: {recipe.difficulty}")
        lines.append(f"CALORIES TOTALES: {recipe.total_calories:.1f} kcal")
        lines.append("")
        
        lines.append("Généré par Assistant Culinaire & Calories")
        
        return "\n".join(lines)
    
    def test_ollama(self):
        """Test manuel de la connexion Ollama"""
        if not self.ollama_client:
            messagebox.showerror("Erreur", "Client Ollama non initialisé")
            return
        
        def test_thread():
            try:
                available = self.ollama_client.is_available()
                model_available = self.ollama_client.is_model_available()
                
                self.root.after(0, lambda: self.show_ollama_status(available, model_available))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erreur", f"Erreur de test: {e}"))
        
        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()
    
    def show_ollama_status(self, available, model_available):
        """Affiche le statut d'Ollama"""
        status_lines = []
        status_lines.append(f"Ollama disponible: {'✓' if available else '✗'}")
        status_lines.append(f"TinyLlama disponible: {'✓' if model_available else '✗'}")
        
        if available and not model_available:
            status_lines.append("\nPour installer TinyLlama:")
            status_lines.append("ollama pull tinyllama")
        
        if not available:
            status_lines.append("\nPour démarrer Ollama:")
            status_lines.append("ollama serve")
        
        messagebox.showinfo("Statut Ollama", "\n".join(status_lines))
    
    def reload_data(self):
        """Recharge les données nutritionnelles"""
        if self.data_manager:
            self.data_manager.load_data()
            
            # Recharger dans l'interface
            ingredients = self.data_manager.get_all_ingredients()
            self.ingredients_selector.load_ingredients(ingredients)
            
            messagebox.showinfo("Rechargement", "Données rechargées avec succès")
            self.status_bar.set_status("Données rechargées")
    
    def add_to_history(self, recipe):
        """Ajoute une recette à l'historique"""
        from datetime import datetime
        
        # Formatage pour l'affichage
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        ingredients_str = ", ".join([ing['name'] for ing in recipe.ingredients[:3]])
        if len(recipe.ingredients) > 3:
            ingredients_str += "..."
        
        # Ajouter à la TreeView
        self.history_tree.insert('', 'end', values=(
            date_str,
            recipe.title,
            ingredients_str,
            f"{recipe.total_calories:.0f} kcal"
        ))
    
    def reload_history(self):
        """Recharge l'historique"""
        # Vider la TreeView
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        self.status_bar.set_status("Historique rechargé")
    
    def delete_history_item(self):
        """Supprime un élément de l'historique"""
        selected = self.history_tree.selection()
        if selected:
            for item in selected:
                self.history_tree.delete(item)
            self.status_bar.set_status("Élément supprimé")
    
    def show_about(self):
        """Affiche la boîte de dialogue À propos"""
        about_text = f"""
{self.config.APP_TITLE}
Version {self.config.APP_VERSION}

Application de génération de recettes et calcul de calories
utilisant TinyLlama via Ollama.

Fonctionnalités:
• Génération de recettes à partir d'ingrédients
• Calcul détaillé des calories et nutriments
• Interface intuitive et moderne
• Fonctionnement hors ligne

Développé avec Python et tkinter
        """
        
        messagebox.showinfo("À propos", about_text.strip())
    
    def run(self):
        """Lance l'application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()

def main():
    """Point d'entrée principal"""
    try:
        # Vérifier la configuration
        Config.ensure_data_dir()
        
        # Lancer l'application
        app = MainApplication()
        app.run()
        
    except Exception as e:
        messagebox.showerror("Erreur fatale", f"Impossible de démarrer l'application: {e}")

if __name__ == "__main__":
    main()