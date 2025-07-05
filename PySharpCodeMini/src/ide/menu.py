from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction

def init_menu_bar(self):
    """初始化菜单栏"""
    menu_bar = self.menuBar()
    file_menu = QMenu("文件", self)

    new_action = QAction("新建", self)
    new_action.triggered.connect(self.new_file_action)
    file_menu.addAction(new_action)

    open_action = QAction("打开", self)
    open_action.triggered.connect(self.open_file_action)
    file_menu.addAction(open_action)

    save_action = QAction("保存", self)
    save_action.triggered.connect(self.save_file_action)
    file_menu.addAction(save_action)

    menu_bar.addMenu(file_menu)
