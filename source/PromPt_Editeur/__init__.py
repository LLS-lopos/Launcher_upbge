from __future__ import annotations

__all__ = [
    "FenetreTerminal",
    "TerminalWidget",
    "PtyProcess",
    "engines",
    "pt_cli",
    "pt_editeur",
]


def __getattr__(name):
    if name in ("FenetreTerminal", "pt_cli"):
        from .cli import FenetreTerminal

        return FenetreTerminal
    if name in ("pt_editeur"):
        from .editeur import EditeurTexte

        return EditeurTexte
    if name == "TerminalWidget":
        from .terminal_widget import TerminalWidget

        return TerminalWidget
    if name == "PtyProcess":
        from .pty_backend import PtyProcess

        return PtyProcess
    if name == "engines":
        import importlib

        return importlib.import_module(".engines", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
