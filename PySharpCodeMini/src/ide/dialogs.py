from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog
from PySide6.QtGui import QFontDatabase
import os

class SettingsDialog(QDialog):
    def __init__(self, lang_manager, parent=None):
        super().__init__(parent)
        self.lang_manager = lang_manager  # 确保 lang_manager 被正确传递
        self.setWindowTitle(self.lang_manager.t("Settings"))
        self.resize(300, 250)  # 调整窗口大小以容纳新按钮

        layout = QVBoxLayout()
        self.theme_label = QLabel(self.lang_manager.t("Theme"))
        layout.addWidget(self.theme_label)
        self.theme_box = QComboBox()
        self.theme_box.addItems(["Light", "Dark"])
        layout.addWidget(self.theme_box)

        self.font_label = QLabel(self.lang_manager.t("Font"))
        layout.addWidget(self.font_label)
        self.font_box = QComboBox()
        font_db = QFontDatabase()
        self.font_box.addItems(font_db.families())
        layout.addWidget(self.font_box)

        self.font_size_label = QLabel(self.lang_manager.t("Font Size"))
        layout.addWidget(self.font_size_label)
        self.font_size_box = QComboBox()
        self.font_size_box.addItems(["10", "12", "14", "16", "20", "24", "28"])
        layout.addWidget(self.font_size_box)

        # 主题文件路径映射
        self.theme_file_map = {"Light": None, "Dark": None}
        self.is_dark_mode = False  # 默认浅色

        # 添加切换深浅色按钮
        self.toggle_dark_btn = QPushButton("切换深浅色")
        self.toggle_dark_btn.clicked.connect(self.toggle_dark_mode)
        layout.addWidget(self.toggle_dark_btn)

        self.save_btn = QPushButton(self.lang_manager.t("Save"))
        self.save_btn.clicked.connect(self.accept)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    def import_theme(self):
        """导入主题 JSON 文件，只添加到下拉框但不自动切换主题"""
        theme_file, _ = QFileDialog.getOpenFileName(self, self.lang_manager.t("Select Theme File"), "", "JSON Files (*.json)")
        if theme_file:
            theme_name = os.path.splitext(os.path.basename(theme_file))[0]  # 提取主题名称
            if theme_name not in [self.theme_box.itemText(i) for i in range(self.theme_box.count())]:
                self.theme_box.addItem(theme_name)  # 动态添加主题到选择框
            self.theme_file_map[theme_name] = theme_file  # 记录路径
            # 不自动切换主题，只添加到下拉框

    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        # 立即预览切换效果
        theme_file = self.theme_file_map.get(self.theme_box.currentText())
        self.parent().apply_theme_and_font(theme_file=theme_file, is_dark_mode=self.is_dark_mode)

    def accept(self):
        """保存设置并应用主题"""
        selected_theme = self.theme_box.currentText()
        theme_file = self.theme_file_map.get(selected_theme)
        self.parent().apply_theme_and_font(theme_file=theme_file, is_dark_mode=self.is_dark_mode)
        self.parent().theme = selected_theme
        self.parent().font_name = self.font_box.currentText()
        self.parent().font_size = int(self.font_size_box.currentText())
        # 你可以考虑把 is_dark_mode 也保存到配置文件
        self.parent().is_dark_mode = self.is_dark_mode
        self.parent().save_project()
        super().accept()

    def retranslate_ui(self):
        """重新翻译界面"""
        t = self.lang_manager.t
        self.setWindowTitle(t("Settings"))
        self.theme_label.setText(t("Theme"))
        self.font_label.setText(t("Font"))
        self.font_size_label.setText(t("Font Size"))
        self.import_theme_btn.setText(t("Import Theme"))
        self.save_btn.setText(t("Save"))

class AboutDialog(QDialog):
    def __init__(self, lang_manager, parent=None):
        super().__init__(parent)
        self.lang_manager = lang_manager
        self.setWindowTitle(self.lang_manager.t("About"))
        self.resize(400, 300)
        layout = QVBoxLayout()

        self.app_name = QLabel(f"<h2>{self.lang_manager.t('PySharp Code IDE')}</h2>")
        self.author = QLabel(f"{self.lang_manager.t('Author')}: Alan mbe")
        self.version = QLabel(f"{self.lang_manager.t('Version')}: v3.0")
        self.description = QLabel(
            f"{self.lang_manager.t('A lightweight IDE supporting Python and C#')}\n"
            f"{self.lang_manager.t('With code highlighting, run, formatting, and file management.')}"
        )
        self.github = QLabel(f'<a href="https://github.com/你的项目链接">{self.lang_manager.t("GitHub 项目主页 / GitHub Project")}</a>')
        self.github.setOpenExternalLinks(True)

        layout.addWidget(self.app_name)
        layout.addWidget(self.author)
        layout.addWidget(self.version)
        layout.addWidget(self.description)
        layout.addWidget(self.github)

        self.close_btn = QPushButton(self.lang_manager.t("Close"))
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)

    def retranslate_ui(self):
        """重新翻译界面"""
        t = self.lang_manager.t
        self.setWindowTitle(t("About"))
        self.app_name.setText(f"<h2>{t('PySharp Code IDE')}</h2>")
        self.author.setText(f"{t('Author')}: Alan mbe")
        self.version.setText(f"{t('Version')}: v3.0")
        self.description.setText(
            f"{t('A lightweight IDE supporting Python and C#')}\n"
            f"{t('With code highlighting, run, formatting, and file management.')}"
        )
        self.github.setText(f'<a href="https://github.com/你的项目链接">{t("GitHub 项目主页 / GitHub Project")}</a>')
        self.close_btn.setText(t("Close"))

class HelpDialog(QDialog):
    def __init__(self, lang_manager, parent=None):
        super().__init__(parent)
        self.lang_manager = lang_manager
        self.setWindowTitle(self.lang_manager.t("Help"))
        self.resize(500, 400)
        layout = QVBoxLayout()

        self.title = QLabel(f"<h2>{self.lang_manager.t('User Guide')}</h2>")
        self.content = QLabel(f"{self.lang_manager.t('...（内容同原文件）...')}")
        self.content.setWordWrap(True)
        self.content.setOpenExternalLinks(True)

        layout.addWidget(self.title)
        layout.addWidget(self.content)

        self.close_btn = QPushButton(self.lang_manager.t("Close"))
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)

    def retranslate_ui(self):
        """重新翻译界面"""
        t = self.lang_manager.t
        self.setWindowTitle(t("Help"))
        self.title.setText(f"<h2>{t('User Guide')}</h2>")
        self.content.setText(f"{t('...（内容同原文件）...')}")
        self.close_btn.setText(t("Close"))