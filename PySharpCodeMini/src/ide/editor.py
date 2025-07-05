from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re

class Editor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = None

    def set_highlighter(self, highlighter):
        self.highlighter = highlighter
        self.highlighter.setDocument(self.document())

    def apply_highlighter(self):
        if self.highlighter:
            self.highlighter.rehighlight()