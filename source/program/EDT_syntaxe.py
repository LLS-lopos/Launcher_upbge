from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QTextDocument, QFont
from PySide6.QtCore import Qt, QRegularExpression

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document)

        # Définir les formats de texte pour la coloration
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(Qt.blue)
        self.keyword_format.setFontWeight(QFont.Bold)

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(Qt.green)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(Qt.red)

        # Définir les règles de coloration
        self.highlighting_rules = []

        keywords = [
        "def", "class", "import", "from", "as", "if",
        "else", "elif", "while", "for", "return", "and",
        "or", "print", "None", "is", "async", "self", "await",
        ]
        for keyword in keywords:
            pattern = QRegularExpression(r'\b' + keyword + r'\b')
            self.highlighting_rules.append((pattern, self.keyword_format))

        # Règle pour les commentaires
        comment_pattern = QRegularExpression(r'#.*')
        self.highlighting_rules.append((comment_pattern, self.comment_format))

        # Règle pour les chaînes de caractères
        string_pattern = QRegularExpression(r'(\"(?:\\.|[^\"])*\")')
        self.highlighting_rules.append((string_pattern, self.string_format))

    def highlightBlock(self, text: str):
        for pattern, fmt in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
