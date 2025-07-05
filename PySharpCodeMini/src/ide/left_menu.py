from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolButton
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

def init_left_menu(self):
    """初始化左侧菜单"""
    self.left_menu = QWidget()
    left_layout = QVBoxLayout(self.left_menu)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(10)

    # 添加按钮
    btn_project = QToolButton()
    btn_project.setIcon(QIcon())
    btn_project.setIconSize(QSize(32, 32))
    btn_project.setToolTip("项目树")
    left_layout.addWidget(btn_project)

    btn_settings = QToolButton()
    btn_settings.setIcon(QIcon())
    btn_settings.setIconSize(QSize(32, 32))
    btn_settings.setToolTip("设置")
    left_layout.addWidget(btn_settings)

    left_layout.addStretch()  # 添加弹性空间

    self.main_splitter.insertWidget(0, self.left_menu)  # 确保左菜单在主分割器的第一个位置
