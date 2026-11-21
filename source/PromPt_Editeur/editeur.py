from __future__ import annotations

import os
import sys
from pathlib import Path

SOURCE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SOURCE_DIR not in sys.path:
    sys.path.insert(0, SOURCE_DIR)

try:
    from . import engines
    from .terminal_widget import TerminalWidget
except ImportError:
    from PromPt_Editeur import engines
    from PromPt_Editeur.terminal_widget import TerminalWidget

import bootstrap
from program.EDT_autocomplession import AutoCompleter
from program.EDT_syntaxe import SyntaxHighlighter

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFontDatabase, QFontMetricsF, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
)


class CompleteurLocal(AutoCompleter):
    def __init__(self, text_edit):
        self.extra_words = set()
        super().__init__(text_edit)

    def extract_words_from_document(self):
        super().extract_words_from_document()
        self.dynamic_words.update(self.extra_words)

    def set_custom_words(self, words):
        self.extra_words = set(words)
        self.dynamic_words.update(self.extra_words)


class EditeurTexte(QMainWindow):
    def __init__(self, titre="LPS Texte éditeur", fichier=None, parent=None):
        super().__init__(parent)
        self.titre = titre
        self.current_file = None
        self.setWindowTitle(titre)
        self.resize(960, 640)

        self.editor = QPlainTextEdit(self)
        self.configure_editor()
        self.setCentralWidget(self.editor)

        self.terminal = TerminalWidget(self)
        self.dock_terminal = QDockWidget("Terminal", self)
        self.dock_terminal.setWidget(self.terminal)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_terminal)
        self.dock_terminal.hide()

        self.highlighter = SyntaxHighlighter(self.editor.document())
        self.completer = CompleteurLocal(self.editor)

        self.create_actions()
        self.create_status_bar()
        self.connect_signals()
        self.refresh_modules()

        if fichier is not None:
            self.load_file(str(fichier))
        else:
            self.update_window_title()

    @classmethod
    def ouvrir_fichier(cls, fichier):
        editor = cls(fichier=fichier)
        editor.show()
        return editor

    def configure_editor(self):
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(11)
        self.editor.setFont(font)
        metrics = QFontMetricsF(font)
        self.editor.setTabStopDistance(metrics.horizontalAdvance("    "))
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.editor.setStyleSheet(
            "QPlainTextEdit { background: #1e1e1e; color: #d4d4d4; "
            "border: 0; selection-background-color: #264f78; }"
        )

    def create_actions(self):
        menu_fichier = self.menuBar().addMenu("&Fichier")
        menu_edition = self.menuBar().addMenu("&Édition")
        menu_affichage = self.menuBar().addMenu("&Affichage")
        menu_moteur = self.menuBar().addMenu("&Moteur")

        action_nouveau = QAction("&Nouveau", self)
        action_nouveau.setShortcut(QKeySequence.New)
        action_nouveau.triggered.connect(self.new_file)

        action_ouvrir = QAction("&Ouvrir...", self)
        action_ouvrir.setShortcut(QKeySequence.Open)
        action_ouvrir.triggered.connect(self.open_file)

        action_enregistrer = QAction("&Enregistrer", self)
        action_enregistrer.setShortcut(QKeySequence.Save)
        action_enregistrer.triggered.connect(self.save_file)

        action_enregistrer_sous = QAction("Enregistrer sous...", self)
        action_enregistrer_sous.setShortcut(QKeySequence.SaveAs)
        action_enregistrer_sous.triggered.connect(self.save_as)

        action_executer = QAction("&Exécuter dans le terminal", self)
        action_executer.setShortcut(QKeySequence("Ctrl+F5"))
        action_executer.triggered.connect(self.execute_file)

        action_executer_moteur = QAction("Exécuter avec le &moteur", self)
        action_executer_moteur.setShortcut(QKeySequence("Ctrl+F6"))
        action_executer_moteur.triggered.connect(self.execute_moteur)

        action_python_moteur = QAction("Python &UPBGE/Range", self)
        action_python_moteur.setShortcut(QKeySequence("Ctrl+Shift+P"))
        action_python_moteur.triggered.connect(self.python_moteur)

        self.engine_combo = QComboBox(self)
        for name, path in engines.available():
            self.engine_combo.addItem(name, path)
        if not self.engine_combo.count():
            self.engine_combo.addItem("Aucun moteur", None)

        action_fermer = QAction("&Fermer", self)
        action_fermer.setShortcut(QKeySequence("Ctrl+W"))
        action_fermer.triggered.connect(self.close)

        action_annuler = QAction("&Annuler", self)
        action_annuler.setShortcut(QKeySequence.Undo)
        action_annuler.triggered.connect(self.editor.undo)

        action_retablir = QAction("&Rétablir", self)
        action_retablir.setShortcut(QKeySequence.Redo)
        action_retablir.triggered.connect(self.editor.redo)

        action_couper = QAction("Cou&per", self)
        action_couper.setShortcut(QKeySequence.Cut)
        action_couper.triggered.connect(self.editor.cut)

        action_copier = QAction("&Copier", self)
        action_copier.setShortcut(QKeySequence.Copy)
        action_copier.triggered.connect(self.editor.copy)

        action_coller = QAction("C&oller", self)
        action_coller.setShortcut(QKeySequence.Paste)
        action_coller.triggered.connect(self.editor.paste)

        self.action_terminal = QAction("&Terminal", self)
        self.action_terminal.setCheckable(True)
        self.action_terminal.setShortcut(QKeySequence("Ctrl+`"))
        self.action_terminal.toggled.connect(self.dock_terminal.setVisible)

        self.action_retour_ligne = QAction("Retour à la &ligne", self)
        self.action_retour_ligne.setCheckable(True)
        self.action_retour_ligne.toggled.connect(self.set_line_wrap)

        action_modules = QAction("&Actualiser les modules", self)
        action_modules.setShortcut(QKeySequence("Ctrl+Shift+M"))
        action_modules.triggered.connect(self.refresh_modules)

        menu_fichier.addAction(action_nouveau)
        menu_fichier.addAction(action_ouvrir)
        menu_fichier.addAction(action_enregistrer)
        menu_fichier.addAction(action_enregistrer_sous)
        menu_fichier.addSeparator()
        menu_fichier.addAction(action_executer)
        menu_fichier.addAction(action_executer_moteur)
        menu_fichier.addSeparator()
        menu_fichier.addAction(action_fermer)

        menu_edition.addAction(action_annuler)
        menu_edition.addAction(action_retablir)
        menu_edition.addSeparator()
        menu_edition.addAction(action_couper)
        menu_edition.addAction(action_copier)
        menu_edition.addAction(action_coller)
        menu_edition.addSeparator()
        menu_edition.addAction(action_modules)

        menu_affichage.addAction(self.action_terminal)
        menu_affichage.addAction(self.action_retour_ligne)
        menu_moteur.addAction(action_python_moteur)

        toolbar = self.addToolBar("Éditeur")
        toolbar.addAction(action_nouveau)
        toolbar.addAction(action_ouvrir)
        toolbar.addAction(action_enregistrer)
        toolbar.addAction(action_executer)
        toolbar.addAction(action_executer_moteur)
        toolbar.addWidget(self.engine_combo)
        toolbar.addAction(action_python_moteur)
        toolbar.addAction(self.action_terminal)

    def create_status_bar(self):
        self.label_file = QLabel("")
        self.label_position = QLabel("Ln 1, Col 1")
        self.label_modified = QLabel("")
        self.label_modules = QLabel("Modules: 0")
        self.statusBar().addWidget(self.label_file, 1)
        self.statusBar().addPermanentWidget(self.label_modules)
        self.statusBar().addPermanentWidget(self.label_modified)
        self.statusBar().addPermanentWidget(self.label_position)
        self.update_status()

    def connect_signals(self):
        self.editor.cursorPositionChanged.connect(self.update_status)
        self.editor.document().modificationChanged.connect(self.on_modification_changed)
        self.dock_terminal.visibilityChanged.connect(self.action_terminal.setChecked)

    def set_line_wrap(self, enabled):
        mode = QPlainTextEdit.WidgetWidth if enabled else QPlainTextEdit.NoWrap
        self.editor.setLineWrapMode(mode)

    def module_names(self, directory):
        names = set()
        path = Path(directory)
        if not path.is_dir():
            return names
        for child in path.iterdir():
            if child.name.startswith(("_", ".")):
                continue
            if child.is_file() and child.suffix == ".py":
                names.add(child.stem)
            elif child.is_dir() and (child / "__init__.py").exists():
                names.add(child.name)
        return names

    def module_roots(self):
        roots = []
        if self.current_file:
            parent = Path(self.current_file).resolve().parent
            roots.extend([parent, parent / "source"])
        roots.append(Path(bootstrap.SOURCE_DIR))
        unique = []
        for root in roots:
            if root not in unique:
                unique.append(root)
        return unique

    def refresh_modules(self):
        names = {"bpy", "bge", "bpy.context", "bpy.data", "bge.logic"}
        for root in self.module_roots():
            names.update(self.module_names(root))
        self.completer.set_custom_words(names)
        self.label_modules.setText(f"Modules: {len(names)}")

    def update_status(self):
        cursor = self.editor.textCursor()
        self.label_position.setText(
            f"Ln {cursor.blockNumber() + 1}, Col {cursor.columnNumber() + 1}"
        )

    def on_modification_changed(self, modified):
        self.label_modified.setText("*" if modified else "")
        self.update_window_title()

    def update_window_title(self):
        name = Path(self.current_file).name if self.current_file else "sans titre"
        suffix = " *" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"{name}{suffix} — {self.titre}")
        self.label_file.setText(self.current_file or "sans titre")

    def load_file(self, path):
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Ouverture impossible", str(exc))
            return False
        self.editor.setPlainText(text)
        self.current_file = str(path)
        self.editor.document().setModified(False)
        self.update_window_title()
        self.refresh_modules()
        return True

    def new_file(self):
        if not self.maybe_save():
            return
        self.editor.clear()
        self.current_file = None
        self.editor.document().setModified(False)
        self.update_window_title()
        self.refresh_modules()

    def open_file(self):
        if not self.maybe_save():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir un fichier",
            self.current_file or "",
            "Fichiers Python (*.py);;Fichiers texte (*.txt);;Tous les fichiers (*)",
        )
        if path:
            self.load_file(path)

    def save_file(self):
        if self.current_file:
            return self.write_file(Path(self.current_file))
        return self.save_as()

    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le fichier",
            self.current_file or "",
            "Fichiers Python (*.py);;Fichiers texte (*.txt);;Tous les fichiers (*)",
        )
        if not path:
            return False
        return self.write_file(Path(path))

    def write_file(self, path):
        try:
            path.write_text(self.editor.toPlainText(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Enregistrement impossible", str(exc))
            return False
        self.current_file = str(path)
        self.editor.document().setModified(False)
        self.update_window_title()
        self.refresh_modules()
        return True

    def maybe_save(self):
        if not self.editor.document().isModified():
            return True
        answer = QMessageBox.question(
            self,
            "Modifications non enregistrées",
            "Voulez-vous enregistrer les modifications ?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if answer == QMessageBox.Save:
            return self.save_file()
        return answer == QMessageBox.Discard

    def execute_file(self):
        if not self.current_file:
            QMessageBox.information(
                self, "Exécution", "Enregistrez d'abord le fichier pour l'exécuter."
            )
            return
        path = Path(self.current_file)
        self.action_terminal.setChecked(True)
        cwd = str(path.parent)
        if path.suffix == ".py":
            self.terminal.start_command([sys.executable, "-u", str(path)], cwd=cwd, clear=True)
        else:
            self.terminal.start_shell(cwd=cwd, clear=True)
        self.terminal.setFocus()

    def engine_path(self):
        executable = self.engine_combo.currentData()
        if not executable:
            QMessageBox.warning(self, "Moteur introuvable", "Aucun exécutable UPBGE/Range n'est configuré.")
            return None
        return executable

    def execute_moteur(self):
        if not self.current_file:
            QMessageBox.information(
                self, "Exécution", "Enregistrez d'abord le fichier pour l'exécuter."
            )
            return
        executable = self.engine_path()
        if not executable:
            return
        path = Path(self.current_file)
        self.action_terminal.setChecked(True)
        self.terminal.start_command(
            engines.script_command(executable, path), cwd=str(path.parent), clear=True
        )
        self.statusBar().showMessage(f"Moteur : {self.engine_combo.currentText()}")
        self.terminal.setFocus()

    def python_moteur(self):
        executable = self.engine_path()
        if not executable:
            return
        self.action_terminal.setChecked(True)
        cwd = str(Path(self.current_file).parent) if self.current_file else None
        self.terminal.start_command(
            engines.interactive_command(executable), cwd=cwd, clear=True
        )
        self.statusBar().showMessage(f"Python moteur : {self.engine_combo.currentText()}")
        self.terminal.setFocus()

    def closeEvent(self, event):
        if not self.maybe_save():
            event.ignore()
            return
        self.terminal.shutdown()
        super().closeEvent(event)


pt_editeur = EditeurTexte
LoposEditor = EditeurTexte


def main(argv=None):
    app = QApplication.instance() or QApplication(argv or [])
    window = EditeurTexte()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
