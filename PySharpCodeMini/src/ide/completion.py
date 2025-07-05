from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt  # 修复导入错误

class CompletionPopup(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.ToolTip)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)

    def show_completions(self, completions, position):
        """显示补全项"""
        self.clear()
        for completion in completions:
            item = QListWidgetItem(completion)
            self.addItem(item)
        self.move(position)
        self.show()

    def insert_completion(self):
        """插入选中的补全项"""
        current_item = self.currentItem()
        if current_item:
            return current_item.text()
        return None
