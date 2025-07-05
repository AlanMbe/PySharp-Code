import re
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document, dark_mode=False):
        super().__init__(document)
        self.highlighting_rules = []
        self.dark_mode = dark_mode
        self.set_dark_mode(self.dark_mode)

    def set_dark_mode(self, dark):
        self.dark_mode = dark
        if dark:
            self.colors = {
                "keyword_color": "#ff9500",
                "string_color": "#a5c261",
                "comment_color": "#888888",
                "function_color": "#ffd700",
                "class_color": "#e6e6e6",
                "call_color": "#7ec3e6"
            }
        else:
            self.colors = {
                "keyword_color": "#ff9500",
                "string_color": "#6a8759",
                "comment_color": "#808080",
                "function_color": "#ffc66d",
                "class_color": "#a9b7c6",
                "call_color": "#6897bb"
        }
        self.setup_highlighting_rules()
        self.rehighlight()

    def setup_highlighting_rules(self):
        """根据当前颜色设置高亮规则"""
        self.highlighting_rules.clear()

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(self.colors["keyword_color"]))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ['def', 'class', 'if', 'else', 'elif', 'while', 'for',
                    'import', 'from', 'return', 'try', 'except', 'with',
                    'as', 'pass', 'break', 'continue', 'and', 'or', 'not']
        for word in keywords:
            pattern = re.compile(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor(self.colors["string_color"]))
        self.highlighting_rules.append((re.compile(r'".*?"'), string_format))
        self.highlighting_rules.append((re.compile(r"'.*?'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(self.colors["comment_color"]))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((re.compile(r'#.*'), comment_format))

        function_format = QTextCharFormat()
        function_format.setForeground(QColor(self.colors["function_color"]))
        self.highlighting_rules.append((re.compile(r'\bdef\s+(\w+)\b'), function_format))

        class_format = QTextCharFormat()
        class_format.setForeground(QColor(self.colors["class_color"]))
        self.highlighting_rules.append((re.compile(r'\bclass\s+(\w+)\b'), class_format))

        call_format = QTextCharFormat()
        call_format.setForeground(QColor(self.colors["call_color"]))
        self.highlighting_rules.append((re.compile(r'\b\w+(?=\()'), call_format))

    def update_highlighting_colors(self, new_colors):
        """更新高亮颜色并重新设置规则"""
        self.colors.update(new_colors)
        self.setup_highlighting_rules()
        self.rehighlight()

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)

class CSharpHighlighter(QSyntaxHighlighter):
    def __init__(self, document, dark_mode=False):
        super().__init__(document)
        self.highlighting_rules = []
        self.dark_mode = dark_mode
        self.set_dark_mode(self.dark_mode)

    def set_dark_mode(self, dark):
        self.dark_mode = dark
        if dark:
            self.colors = {
                "keyword_color": "#ffcc66",
                "string_color": "#a5c261",
                "comment_color": "#888888",
                "function_color": "#ffd700",
                "class_color": "#e6e6e6",
                "call_color": "#7ec3e6"
            }
        else:
            self.colors = {
                "keyword_color": "#0033b3",
                "string_color": "#6a8759",
                "comment_color": "#808080",
                "function_color": "#ffc66d",
                "class_color": "#a9b7c6",
                "call_color": "#6897bb"
        }
        self.setup_highlighting_rules()
        self.rehighlight()

    def setup_highlighting_rules(self):
        """根据当前颜色设置高亮规则"""
        self.highlighting_rules.clear()

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(self.colors["keyword_color"]))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ['class', 'void', 'using', 'namespace', 'public', 'private',
                    'if', 'else', 'for', 'while', 'return', 'int', 'string', 'bool']
        for word in keywords:
            pattern = re.compile(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor(self.colors["string_color"]))
        self.highlighting_rules.append((re.compile(r'".*?"'), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(self.colors["comment_color"]))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((re.compile(r'//.*'), comment_format))

        function_format = QTextCharFormat()
        function_format.setForeground(QColor(self.colors["function_color"]))
        self.highlighting_rules.append((re.compile(r'\b(?:void|int|string|bool)\s+(\w+)\s*\('), function_format))

        class_format = QTextCharFormat()
        class_format.setForeground(QColor(self.colors["class_color"]))
        self.highlighting_rules.append((re.compile(r'\bclass\s+(\w+)\b'), class_format))

        call_format = QTextCharFormat()
        call_format.setForeground(QColor(self.colors["call_color"]))
        self.highlighting_rules.append((re.compile(r'\b\w+(?=\()'), call_format))

    def update_highlighting_colors(self, new_colors):
        """更新高亮颜色并重新设置规则"""
        self.colors.update(new_colors)
        self.setup_highlighting_rules()
        self.rehighlight()

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)
