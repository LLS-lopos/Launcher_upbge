from __future__ import annotations

import codecs
import os
import shlex
import subprocess

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QFontMetricsF,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QVBoxLayout, QWidget

from . import engines
from .pty_backend import PtyProcess


class _TerminalView(QPlainTextEdit):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def keyPressEvent(self, event):
        self.owner.handle_key(event)


class TerminalWidget(QWidget):
    process_finished = Signal(int)

    BASE_COLORS = (
        "#1c1c1c",
        "#cd3131",
        "#0dbc79",
        "#e5e510",
        "#2472c8",
        "#bc3fbc",
        "#11a8cd",
        "#e5e5e5",
    )
    BRIGHT_COLORS = (
        "#666666",
        "#f14c4c",
        "#23d18b",
        "#f5f543",
        "#3b8eea",
        "#d670d6",
        "#29b8db",
        "#ffffff",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pty = PtyProcess(self)
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._view = _TerminalView(self)
        self._cursor = self._view.textCursor()
        self._esc_state = 0
        self._csi_params = ""
        self._osc_buffer = ""
        self._saved_cursor = None
        self._alternate = None
        self._bracketed_paste = False
        self._configure_view()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)
        self.setFocusProxy(self._view)
        self._pty.output.connect(self.on_output)
        self._pty.finished.connect(self.on_finished)
        self._pty.error.connect(self.on_error)

    @property
    def pty(self):
        return self._pty

    def _configure_view(self):
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(10)
        self._view.setFont(font)
        self._view.setReadOnly(True)
        self._view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._view.setMaximumBlockCount(20000)
        self._view.setContextMenuPolicy(Qt.NoContextMenu)
        self._view.setStyleSheet(
            "QPlainTextEdit { background: #101014; color: #d4d4d4; "
            "border: 0; selection-background-color: #264f78; }"
        )
        self._view.setFocusPolicy(Qt.StrongFocus)

    def terminal_size(self):
        metrics = QFontMetricsF(self._view.font())
        char_width = max(1, int(metrics.horizontalAdvance("M")))
        char_height = max(1, int(metrics.height()))
        width = max(1, self._view.viewport().width())
        height = max(1, self._view.viewport().height())
        return width // char_width, height // char_height

    def start_shell(self, cwd=None, clear=False):
        if clear:
            self.reset_terminal()
        cols, rows = self.terminal_size()
        return self._pty.start(cwd=cwd, cols=cols, rows=rows)

    def start_command(self, argv, cwd=None, clear=False):
        if clear:
            self.reset_terminal()
        cols, rows = self.terminal_size()
        return self._pty.start(command=argv, cwd=cwd, cols=cols, rows=rows)

    def copy(self):
        self._view.copy()

    def paste(self):
        self._pty.write(QApplication.clipboard().text())

    def clear(self):
        self.reset_terminal()

    def terminate(self):
        self._pty.terminate()

    def shutdown(self):
        self._pty.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pty.running:
            cols, rows = self.terminal_size()
            self._pty.resize(cols, rows)

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)

    def on_output(self, data):
        text = self._decoder.decode(data)
        self.process_text(text)

    def on_finished(self, code):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#808080"))
        self._cursor.setCharFormat(fmt)
        if not self._cursor.atBlockStart():
            self._cursor.insertText("\n")
        self._cursor.insertText(f"[terminé: {code}]\n")
        self.sync_cursor()
        self.process_finished.emit(code)

    def on_error(self, message):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#f14c4c"))
        self._cursor.setCharFormat(fmt)
        if not self._cursor.atBlockStart():
            self._cursor.insertText("\n")
        self._cursor.insertText(f"[erreur PTY: {message}]\n")
        self.sync_cursor()

    def process_text(self, text):
        for char in text:
            if self._esc_state == 0:
                self.process_plain(char)
            elif self._esc_state == 1:
                self.process_escape(char)
            elif self._esc_state == 2:
                self.process_csi(char)
            elif self._esc_state == 4:
                self.process_osc(char)
            elif self._esc_state == 5:
                self._esc_state = 0
            elif self._esc_state == 6:
                self._esc_state = 0 if char == "\\" else 4

    def process_plain(self, char):
        if char == "\x1b":
            self._esc_state = 1
        elif char == "\x9b":
            self._esc_state = 2
            self._csi_params = ""
        elif char == "\r":
            self._cursor.movePosition(QTextCursor.StartOfLine)
        elif char == "\b":
            self._cursor.movePosition(QTextCursor.Left)
        elif char == "\n":
            self._cursor.movePosition(QTextCursor.EndOfLine)
            self._cursor.insertText("\n")
        elif char == "\t":
            column = self._cursor.columnNumber()
            self.insert_text(" " * (8 - column % 8))
        elif char == "\x07":
            return
        elif char >= " ":
            self.insert_text(char)
        else:
            return
        self.sync_cursor()

    def process_escape(self, char):
        if char == "[":
            self._esc_state = 2
            self._csi_params = ""
        elif char == "]":
            self._esc_state = 4
            self._osc_buffer = ""
        elif char in "PX^_":
            self._esc_state = 5
        elif char == "c":
            self.reset_terminal()
        else:
            self._esc_state = 0

    def process_csi(self, char):
        code = ord(char)
        if 0x30 <= code <= 0x3F or char in ":;<=>?":
            self._csi_params += char
            return
        if 0x40 <= code <= 0x7E:
            self.handle_csi(char, self._csi_params)
        self._esc_state = 0
        self._csi_params = ""

    def process_osc(self, char):
        if char == "\x07":
            self._esc_state = 0
            self._osc_buffer = ""
        elif char == "\x1b":
            self._esc_state = 6
        else:
            self._osc_buffer += char

    def handle_csi(self, final, raw_params):
        private = raw_params.startswith("?")
        params_text = raw_params.lstrip("?<>=")
        values = []
        for item in params_text.split(";"):
            if item.isdigit():
                values.append(int(item))
        if private:
            code = values[0] if values else 0
            if code == 25:
                self._view.setCursorWidth(0 if final == "l" else 1)
            elif code in (47, 1047, 1049):
                if final == "h":
                    self.enter_alternate_screen()
                else:
                    self.leave_alternate_screen()
            elif code == 2004:
                self._bracketed_paste = final == "h"
            return
        count = max(1, values[0]) if values else 1
        if final == "m":
            self.apply_sgr(values or [0])
        elif final == "A":
            self._cursor.movePosition(QTextCursor.Up, QTextCursor.MoveAnchor, count)
        elif final == "B":
            self._cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, count)
        elif final == "C":
            self._cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, count)
        elif final == "D":
            self._cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, count)
        elif final in "Hf":
            row = max(1, values[0]) if values else 1
            column = max(1, values[1]) if len(values) > 1 else 1
            self.move_to(row, column)
        elif final == "G":
            self.move_to_column(max(1, values[0]) if values else 1)
        elif final == "d":
            self.move_to_row(max(1, values[0]) if values else 1)
        elif final == "J":
            self.erase_display(values[0] if values else 0)
        elif final == "K":
            self.erase_line(values[0] if values else 0)
        elif final == "s":
            self.save_cursor()
        elif final == "u":
            self.restore_cursor()
        self.sync_cursor()

    def move_to(self, row, column):
        self._cursor.movePosition(QTextCursor.Start)
        self._cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, row - 1)
        self.move_to_column(column)

    def move_to_row(self, row):
        self._cursor.movePosition(QTextCursor.Start)
        self._cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, row - 1)

    def move_to_column(self, column):
        self._cursor.movePosition(QTextCursor.StartOfLine)
        self._cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, column - 1)

    def erase_display(self, mode):
        if mode in (2, 3):
            self._cursor.select(QTextCursor.Document)
            self._cursor.removeSelectedText()
            self._cursor.setCharFormat(QTextCharFormat())
            self._cursor.movePosition(QTextCursor.Start)
        elif mode == 0:
            self._cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            self._cursor.removeSelectedText()
        elif mode == 1:
            self._cursor.movePosition(QTextCursor.Start, QTextCursor.KeepAnchor)
            self._cursor.removeSelectedText()

    def erase_line(self, mode):
        if mode == 0:
            self._cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        elif mode == 1:
            self._cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
        elif mode == 2:
            self._cursor.movePosition(QTextCursor.StartOfLine)
            self._cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        else:
            return
        self._cursor.removeSelectedText()

    def save_cursor(self):
        self._saved_cursor = (self._cursor.position(), self._cursor.charFormat())

    def restore_cursor(self):
        if self._saved_cursor is None:
            return
        position, fmt = self._saved_cursor
        self._cursor.setPosition(position)
        self._cursor.setCharFormat(fmt)

    def enter_alternate_screen(self):
        if self._alternate is not None:
            return
        self._alternate = (
            self._view.toPlainText(),
            self._cursor.position(),
            self._cursor.charFormat(),
        )
        self._cursor.select(QTextCursor.Document)
        self._cursor.removeSelectedText()
        self._cursor.setCharFormat(QTextCharFormat())
        self._cursor.movePosition(QTextCursor.Start)

    def leave_alternate_screen(self):
        if self._alternate is None:
            return
        text, position, fmt = self._alternate
        self._alternate = None
        self._view.setPlainText(text)
        self._cursor = self._view.textCursor()
        self._cursor.setPosition(min(position, len(text)))
        self._cursor.setCharFormat(fmt)

    def reset_terminal(self):
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._view.clear()
        self._cursor = self._view.textCursor()
        self._esc_state = 0
        self._csi_params = ""
        self._osc_buffer = ""
        self._alternate = None
        self._saved_cursor = None
        self._view.setCursorWidth(1)

    def apply_sgr(self, values):
        fmt = QTextCharFormat()
        index = 0
        while index < len(values):
            code = values[index]
            if code == 0:
                fmt = QTextCharFormat()
            elif code == 1:
                fmt.setFontWeight(QFont.Bold)
            elif code == 22:
                fmt.setFontWeight(QFont.Normal)
            elif code == 3:
                fmt.setFontItalic(True)
            elif code == 23:
                fmt.setFontItalic(False)
            elif code == 4:
                fmt.setFontUnderline(True)
            elif code == 24:
                fmt.setFontUnderline(False)
            elif 30 <= code <= 37:
                fmt.setForeground(QColor(self.BASE_COLORS[code - 30]))
            elif 40 <= code <= 47:
                fmt.setBackground(QColor(self.BASE_COLORS[code - 40]))
            elif 90 <= code <= 97:
                fmt.setForeground(QColor(self.BRIGHT_COLORS[code - 90]))
            elif 100 <= code <= 107:
                fmt.setBackground(QColor(self.BRIGHT_COLORS[code - 100]))
            elif code == 39:
                fmt.clearForeground()
            elif code == 49:
                fmt.clearBackground()
            elif code in (38, 48):
                color, consumed = self.extended_color(values, index + 1)
                if color is not None:
                    if code == 38:
                        fmt.setForeground(color)
                    else:
                        fmt.setBackground(color)
                index += consumed
            index += 1
        self._cursor.setCharFormat(fmt)

    def extended_color(self, values, index):
        if index >= len(values):
            return None, 0
        mode = values[index]
        if mode == 5 and index + 1 < len(values):
            return QColor(self.color_256(values[index + 1])), 2
        if mode == 2 and index + 3 < len(values):
            return QColor(values[index + 1], values[index + 2], values[index + 3]), 4
        return None, 1

    def color_256(self, value):
        if value < 16:
            palette = self.BASE_COLORS + self.BRIGHT_COLORS
            return palette[value]
        if value < 232:
            value -= 16
            steps = (0, 95, 135, 175, 215, 255)
            r = steps[value // 36]
            g = steps[(value % 36) // 6]
            b = steps[value % 6]
            return QColor(r, g, b)
        level = 8 + (value - 232) * 10
        return QColor(level, level, level)

    def insert_text(self, text):
        for char in text:
            if not self._cursor.atEnd():
                self._cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            self._cursor.insertText(char)

    def sync_cursor(self):
        self._view.setTextCursor(self._cursor)
        self._view.ensureCursorVisible()

    def current_command_line(self):
        text = self._cursor.block().text()
        upper = text.upper()
        for keyword in engines.GAME_KEYWORDS:
            start = 0
            while True:
                index = upper.find(keyword, start)
                if index < 0:
                    break
                previous = text[index - 1] if index else ""
                if not previous or previous.isspace() or previous in "$#❯>":
                    return text[index:].strip()
                start = index + len(keyword)
        for marker in ("$ ", "# ", "❯ ", "> "):
            index = text.rfind(marker)
            if index >= 0:
                return text[index + len(marker):].strip()
        return text.strip()

    def quote_command(self, parts):
        if os.name == "nt":
            return " ".join(subprocess.list2cmdline([part]) for part in parts)
        return " ".join(shlex.quote(part) for part in parts)

    def rewrite_game_command(self, line):
        try:
            parts = shlex.split(line, posix=(os.name != "nt"))
        except ValueError:
            return False, None, None
        if not parts:
            return False, None, None
        keyword = parts[0].upper()
        if keyword not in engines.GAME_KEYWORDS:
            return False, None, None
        executable = engines.game_commands().get(keyword)
        if not executable:
            return True, None, f"[{keyword}] exécutable introuvable dans la configuration"
        if len(parts) < 2:
            return True, None, f"Usage: {keyword} fichier.blend [arguments...]"
        command = self.quote_command([executable] + parts[1:])
        return True, command, None

    def handle_key(self, event):
        key = event.key()
        modifiers = event.modifiers()
        if key in (Qt.Key_Return, Qt.Key_Enter) and not modifiers and self._pty.running:
            line = self.current_command_line()
            handled, replacement, message = self.rewrite_game_command(line)
            if handled:
                self._pty.write(b"\x15" + b"\b" * len(line))
                if replacement:
                    self._pty.write((replacement + "\r").encode("utf-8"))
                elif message:
                    self._pty.write(("echo " + message + "\r").encode("utf-8"))
                event.accept()
                return
        if modifiers & Qt.ControlModifier and modifiers & Qt.ShiftModifier:
            if key == Qt.Key_C:
                self._view.copy()
                event.accept()
                return
            if key == Qt.Key_V:
                text = QApplication.clipboard().text()
                self._pty.write(text)
                event.accept()
                return
        if modifiers & Qt.ControlModifier and Qt.Key_A <= key <= Qt.Key_Z:
            letter = chr(ord("a") + key - Qt.Key_A)
            self._pty.write(bytes([ord(letter) - ord("a") + 1]))
            event.accept()
            return
        special = {
            Qt.Key_Return: b"\r",
            Qt.Key_Enter: b"\r",
            Qt.Key_Backspace: b"\x7f",
            Qt.Key_Tab: b"\x1b[Z" if modifiers & Qt.ShiftModifier else b"\t",
            Qt.Key_Up: b"\x1b[A",
            Qt.Key_Down: b"\x1b[B",
            Qt.Key_Right: b"\x1b[C",
            Qt.Key_Left: b"\x1b[D",
            Qt.Key_Home: b"\x1b[H",
            Qt.Key_End: b"\x1b[F",
            Qt.Key_Delete: b"\x1b[3~",
            Qt.Key_PageUp: b"\x1b[5~",
            Qt.Key_PageDown: b"\x1b[6~",
            Qt.Key_Escape: b"\x1b",
        }
        if key in special:
            self._pty.write(special[key])
            event.accept()
            return
        text = event.text()
        if text:
            if modifiers & Qt.AltModifier and not modifiers & Qt.ControlModifier:
                text = "\x1b" + text
            self._pty.write(text)
        event.accept()
