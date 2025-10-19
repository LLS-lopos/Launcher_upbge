import os
import platform
import re
import time
import traceback
from datetime import datetime
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt, QProcess, QProcessEnvironment, Signal, QTimer, QEvent
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from PySide6.QtWidgets import (QTextEdit, QVBoxLayout, QWidget, QLineEdit, 
                             QHBoxLayout, QPushButton, QApplication, QInputDialog)

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
        self.setFont(QFont("Monospace", 12))
        
        # Initialisation des variables d'instance
        self.history = []
        self.history_index = -1
        self._prompt_text = f"{os.getcwd()}$ "
        
        # Configuration supplémentaire du widget
        self.setUndoRedoEnabled(False)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.setFont(QFont("Courier New", 12))
        
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
            
        # Sauvegarde la commande en cours si on commence à naviguer dans l'historique
        if not hasattr(self, '_current_unsaved_command') or self.history_index == len(self.history):
            self._current_unsaved_command = self.get_current_command()
            
        # Navigation dans l'historique
        if direction < 0:  # Flèche haut
            if self.history_index > 0:
                self.history_index -= 1
            elif self.history_index == -1 and self.history:
                self.history_index = len(self.history) - 1
            
            # Affiche la commande de l'historique
            if 0 <= self.history_index < len(self.history):
                cmd = self.history[self.history_index]
                self.replace_command(cmd)
                
        elif direction > 0:  # Flèche bas
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                # Affiche la commande suivante dans l'historique
                cmd = self.history[self.history_index]
                self.replace_command(cmd)
            else:
                # Si on est à la fin de l'historique, on restaure la commande non enregistrée
                if hasattr(self, '_current_unsaved_command'):
                    self.history_index = len(self.history)
                    self.replace_command(self._current_unsaved_command)
                else:
                    self.history_index = len(self.history)
                    self.replace_command('')
        
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
        if ' ' in text or text.startswith(('cd', './', '/', '~', '../')):
            # Si la commande commence par 'cd' ou contient un espace, on complète un chemin
            if text.startswith('cd'):
                # Pour 'cd', on ne complète que les répertoires
                if text.strip() == 'cd':
                    prefix = 'cd '
                    dirname = '.'
                    basename = ''
                else:
                    # Extraction du chemin à compléter
                    parts = text.split(' ', 1)
                    if len(parts) > 1:
                        path = parts[1].strip()
                        if not path:  # Cas 'cd ' (espace après cd)
                            dirname = '.'
                            basename = ''
                            prefix = 'cd '
                        else:
                            # Gestion du ~ pour le home
                            if path.startswith('~'):
                                path = os.path.expanduser(path)
                            # Détermination du répertoire de base et du préfixe
                            dirname = os.path.dirname(path) or '.'
                            basename = os.path.basename(path)
                            prefix = 'cd ' + (os.path.dirname(parts[1]) + '/' if os.path.dirname(parts[1]) else '')
                    else:
                        prefix = 'cd '
                        dirname = '.'
                        basename = ''
            else:
                # Pour les autres commandes avec des chemins
                parts = text.rsplit(' ', 1)
                if len(parts) > 1:
                    path = parts[1].strip()
                    if not path:  # Si le dernier mot est vide après l'espace
                        dirname = '.'
                        basename = ''
                    else:
                        # Gestion du ~ pour le home
                        if path.startswith('~'):
                            path = os.path.expanduser(path)
                        dirname = os.path.dirname(path) or '.'
                        basename = os.path.basename(path)
                    prefix = parts[0] + ' ' + (os.path.dirname(parts[1]) + '/' if os.path.dirname(parts[1]) else '')
                else:
                    # Si pas d'espace, on complète à partir du répertoire courant
                    prefix = ''
                    dirname = '.'
                    basename = parts[0]
            
            try:
                # Normalisation du chemin du répertoire
                if dirname.startswith('~'):
                    dirname = os.path.expanduser(dirname)
                
                if not os.path.exists(dirname):
                    return []
                    
                # Liste les fichiers/dossiers correspondants
                try:
                    files = os.listdir(dirname)
                except PermissionError:
                    return []
                
                # Filtre les fichiers/dossiers correspondants
                matches = []
                for f in files:
                    if f.startswith(basename):
                        full_path = os.path.join(dirname, f)
                        is_dir = os.path.isdir(full_path)
                        # Pour 'cd', on ne garde que les dossiers
                        if text.startswith('cd') and not is_dir:
                            continue
                        # Ajoute un / à la fin des dossiers
                        matches.append(f + ('/' if is_dir else ''))
                
                # Si on a un seul match et qu'on est en train de taper un chemin
                if len(matches) == 1 and (text.endswith('/') or ' ' in text):
                    single_match = matches[0]
                    # Si c'est un répertoire, on ouvre directement
                    if single_match.endswith('/'):
                        completed = prefix + single_match
                        return [completed]
                
                # Nettoie les chemins (supprime les doubles // sauf au début)
                matches = [m.replace('//', '/' if m.startswith('//') else '/') for m in matches]
                
                # Ajoute le préfixe de la commande
                if prefix:
                    matches = [prefix + m for m in matches]
                
                return sorted(matches)
                
            except Exception as e:
                log(f"Erreur lors de la complétion: {str(e)}\n{traceback.format_exc()}", error=True)
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
        try:
            command = self.get_current_command()
            if not command.strip() and not self.toPlainText().endswith('$ '):
                return  # Ne rien faire si pas de commande et pas sur la ligne de commande
                
            matches = self.get_completion_matches(command)
            
            if not matches:
                return  # Aucune correspondance
                
            if len(matches) == 1:
                # Une seule correspondance, on complète
                self.complete_command(matches[0])
            else:
                # Affiche les correspondances possibles
                self.append_output('\n' + '  '.join(matches) + '\n')
                # Réaffiche la commande en cours
                self.append_output(f"{self._prompt_text}{command}", is_command=True)
        except Exception as e:
            log(f"Erreur dans handle_tab_completion: {str(e)}\n{traceback.format_exc()}", error=True)
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
            
        # Ajoute la commande à l'historique seulement si elle est différente de la dernière commande
        if not self.history or cmd != self.history[-1]:
            self.history.append(cmd)
            # Limite la taille de l'historique à 1000 commandes
            if len(self.history) > 1000:
                self.history.pop(0)
                
        # Réinitialise l'index d'historique à la fin de la liste
        self.history_index = len(self.history)
        
        # Supprime la commande non enregistrée si elle existe
        if hasattr(self, '_current_unsaved_command'):
            delattr(self, '_current_unsaved_command')
        
        # Émet le signal avec la commande
        self.parent().command_entered.emit(cmd)
        
        # Passe à la ligne suivante et affiche un nouveau prompt
        self.append_output("\n" + self._prompt_text, is_prompt=True, move_cursor=True)

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
        self.current_dir = self.start_dir
        self.sudo_password = None
        self.waiting_for_password = False
        self.pending_commands = []
        self.init_file = None  # Pour stocker le chemin du fichier d'initialisation
        self.command_history = []  # Historique des commandes
        self.history_index = -1  # Index de l'historique actuel
        try:
            self.setup_ui()
            self.setup_process()
            self.setMinimumHeight(200)
            self.setMaximumHeight(800)
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
        # Installation d'un filtre d'événement pour gérer les flèches haut/bas
        self.command_input.installEventFilter(self)
        
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
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._process_finished)
        self.current_dir = self.start_dir
        
        # Afficher le prompt initial
        self.show_prompt()
        
    def _read_stdout(self):
        """Lit la sortie standard du processus"""
        if hasattr(self, 'process') and self.process:
            try:
                # Lire toutes les données disponibles
                while self.process.canReadLine() or self.process.bytesAvailable() > 0:
                    if self.process.canReadLine():
                        data = self.process.readLine().data().decode('utf-8', errors='replace')
                    else:
                        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
                    
                    if data:
                        # Filtrer les éventuelles fuites de mot de passe
                        if hasattr(self, 'sudo_password') and self.sudo_password:
                            data = data.replace(self.sudo_password, '********')
                        self.terminal.append_output(data, error=False)
                        # Forcer la mise à jour de l'interface
                        QApplication.processEvents()
                        
                # Faire défiler vers le bas pour voir les nouvelles sorties
                cursor = self.terminal.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.terminal.setTextCursor(cursor)
                
            except Exception as e:
                log(f"Erreur lors de la lecture de la sortie standard: {str(e)}", error=True)
    
    def _read_stderr(self):
        """Lit la sortie d'erreur du processus"""
        if hasattr(self, 'process') and self.process:
            try:
                # Lire toutes les données d'erreur disponibles
                while self.process.canReadLine() or self.process.bytesAvailable() > 0:
                    if self.process.canReadLine():
                        data = self.process.readLine().data().decode('utf-8', errors='replace')
                    else:
                        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
                    
                    if data:
                        # Filtrer les éventuelles fuites de mot de passe
                        if hasattr(self, 'sudo_password') and self.sudo_password:
                            data = data.replace(self.sudo_password, '********')
                            # Masquer les messages d'erreur liés à l'authentification
                            if 'password' in data.lower() and ('incorrect' in data.lower() or 'incorrect' in data.lower()):
                                data = "[sudo] erreur d'authentification\n"
                        self.terminal.append_output(data, error=True)
                        # Forcer la mise à jour de l'interface
                        QApplication.processEvents()
                
                # Faire défiler vers le bas pour voir les nouvelles sorties
                cursor = self.terminal.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.terminal.setTextCursor(cursor)
                
            except Exception as e:
                log(f"Erreur lors de la lecture de la sortie d'erreur: {str(e)}", error=True)
    
    def _process_finished(self, exit_code, exit_status):
        """Appelé quand le processus est terminé"""
        # Arrêter le timer de timeout
        if hasattr(self, 'process_timer') and self.process_timer.isActive():
            self.process_timer.stop()
        
        # Lire les dernières données qui pourraient rester dans les buffers
        self._read_stdout()
        self._read_stderr()
        
        # Afficher le code de sortie si différent de 0
        if exit_code != 0:
            # Vérifier s'il s'agit d'une erreur d'authentification
            if exit_code == 1 and hasattr(self, 'sudo_password') and self.sudo_password:
                self.terminal.append_output("\n[Erreur d'authentification: mot de passe incorrect]\n", error=True)
            else:
                self.terminal.append_output(f"\n[Processus terminé avec le code de sortie {exit_code}]\n", error=True)
        else:
            self.terminal.append_output("\n[Processus terminé avec succès]\n")
            
        # Nettoyer le script temporaire s'il existe
        temp_script = "/tmp/temp_sudo_script.sh"
        if os.path.exists(temp_script):
            try:
                os.remove(temp_script)
            except Exception as e:
                log(f"Erreur lors de la suppression du script temporaire: {str(e)}", error=True)
        
        # Réinitialiser le mot de passe après chaque commande sudo
        if hasattr(self, 'process') and self.process and 'sudo' in self.process.program():
            self.sudo_password = None
            
        # Exécuter les commandes en attente
        if self.pending_commands:
            next_cmd = self.pending_commands.pop(0)
            QTimer.singleShot(100, lambda: self.execute_command(next_cmd))
        else:
            self.show_prompt()

    def is_sudo_required(self, cmd):
        """Vérifie si la commande nécessite des droits sudo"""
        return cmd.strip().startswith('sudo ')

    def get_sudo_password(self):
        """Affiche une boîte de dialogue pour saisir le mot de passe sudo"""
        password, ok = QInputDialog.getText(
            self, 
            'Authentification requise',
            '[sudo] Mot de passe pour ' + os.getenv('USER', 'utilisateur') + ':',
            QLineEdit.Password
        )
        return password if ok else None

    def execute_command(self, cmd):
        """Exécute une commande dans le terminal de manière asynchrone"""
        if not cmd.strip():
            return
            
        # Nettoyer la commande
        original_cmd = cmd
        cmd = self.clean_command(cmd)
        
        # Ne pas logger les commandes contenant des mots de passe
        safe_to_log = not any(sensitive in cmd.lower() for sensitive in ['pass', 'pwd', 'secret', 'token', 'key'])
        if safe_to_log:
            log(f"Exécution de la commande: {cmd}")
        else:
            log("Exécution d'une commande sensible (masquée dans les logs)")
        
        # Si on attend déjà un mot de passe, ajouter à la file d'attente
        if self.waiting_for_password:
            self.pending_commands.append(original_cmd)
            return
            
        # Vérifier si la commande nécessite sudo
        if self.is_sudo_required(cmd) and not self.sudo_password:
            self.waiting_for_password = True
            self.sudo_password = self.get_sudo_password()
            self.waiting_for_password = False
            
            if not self.sudo_password:
                self.terminal.append_output("\n[commande sudo annulée]\n", error=True)
                self.show_prompt()
                return
                
        try:
            # Gestion spéciale pour la commande cd
            if cmd.startswith('cd '):
                new_dir = cmd[3:].strip()
                self._change_directory(new_dir)
                return
                
            # Arrêter le processus en cours s'il y en a un
            if hasattr(self, 'process') and self.process and self.process.state() == QProcess.Running:
                self.process.kill()
                self.process.waitForFinished()
            
            # Créer un nouveau processus
            self.process = QProcess(self)
            self.process.readyReadStandardOutput.connect(self._read_stdout)
            self.process.readyReadStandardError.connect(self._read_stderr)
            self.process.finished.connect(self._process_finished)
            
            # Configurer le processus
            self.process.setWorkingDirectory(self.current_dir)
            
            # Configurer l'environnement pour utiliser bash
            env = QProcessEnvironment.systemEnvironment()
            env.insert("SHELL", "/bin/bash")
            env.insert("PYTHONUNBUFFERED", "1")  # Désactiver la mise en buffer de Python
            env.insert("PYTHONIOENCODING", "utf-8")
            env.insert("PYTHONNOUSERSITE", "1")
            self.process.setProcessEnvironment(env)
            
            # Configurer les canaux de sortie
            self.process.setProcessChannelMode(QProcess.SeparateChannels)  # Pour gérer séparément stdout et stderr
            self.process.setReadChannel(QProcess.StandardOutput)
            
            # Préparer la commande avec sudo si nécessaire
            if self.is_sudo_required(cmd) and self.sudo_password:
                # Créer un script temporaire pour exécuter la commande sudo
                temp_script = "/tmp/temp_sudo_script.sh"
                cmd_to_execute = cmd[5:].lstrip()
                
                # Créer le script avec la commande sudo
                with open(temp_script, 'w') as f:
                    f.write('#!/bin/bash\n')
                    f.write(f'echo "{self.sudo_password}" | sudo -S {cmd_to_execute} 2>/dev/null\n')
                    f.write('exit $?\n')
                
                # Rendre le script exécutable
                os.chmod(temp_script, 0o700)
                
                # Utiliser le script temporaire
                cmd = f'/bin/bash {temp_script}'
            
            # Lancer la commande avec le mode non-bloquant
            self.process.start("/bin/bash", ["-c", f"set -o pipefail; stdbuf -oL -eL {cmd}"])
            
            # Configurer un timer pour gérer les timeouts
            self.process_timer = QTimer(self)
            self.process_timer.setSingleShot(True)
            self.process_timer.timeout.connect(self._handle_process_timeout)
            self.process_timer.start(30000)  # 30 secondes de timeout
            
        except Exception as e:
            error_msg = f"Erreur lors de l'exécution de la commande: {str(e)}"
            log(error_msg, error=True)
            self.terminal.append_output(f"{error_msg}\n", error=True)
            self.show_prompt()
            
    def _handle_process_timeout(self):
        """Gère le timeout d'un processus en cours d'exécution"""
        if hasattr(self, 'process') and self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.terminal.append_output("\n[Commande interrompue: délai d'attente dépassé]\n", error=True)
            self.show_prompt()
            
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
        prompt_text = f"{os.getenv('USER', 'user')}@{platform.uname().node.split('.')[0]}:{cwd}$ "
        
        # Afficher le prompt
        self.terminal.append_output(prompt_text, is_prompt=True)
        
    def eventFilter(self, obj, event):
        """Filtre les événements pour gérer la navigation dans l'historique"""
        if obj is self.command_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Up:  # Flèche haut
                self.navigate_history(-1)
                return True
            elif event.key() == Qt.Key_Down:  # Flèche bas
                self.navigate_history(1)
                return True
        return super().eventFilter(obj, event)
        
    def navigate_history(self, direction):
        """Navigue dans l'historique des commandes"""
        if not self.command_history:
            return
            
        # Sauvegarde la commande en cours si on commence à naviguer dans l'historique
        if not hasattr(self, '_current_unsaved_command') or self.history_index == len(self.command_history):
            self._current_unsaved_command = self.command_input.text()
            
        # Navigation dans l'historique
        if direction < 0:  # Flèche haut
            if self.history_index > 0:
                self.history_index -= 1
            elif self.history_index == -1 and self.command_history:
                self.history_index = len(self.command_history) - 1
            
            # Affiche la commande de l'historique
            if 0 <= self.history_index < len(self.command_history):
                self.command_input.setText(self.command_history[self.history_index])
                # Place le curseur à la fin du texte
                self.command_input.setCursorPosition(len(self.command_input.text()))
                
        elif direction > 0:  # Flèche bas
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                # Affiche la commande suivante dans l'historique
                self.command_input.setText(self.command_history[self.history_index])
                # Place le curseur à la fin du texte
                self.command_input.setCursorPosition(len(self.command_input.text()))
            else:
                # Si on est à la fin de l'historique, on restaure la commande non enregistrée
                if hasattr(self, '_current_unsaved_command'):
                    self.history_index = len(self.command_history)
                    self.command_input.setText(self._current_unsaved_command)
                    # Place le curseur à la fin du texte
                    self.command_input.setCursorPosition(len(self.command_input.text()))
        
    def on_command_entered(self):
        """Appelé quand une commande est entrée dans le champ de saisie"""
        cmd = self.command_input.text().strip()
        if not cmd:
            return
            
        try:
            # Ajouter la commande à l'historique si elle est différente de la dernière commande
            if not self.command_history or cmd != self.command_history[-1]:
                self.command_history.append(cmd)
                # Limiter la taille de l'historique à 100 commandes
                if len(self.command_history) > 100:
                    self.command_history.pop(0)
            
            # Réinitialiser l'index d'historique
            self.history_index = len(self.command_history)
            
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
            
            # Supprimer la commande non enregistrée si elle existe
            if hasattr(self, '_current_unsaved_command'):
                delattr(self, '_current_unsaved_command')
            
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
                log("Détachement du processus pour qu'il continue en arrière-plan...")
                try:
                    # Détacher le processus pour qu'il continue de s'exécuter
                    self.process.setParent(None)
                    self.process.detach()
                    log("Processus détaché avec succès")
                except Exception as e:
                    log(f"Erreur lors du détachement du processus: {str(e)}\n{traceback.format_exc()}", error=True)
            self.process = None
            log("Nettoyage du terminal terminé")
            
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
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())