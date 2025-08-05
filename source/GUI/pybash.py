import os
import platform
import re
import time
import traceback
import subprocess
import shlex
import signal
from datetime import datetime
from PySide6.QtCore import QTimer, Signal, Qt, QProcess
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont, QKeyEvent, QTextFormat, QTextCharFormat, QTextDocument
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLineEdit, QApplication, QHBoxLayout, 
                             QLabel, QPushButton, QScrollBar, QStyle, QSizePolicy, QMessageBox)
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont, QIcon

# Configuration du logging
def setup_logging():
    """Configure le système de journalisation"""
    log_dir = "/tmp/launcher_upbge"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"terminal_{int(time.time())}.log")
    
    def log_message(message, error=False):
        """Écrit un message dans le fichier de log"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            level = "ERROR" if error else "INFO"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] [{level}] {message}\n")
        except Exception as e:
            print(f"Erreur lors de l'écriture dans le fichier de log: {e}")
    
    return log_message

# Initialisation du logger
log = setup_logging()

class Terminal(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialisation des formats en premier
        self._init_formats()
        
        # Configuration du widget
        self.setReadOnly(False)  # Permettre l'édition
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setAcceptRichText(False)
        self.setFont(QFont("Monospace", 10))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #f8f8f2;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        
        # Initialisation des variables d'instance
        self.history = []
        self.history_index = -1
        self._prompt_text = f"{os.getcwd()}$ "
        
        # Configuration supplémentaire du widget
        self.setUndoRedoEnabled(False)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.setFont(QFont("Courier New", 10))
        
        # Affiche le prompt initial
        cursor = self.textCursor()
        cursor.insertText(self._prompt_text, self._prompt_format)
        self.setTextCursor(cursor)
        
    def _init_formats(self):
        """Initialise les différents formats de texte"""
        # Format pour le prompt (en bleu)
        self._prompt_format = QTextCharFormat()
        self._prompt_format.setForeground(QColor("#4b9bff"))  # Couleur bleue
        
        # Format pour la sortie (en blanc)
        self._output_format = QTextCharFormat()
        self._output_format.setForeground(QColor("#ffffff"))  # Couleur blanche
        
        # Format pour les erreurs
        self._error_format = QTextCharFormat()
        self._error_format.setForeground(QColor("#ff0000"))  # Couleur rouge claire
        
        # Format pour la commande en cours
        self._cmd_format = QTextCharFormat()
        self._cmd_format.setForeground(QColor("#00ffe0"))  # Bleu
        
        # Format pour le séparateur
        self._separator_format = QTextCharFormat()
        self._separator_format.setForeground(QColor("#888888"))  # Gris clair
        self._separator_format.setFontItalic(True)
        
    def prompt_format(self):
        """Retourne le format à utiliser pour le prompt"""
        return self._prompt_format
        
    def output_format(self):
        """Retourne le format à utiliser pour la sortie standard"""
        return self._output_format
        
    def error_format(self):
        """Retourne le format à utiliser pour les erreurs"""
        return self._error_format
        
    def cmd_format(self):
        """Retourne le format à utiliser pour les commandes"""
        return self._cmd_format
        
    def keyPressEvent(self, event):
        """Gère les appuis de touches dans le terminal"""
        # Gestion de la touche Tab pour l'auto-complétion
        if event.key() == Qt.Key_Tab:
            self.handle_tab_completion()
            return
            
        # Gestion des touches spéciales
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.execute_command()
            return
        elif event.key() == Qt.Key_Backspace:
            if self.textCursor().positionInBlock() > len(self._prompt_text):
                super().keyPressEvent(event)
        elif event.key() == Qt.Key_Left:
            if self.textCursor().positionInBlock() > len(self._prompt_text):
                super().keyPressEvent(event)
        elif event.key() == Qt.Key_Right:
            super().keyPressEvent(event)
        elif event.key() == Qt.Key_Up:
            self.navigate_history(-1)
        elif event.key() == Qt.Key_Down:
            self.navigate_history(1)
        elif event.key() == Qt.Key_Home:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, len(self._prompt_text))
            self.setTextCursor(cursor)
        # Gestion des caractères normaux
        elif event.text() and event.text().isprintable():
            super().keyPressEvent(event)
            
    def navigate_history(self, direction):
        """Navigue dans l'historique des commandes"""
        if not self.history:
            return
            
        if direction < 0 and self.history_index > 0:  # Flèche haut
            self.history_index -= 1
        elif direction > 0 and self.history_index < len(self.history) - 1:  # Flèche bas
            self.history_index += 1
            
        # Récupère la commande de l'historique
        cmd = self.history[self.history_index]
        self.replace_command(cmd)
        
    def replace_command(self, cmd):
        """Remplace la commande en cours par celle spécifiée"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(self._prompt_text + cmd, self._cmd_format)
        self.setTextCursor(cursor)
        
    def get_current_command(self):
        """Récupère la commande en cours de frappe"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        line = cursor.selectedText().strip()
        
        # Si la ligne est vide, retourner une chaîne vide
        if not line:
            return ""
            
        # Nettoyage de la ligne pour ne garder que la commande
        # 1. Supprimer le prompt complet s'il est présent
        if self._prompt_text and line.startswith(self._prompt_text):
            line = line[len(self._prompt_text):].strip()
        # 2. Supprimer le format du prompt avec nom d'utilisateur et répertoire
        elif re.match(r'^\[?\w+@[\w-]+\s*:\s*~?[^\]]*\]?\$\s*', line):
            line = re.sub(r'^\[?\w+@[\w-]+\s*:\s*~?[^\]]*\]?\$\s*', '', line)
        # 3. Supprimer le chemin du répertoire courant suivi de $
        elif os.getcwd() + '$' in line:
            line = line.split('$', 1)[1].lstrip()
        # 4. Supprimer un simple $ suivi d'un espace
        elif line.startswith('$'):
            line = line[1:].lstrip()
            
        # Nettoyer les espaces superflus et retourner
        return line.strip()
        
    def get_completion_matches(self, text):
        """Récupère les complétions possibles pour le texte donné"""
        if not text:
            return []
            
        # Vérifie si on complète une commande ou un fichier
        if ' ' in text or text.startswith('cd'):
            # Si la commande commence par 'cd' ou contient un espace, on complète un chemin
            if text.startswith('cd'):
                # Pour 'cd', on ne complète que les répertoires
                if text.strip() == 'cd':
                    # Si juste 'cd', on suggère les dossiers du répertoire courant
                    prefix = 'cd '
                    dirname = '.'
                    basename = ''
                else:
                    # Sinon, on extrait le chemin à compléter
                    parts = text.split(' ', 1)
                    prefix = 'cd ' if len(parts) == 1 else 'cd ' + parts[1].rsplit('/', 1)[0] + '/' if '/' in parts[1] else 'cd '
                    partial = parts[1] if len(parts) > 1 else ''
                    dirname = os.path.dirname(partial) or '.'
                    basename = os.path.basename(partial)
            else:
                # Pour les autres commandes, on complète fichiers et dossiers
                parts = text.rsplit(' ', 1)
                if len(parts) > 1:
                    prefix = parts[0] + ' '
                    partial = parts[-1]
                    dirname = os.path.dirname(partial) or '.'
                    basename = os.path.basename(partial)
                else:
                    # Si pas d'espace, on complète à partir du répertoire courant
                    prefix = ''
                    partial = parts[0] if parts[0] else ''
                    dirname = '.'
                    basename = partial
            
            try:
                # Liste les fichiers/dossiers correspondants
                if not os.path.exists(dirname):
                    return []
                    
                files = os.listdir(dirname)
                
                # Pour 'cd', on ne garde que les dossiers
                if text.startswith('cd'):
                    matches = [f + '/' for f in files if f.startswith(basename) 
                             and os.path.isdir(os.path.join(dirname, f))]
                else:
                    # Pour les autres commandes, on garde tout
                    matches = [f + '/' if os.path.isdir(os.path.join(dirname, f)) else f 
                              for f in files if f.startswith(basename)]
                
                # Ajoute le chemin complet si nécessaire
                if dirname != '.':
                    base_path = dirname + '/' if not dirname.endswith('/') else dirname
                    matches = [base_path + f for f in matches]
                
                # Nettoie les chemins (supprime les doubles //)
                matches = [m.replace('//', '/') for m in matches]
                
                # Ajoute le préfixe de la commande
                if text.startswith('cd'):
                    # Pour 'cd', on gère différemment selon si c'est un chemin absolu ou relatif
                    if not partial.startswith('/') and not partial.startswith('~'):
                        # Chemin relatif
                        matches = [prefix + m for m in matches]
                    else:
                        # Chemin absolu ou ~
                        matches = ['cd ' + m for m in matches]
                else:
                    # Pour les autres commandes
                    matches = [prefix + m for m in matches]
                
                return sorted(matches)
                
            except Exception as e:
                log(f"Erreur lors de la complétion: {str(e)}", error=True)
                return []
        else:
            # Complétion de commande (dans le PATH)
            path_dirs = os.environ.get('PATH', '').split(':')
            matches = []
            
            for path_dir in path_dirs:
                try:
                    if os.path.isdir(path_dir):
                        for f in os.listdir(path_dir):
                            if f.startswith(text) and os.access(os.path.join(path_dir, f), os.X_OK):
                                matches.append(f)
                except Exception:
                    continue
                    
            return sorted(list(set(matches)))  # Évite les doublons
    
    def handle_tab_completion(self):
        """Gère l'auto-complétion avec la touche Tab"""
        command = self.get_current_command()
        matches = self.get_completion_matches(command)
        
        if not matches:
            return  # Aucune correspondance
            
        if len(matches) == 1:
            # Une seule correspondance, on complète
            self.complete_command(matches[0])
        else:
            # Plusieurs correspondances, on les affiche
            self.append_output("\n" + "  ".join(matches) + "\n")
            self.append_output(self._prompt_text + command, move_cursor=False)
    
    def complete_command(self, completion):
        """Complète la commande en cours avec le texte donné"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.removeSelectedText()
        self.setTextCursor(cursor)
        self.append_output(self._prompt_text + completion, move_cursor=False)
    
    def get_prompt(self):
        """Retourne le prompt du terminal"""
        return self._prompt_text
        
    def update_prompt(self):
        """Met à jour le texte du prompt"""
        self._prompt_text = f"{os.getcwd()}$ "
        
    def execute_command(self):
        """Exécute la commande actuelle"""
        cmd = self.get_current_command()
        if not cmd:
            cursor = self.textCursor()
            cursor.insertText(self._prompt_text, self._prompt_format)
            self.setTextCursor(cursor)
            return
            
        # Ajoute la commande à l'historique
        self.history.append(cmd)
        self.history_index = len(self.history)
        
        # Émet le signal avec la commande
        self.parent().command_entered.emit(cmd)
        
    def complete_command(self, completion):
        """Complète la commande en cours avec le texte donné"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.removeSelectedText()
        self.setTextCursor(cursor)
        self.append_output(self._prompt_text + completion, move_cursor=False)
        
    def get_prompt(self):
        """Retourne le prompt du terminal"""
        return self._prompt_text
        
    def update_prompt(self):
        """Met à jour le texte du prompt"""
        self._prompt_text = f"{os.getcwd()}$ "
        
    def execute_command(self):
        """Exécute la commande actuelle"""
        cmd = self.get_current_command()
        if not cmd:
            cursor = self.textCursor()
            cursor.insertText(self._prompt_text, self._prompt_format)
            self.setTextCursor(cursor)
            return
            
        # Ajoute la commande à l'historique
        self.history.append(cmd)
        self.history_index = len(self.history)
        
        # Émet le signal avec la commande
        self.parent().command_entered.emit(cmd)
        
        # Passe à la ligne suivante et affiche un nouveau prompt
        self.append_output(self._prompt_text, is_prompt=True)

    def append_output(self, text, error=False, move_cursor=True, is_prompt=False, is_separator=False, is_command=False):
        """Ajoute la sortie de la commande
        
        Args:
            text: Le texte à afficher
            error: Si True, le texte est affiché comme une erreur
            move_cursor: Si True, déplace le curseur à la fin du texte
            is_prompt: Si True, utilise le format de prompt
            is_separator: Si True, utilise le format de séparateur
            is_command: Si True, utilise le format de commande
        """
        if not text and not is_separator:  # Ne rien faire si le texte est vide et ce n'est pas un séparateur
            return
            
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Appliquer le format approprié
        if is_prompt:
            format_ = self._prompt_format
        elif is_separator:
            format_ = self._separator_format
            text = "─" * 80 + "\n"  # Ligne de séparation
        elif is_command:
            format_ = self._cmd_format
        elif error:
            format_ = self._error_format
        else:
            format_ = self._output_format
            
        # Insérer le texte avec le format
        cursor.insertText(text, format_)
        
        # Ne plus ajouter automatiquement de séparateur ici
        # La gestion des séparateurs est maintenant faite uniquement via _add_separator()
        
        # Déplacer le curseur à la fin si demandé
        if move_cursor:
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)

