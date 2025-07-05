import json
import os
from PySide6.QtGui import QFont, QTextCharFormat, QColor
from PySide6.QtWidgets import QPushButton

def load_theme_from_json(theme_file):
    """从 JSON 文件加载主题配置"""
    if not os.path.exists(theme_file):
        print(f"主题文件不存在: {theme_file}")
        return {}
    with open(theme_file, "r", encoding="utf-8") as f:
        try:
            theme = json.load(f)
            print(f"成功加载主题: {theme}")
            return theme
        except json.JSONDecodeError as e:
            print(f"无法解析主题文件：{theme_file}, 错误: {e}")
            return {}

def apply_theme_and_font(self, theme_file=None):
    """应用主题和字体，适配多标签页编辑器，支持深灰/浅灰自动切换"""
    theme = {}
    if theme_file:
        theme = load_theme_from_json(theme_file)

    # 默认浅色主题
    default_theme = {
        "font_name": self.font_name,
        "font_size": self.font_size,
        "font_style": "normal",
        "editor_background": "#ffffff",
        "editor_foreground": "#000000",
        "terminal_background": "#ffffff",
        "terminal_foreground": "#000000",
        "menu_background": "#f3f3f3",
        "menu_foreground": "#000000",
        "button_background": "#e0e0e0",
        "button_foreground": "#000000",
        "main_background": "#ffffff",
        "main_foreground": "#000000",
        "highlighting_colors": {
            "keyword_color": "#0000ff",
            "string_color": "#a31515",
            "comment_color": "#008000",
            "function_color": "#795e26",
            "class_color": "#267f99",
            "call_color": "#001080"
        }
    }
    # 深灰色主题
    dark_theme = {
        "font_name": self.font_name,
        "font_size": self.font_size,
        "font_style": "normal",
        "editor_background": "#23272e",
        "editor_foreground": "#dddddd",
        "terminal_background": "#23272e",
        "terminal_foreground": "#dddddd",
        "menu_background": "#23272e",
        "menu_foreground": "#dddddd",
        "button_background": "#2d313a",
        "button_foreground": "#dddddd",
        "main_background": "#23272e",
        "main_foreground": "#dddddd",
        "highlighting_colors": {
            "keyword_color": "#82aaff",
            "string_color": "#ecc48d",
            "comment_color": "#5c6370",
            "function_color": "#c3e88d",
            "class_color": "#ffcb6b",
            "call_color": "#82aaff"
        }
    }
    # 判断主题
    if getattr(self, 'theme', '').lower().startswith('dark'):
        theme = {**default_theme, **dark_theme, **theme}
    else:
        theme = {**default_theme, **theme}

    # 设置字体
    font_name = theme.get("font_name", self.font_name)
    font_size = theme.get("font_size", self.font_size)
    font_style = theme.get("font_style", "normal").lower()
    font = QFont(font_name, font_size)
    if font_style == "italic":
        font.setItalic(True)
    elif font_style == "bold":
        font.setBold(True)

    # 遍历所有标签页编辑器
    if hasattr(self, "tab_widget"):
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if hasattr(editor, "setFont"):
                editor.setFont(font)
                # 设置编辑器颜色
                editor_bg = theme.get("editor_background", "#ffffff")
                editor_fg = theme.get("editor_foreground", "#000000")
                editor.setStyleSheet(f"background-color: {editor_bg}; color: {editor_fg};")

    # 设置终端字体和颜色
    self.terminal_output.setFont(font)
    self.terminal_input.setFont(font)
    terminal_bg = theme.get("terminal_background", "#ffffff")
    terminal_fg = theme.get("terminal_foreground", "#000000")
    self.terminal_output.setStyleSheet(f"background-color: {terminal_bg}; color: {terminal_fg};")
    self.terminal_input.setStyleSheet(f"background-color: {terminal_bg}; color: {terminal_fg};")

    # 更新菜单栏样式
    menu_bg = theme.get("menu_background", "#f3f3f3")
    menu_fg = theme.get("menu_foreground", "#000000")
    self.menuBar().setStyleSheet(f"background-color: {menu_bg}; color: {menu_fg};")

    # 更新按钮样式
    button_bg = theme.get("button_background", "#e0e0e0")
    button_fg = theme.get("button_foreground", "#000000")
    for btn in self.findChildren(QPushButton):
        btn.setStyleSheet(f"background-color: {button_bg}; color: {button_fg};")

    # 更新主窗口背景
    main_bg = theme.get("main_background", "#ffffff")
    main_fg = theme.get("main_foreground", "#000000")
    self.setStyleSheet(f"background-color: {main_bg}; color: {main_fg};")

    # 更新代码高亮颜色
    if hasattr(self, "highlighter") and self.highlighter:
        highlighting_colors = theme.get("highlighting_colors", {})
        self.highlighter.update_highlighting_colors(highlighting_colors)

    # 文件树（QTreeView）背景色
    if hasattr(self, "tree"):
        tree_bg = theme.get("main_background", "#23272e")
        tree_fg = theme.get("main_foreground", "#dddddd")
        self.tree.setStyleSheet(f"QTreeView {{ background-color: {tree_bg}; color: {tree_fg}; border: none; }}")

    # 标签页（QTabWidget/QTabBar）背景色
    if hasattr(self, "tab_widget"):
        tab_bg = theme.get("main_background", "#23272e")
        tab_fg = theme.get("main_foreground", "#dddddd")
        self.tab_widget.setStyleSheet(
            f"QTabWidget::pane {{ background: {tab_bg}; }}"
            f"QTabBar {{ background: {tab_bg}; color: {tab_fg}; }}"
            f"QTabBar::tab {{ background: {tab_bg}; color: {tab_fg}; }}"
            f"QTabBar::tab:selected {{ background: #282c34; color: #fff; }}"
        )

    # 强制刷新界面
    self.update()

class HighlighterMixin:
    """用于更新高亮颜色的辅助类"""
    def update_highlighting_colors(self, colors):
        """更新高亮颜色"""
        for key, color in colors.items():
            if hasattr(self, f"{key}_color"):
                setattr(self, f"{key}_color", QColor(color))
        self.set_syntax_highlighting_rules()
        self.rehighlight()
