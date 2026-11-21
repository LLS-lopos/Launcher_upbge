from __future__ import annotations

import os
import sys

SOURCE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SOURCE_DIR not in sys.path:
    sys.path.insert(0, SOURCE_DIR)

try:
    from . import engines
    from .terminal_widget import TerminalWidget
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from source.PromPt_Editeur.PromPt_Editeur import engines
    from source.PromPt_Editeur.PromPt_Editeur.terminal_widget import TerminalWidget

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QComboBox, QMainWindow, QMessageBox


class FenetreTerminal(QMainWindow):
    def __init__(self, titre="Terminal UPBGE", cwd=None, parent=None):
        super().__init__(parent)
        self.cwd = cwd or os.getcwd()
        self.setWindowTitle(titre)
        self.resize(920, 560)
        self.terminal = TerminalWidget(self)
        self.setCentralWidget(self.terminal)
        self.statusBar().showMessage(self.cwd)
        self.terminal.process_finished.connect(self.on_process_finished)
        self.build_actions()
        self.terminal.start_shell(self.cwd)
        self.terminal.setFocus()

    def build_actions(self):
        menu_fichier = self.menuBar().addMenu("&Fichier")
        menu_edition = self.menuBar().addMenu("&Édition")
        menu_moteur = self.menuBar().addMenu("&Moteur")

        action_nouveau = QAction("&Nouveau shell", self)
        action_nouveau.setShortcut(QKeySequence("Ctrl+Shift+N"))
        action_nouveau.triggered.connect(self.nouveau_shell)

        action_fermer = QAction("&Fermer", self)
        action_fermer.setShortcut(QKeySequence("Ctrl+W"))
        action_fermer.triggered.connect(self.close)

        action_copier = QAction("&Copier", self)
        action_copier.setShortcut(QKeySequence("Ctrl+Shift+C"))
        action_copier.triggered.connect(self.terminal.copy)

        action_coller = QAction("C&oller", self)
        action_coller.setShortcut(QKeySequence("Ctrl+Shift+V"))
        action_coller.triggered.connect(self.terminal.paste)

        action_effacer = QAction("&Effacer", self)
        action_effacer.setShortcut(QKeySequence("Ctrl+L"))
        action_effacer.triggered.connect(self.terminal.clear)

        action_python_moteur = QAction("Python &UPBGE/Range", self)
        action_python_moteur.setShortcut(QKeySequence("Ctrl+Shift+P"))
        action_python_moteur.triggered.connect(self.python_moteur)

        self.engine_combo = QComboBox(self)
        for name, path in engines.available():
            self.engine_combo.addItem(name, path)
        if not self.engine_combo.count():
            self.engine_combo.addItem("Aucun moteur", None)

        menu_fichier.addAction(action_nouveau)
        menu_fichier.addAction(action_fermer)
        menu_edition.addAction(action_copier)
        menu_edition.addAction(action_coller)
        menu_edition.addAction(action_effacer)
        menu_moteur.addAction(action_python_moteur)

        toolbar = self.addToolBar("Terminal")
        toolbar.addAction(action_nouveau)
        toolbar.addAction(action_python_moteur)
        toolbar.addWidget(self.engine_combo)
        toolbar.addAction(action_effacer)
        toolbar.addAction(action_fermer)

    def nouveau_shell(self):
        self.terminal.start_shell(self.cwd, clear=True)
        self.terminal.setFocus()

    def python_moteur(self):
        executable = self.engine_combo.currentData()
        if not executable:
            QMessageBox.warning(self, "Moteur introuvable", "Aucun exécutable UPBGE/Range n'est configuré.")
            return
        self.terminal.start_command(engines.interactive_command(executable), cwd=self.cwd, clear=True)
        self.statusBar().showMessage(f"Python moteur : {self.engine_combo.currentText()}")
        self.terminal.setFocus()

    def on_process_finished(self, code):
        self.statusBar().showMessage(f"{self.cwd} — code {code}", 10000)

    def closeEvent(self, event):
        if self.terminal.pty.running:
            answer = QMessageBox.question(
                self,
                "Terminal actif",
                "Un processus est encore en cours. Le terminer ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer == QMessageBox.No:
                event.ignore()
                return
        self.terminal.shutdown()
        super().closeEvent(event)


pt_cli = FenetreTerminal


def main(argv=None):
    app = QApplication.instance() or QApplication(argv or [])
    window = FenetreTerminal()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
