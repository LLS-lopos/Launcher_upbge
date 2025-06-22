import sys
import os

# Add the source directory to Python path
source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, source_dir)

from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton, QFileDialog, QHBoxLayout
from PySide6.QtGui import QGuiApplication
from program.EDT_syntaxe import SyntaxHighlighter
from program.EDT_autocomplession import AutoCompleter

class LoposEditor(QMainWindow):
    @classmethod
    def ouvrir_fichier(cls, fichier):
        """Méthode de classe pour ouvrir un fichier dans un nouvel éditeur"""
        editor = cls(fichier=fichier)
        editor.show()
        return editor

    def __init__(self, titre="LPS éditeur", fichier=None, m_largeur=0, m_hauteur=0, largeur=700, hauteur=600):
        super().__init__()
        self.titre = titre
        self.largeur = largeur
        self.hauteur = hauteur
        self.m_largeur = m_largeur 
        self.m_hauteur = m_hauteur 
        self.setWindowTitle(self.titre)

        moniteur = QGuiApplication.primaryScreen()
        taille_moniteur = moniteur.size()
        calcul_l = (taille_moniteur.width()//2) - (self.largeur//2)
        calcul_h = (taille_moniteur.height()//2) - (self.hauteur//2)
        
        self.setGeometry(int(calcul_l), int(calcul_h), self.largeur, self.hauteur)

        # Créer un widget central
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Créer un layout vertical
        self.layout_v = QVBoxLayout(self.central_widget)

        # Créer un layout horizontal pour les boutons
        self.layout_h = QHBoxLayout()
        self.layout_v.addLayout(self.layout_h)

        # Créer un bouton pour ouvrir un fichier texte
        self.open_button = QPushButton("Ouvrir", self)
        self.open_button.clicked.connect(self.open_file)
        self.layout_h.addWidget(self.open_button)

        # Créer un bouton pour sauvegarder le texte
        self.register_button = QPushButton("Enregistrer", self)
        self.register_button.clicked.connect(self.registre_file)
        self.layout_h.addWidget(self.register_button)

        # Créer un bouton pour sauvegarder le texte
        self.save_button = QPushButton("Sauvegarder", self)
        self.save_button.clicked.connect(self.save_file)
        self.layout_h.addWidget(self.save_button)

        # Créer un QTextEdit
        self.text_edit = QTextEdit(self)
        self.layout_v.addWidget(self.text_edit)

        # Initialiser le SyntaxHighlighter
        self.highlighter = SyntaxHighlighter(self.text_edit.document())

        # Initialiser l'AutoCompleter
        self.auto_completer = AutoCompleter(self.text_edit)

        # Si un fichier est spécifié, le charger
        if fichier is not None:
            try:
                with open(fichier, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_edit.setPlainText(content)
                    self.current_file = fichier
            except Exception as e:
                print(f"Erreur lors du chargement du fichier {fichier}: {e}")
                self.current_file = None
        else:
            self.current_file = None

    def save_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Sauvegarder le fichier", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            self.current_file = file_name  # Mettre à jour le nom de fichier actuel
            with open(file_name, 'w') as file:
                file.write(self.text_edit.toPlainText())

    def open_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Ouvrir le fichier", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            self.current_file = file_name  # Mettre à jour le nom de fichier actuel
            with open(file_name, 'r') as file:
                self.text_edit.setPlainText(file.read())
    
    def registre_file(self):
        if self.current_file:  # Vérifier si un fichier a été ouvert ou enregistré
            with open(self.current_file, 'w') as file:
                file.write(self.text_edit.toPlainText())
        else:
            self.save_file()  # Si aucun fichier n'est ouvert, demander à l'utilisateur de sauvegarder

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = LoposEditor()
    editor.show()
    sys.exit(app.exec())