class PyBash(QWidget):
    # Signal émis lorsqu'une commande est entrée
    command_entered = Signal(str)
    
    def __init__(self, parent=None, start_dir=None):
        super().__init__(parent)
        log(f"Initialisation de PyBash avec le répertoire: {start_dir}")
        self.process = None
        self.terminal = Terminal(self)  # Passer self comme parent
        self.start_dir = start_dir or os.path.expanduser("~")
        self.init_file = None  # Pour stocker le chemin du fichier d'initialisation
        try:
            self.setup_ui()
            self.setup_process()
            self.setMinimumHeight(200)
            self.setMaximumHeight(300)
            log("PyBash initialisé avec succès")
        except Exception as e:
            log(f"Erreur lors de l'initialisation de PyBash: {str(e)}\n{traceback.format_exc()}", error=True)
            raise

    def setup_ui(self):
        """Configure l'interface utilisateur du terminal"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Zone de sortie du terminal (lecture seule)
        self.terminal.setReadOnly(True)
        layout.addWidget(self.terminal, stretch=1)
        
        # Zone de saisie de commande
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Entrez une commande...")
        self.command_input.returnPressed.connect(self.on_command_entered)
        
        # Layout pour la zone de commande et le bouton
        command_layout = QHBoxLayout()
        command_layout.addWidget(self.command_input, stretch=1)
        
        # Bouton pour effacer le terminal
        clear_btn = QPushButton("Effacer")
        clear_btn.clicked.connect(self.terminal.clear)
        command_layout.addWidget(clear_btn)
        
        layout.addLayout(command_layout)
        
        # Connecter le signal de commande
        self.command_entered.connect(self.execute_command)

    def setup_process(self):
        """Configure le processus pour exécuter les commandes"""
        log("Configuration du processus du terminal...")
        self.process = None
        self.process_output = ""
        self.process_error = ""
        self.current_dir = self.start_dir
        
        # Afficher le prompt initial
        self.show_prompt()

    def execute_command(self, cmd):
        """Exécute une commande dans le terminal"""
        if not cmd.strip():
            return
            
        # Nettoyer la commande
        cmd = self.clean_command(cmd)
        log(f"Exécution de la commande: {cmd}")
        
        try:
            # Gestion spéciale pour la commande cd
            if cmd.startswith('cd '):
                new_dir = cmd[3:].strip()
                self._change_directory(new_dir)
                return
                
            # Exécuter la commande avec subprocess
            process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=self.current_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                executable='/bin/bash'
            )
            
            # Lire la sortie complète
            stdout, stderr = process.communicate()
            
            # Afficher la sortie standard
            if stdout.strip():
                self.terminal.append_output(stdout, error=False)
                
            # Afficher les erreurs
            if stderr.strip():
                self.terminal.append_output(stderr, error=True)
            
        except Exception as e:
            error_msg = f"Erreur lors de l'exécution de la commande: {str(e)}"
            log(error_msg, error=True)
            self.terminal.append_output(f"{error_msg}\n", error=True)
            
    def _change_directory(self, new_dir):
        """Change le répertoire de travail"""
        try:
            if not new_dir:
                new_dir = os.path.expanduser('~')
                
            # Gestion du ~ pour le répertoire utilisateur
            if new_dir.startswith('~'):
                new_dir = os.path.expanduser(new_dir)
                
            # Résoudre le chemin
            new_dir = os.path.abspath(os.path.join(self.current_dir, new_dir))
            
            # Vérifier si le répertoire existe
            if os.path.isdir(new_dir):
                self.current_dir = new_dir
            else:
                error_msg = f"cd: {new_dir}: Aucun fichier ou dossier de ce type"
                self.terminal.append_output(f"{error_msg}\n", error=True)
                
        except Exception as e:
            error_msg = f"Erreur lors du changement de répertoire: {str(e)}"
            log(error_msg, error=True)
            self.terminal.append_output(f"{error_msg}\n", error=True)

    def clean_command(self, cmd):
        """Nettoie la commande en supprimant le prompt si présent"""
        if not cmd:
            return ""
            
        # Supprimer le prompt si présent
        if self.terminal._prompt_text and cmd.startswith(self.terminal._prompt_text):
            cmd = cmd[len(self.terminal._prompt_text):].strip()
            
        # Supprimer un simple $ suivi d'un espace
        if cmd.startswith('$ '):
            cmd = cmd[2:].lstrip()
            
        return cmd.strip()
        
    def _add_separator(self):
        """Ajoute un séparateur visuel après une commande"""
        if not hasattr(self, '_last_command_was_separator'):
            self._last_command_was_separator = False
            
        # Ne pas ajouter de séparateur si la dernière commande était déjà un séparateur
        if not self._last_command_was_separator:
            cursor = self.terminal.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText("\n" + "─" * 80 + "\n", self.terminal._separator_format)
            self.terminal.setTextCursor(cursor)
            self._last_command_was_separator = True
        
    def show_prompt(self):
        """Affiche le prompt avec le répertoire courant"""
        # Obtenir le nom du répertoire courant
        cwd = os.path.basename(self.current_dir) if self.current_dir != os.path.expanduser('~') else '~'
        
        # Créer le texte du prompt
        prompt_text = f"{os.getenv('USER', 'user')}@{os.uname().nodename.split('.')[0]}:{cwd}$ "
        
        # Afficher le prompt
        self.terminal.append_output(prompt_text, is_prompt=True)
        
    def on_command_entered(self):
        """Appelé quand une commande est entrée dans le champ de saisie"""
        cmd = self.command_input.text().strip()
        if not cmd:
            return
            
        try:
            # Effacer le champ de saisie
            self.command_input.clear()
            
            # Afficher le prompt et la commande
            self.show_prompt()
            self.terminal.append_output(f"{cmd}\n", is_command=True)
            
            # Réinitialiser l'état du séparateur avant d'exécuter la commande
            if hasattr(self, '_last_command_was_separator'):
                self._last_command_was_separator = False
            
            # Exécuter la commande
            self.execute_command(cmd)
            
            # Afficher un séparateur après la commande
            self._add_separator()
            
        except Exception as e:
            # En cas d'erreur, afficher l'erreur
            error_msg = f"Erreur: {str(e)}"
            self.terminal.append_output(f"{error_msg}\n", error=True)
            log(error_msg, error=True)
            
            # Ajouter un séparateur même en cas d'erreur
            self._add_separator()
            
        finally:
            # Toujours afficher le prompt après l'exécution
            self.show_prompt()
            
    def closeEvent(self, event):
        """Gère l'événement de fermeture de la fenêtre"""
        self.cleanup()
        event.accept()
        
    def cleanup(self):
        """Nettoie les ressources du terminal"""
        log("Nettoyage des ressources du terminal...")
        if hasattr(self, 'process') and self.process:
            log(f"État du processus avant nettoyage: {self.process.state()}")
            if self.process.state() == QProcess.Running:
                log("Envoi de la commande exit au shell...")
                try:
                    self.process.write(b'exit\n')
                    if not self.process.waitForFinished(1000):
                        log("Le processus ne s'est pas arrêté, tentative de terminaison...")
                        self.process.terminate()
                        if not self.process.waitForFinished(1000):
                            log("Le processus ne répond pas, tentative de kill...")
                            self.process.kill()
                except Exception as e:
                    log(f"Erreur lors de l'arrêt du processus: {str(e)}\n{traceback.format_exc()}", error=True)
            self.process = None
            log("Processus nettoyé")
            
        # Nettoyer le fichier d'initialisation s'il existe
        if hasattr(self, 'init_file') and self.init_file:
            try:
                if os.path.exists(self.init_file):
                    log(f"Suppression du fichier temporaire: {self.init_file}")
                    os.unlink(self.init_file)
                else:
                    log(f"Le fichier temporaire n'existe plus: {self.init_file}")
            except Exception as e:
                error_msg = f"Erreur lors de la suppression du fichier temporaire: {str(e)}"
                log(error_msg, error=True)
                print(error_msg)
            self.init_file = None
            
        log("Nettoyage des ressources terminé")

# Pour tester le terminal seul
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = PyBash()
    window.setWindowTitle("Terminal Intégré")
    window.resize(800, 500)
    window.show()
    sys.exit(app.exec())