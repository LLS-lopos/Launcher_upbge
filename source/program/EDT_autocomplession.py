from PySide6.QtWidgets import QCompleter
from PySide6.QtCore import QStringListModel, Qt
import re
import keyword

class AutoCompleter:
    def __init__(self, text_edit):
        self.text_edit = text_edit
        self.completer = QCompleter(self.text_edit)
        
        # Comprehensive list of Python keywords and built-in functions
        self.keywords = list(keyword.kwlist)
        self.builtin_functions = [
            'print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter', 
            'str', 'int', 'float', 'list', 'dict', 'set', 'tuple', 
            'open', 'input', 'abs', 'max', 'min', 'sum', 'sorted'
        ]
        
        # Dynamic word collection
        self.dynamic_words = set()
        
        # Modèle de données pour le completer
        self.model = QStringListModel()
        self.completer.setModel(self.model)
        
        # Configurer le completer
        self.completer.setWidget(self.text_edit)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)

        # Connecter le signal de texte modifié pour mettre à jour les suggestions
        self.text_edit.textChanged.connect(self.update_completer)

    def extract_words_from_document(self):
        """Extraire dynamiquement les mots du document."""
        text = self.text_edit.toPlainText()
        # Extraire les variables et noms de fonctions/classes
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)
        self.dynamic_words = set(words)

    def update_completer(self):
        # Mettre à jour les mots dynamiques
        self.extract_words_from_document()
        
        # Obtenir le texte actuel et la position du curseur
        current_text = self.text_edit.toPlainText()
        cursor = self.text_edit.textCursor()
        cursor_position = cursor.position()
        
        # Trouver le début du mot actuel
        start = max(current_text.rfind(' ', 0, cursor_position), 
                    current_text.rfind('\n', 0, cursor_position)) + 1
        word = current_text[start:cursor_position].strip()
        
        # Combiner et filtrer les suggestions
        all_words = set(self.keywords + self.builtin_functions + list(self.dynamic_words))
        filtered_words = [
            w for w in all_words 
            if w.startswith(word) and w != word
        ]
        
        # Trier les suggestions (mots plus courts/communs en premier)
        filtered_words.sort(key=lambda x: (len(x), x))
        
        # Limiter le nombre de suggestions
        filtered_words = filtered_words[:20]
        
        # Mettre à jour le modèle
        self.model.setStringList(filtered_words)
        
        # Afficher le completer si des suggestions sont disponibles
        if filtered_words:
            self.completer.complete()

    def add_custom_words(self, words):
        """Permettre l'ajout de mots personnalisés."""
        if isinstance(words, str):
            words = [words]
        self.dynamic_words.update(words)
