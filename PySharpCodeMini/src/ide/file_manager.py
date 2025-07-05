from PySide6.QtWidgets import QTreeView, QFileSystemModel
from PySide6.QtCore import QDir, Qt

def init_file_manager(self):
    """初始化文件管理器"""
    self.tree = QTreeView()
    self.model = QFileSystemModel()
    self.model.setRootPath(QDir.currentPath())  # 设置根路径为当前工作目录
    self.tree.setModel(self.model)
    self.tree.setRootIndex(self.model.index(QDir.currentPath()))  # 确保项目树显示当前工作目录内容
    self.tree.setHeaderHidden(False)  # 显示表头以提供更多信息
    self.tree.setSortingEnabled(True)  # 启用排序
    self.tree.sortByColumn(0, Qt.AscendingOrder)  # 默认按名称升序排序
    self.tree.setColumnWidth(0, 250)  # 调整列宽以适应文件名
    self.tree.clicked.connect(self.open_file_from_tree)  # 确保点击文件时可以打开
    self.main_splitter.addWidget(self.tree)

def open_file_from_tree(self, index):
    """从项目树中打开文件"""
    file_path = self.model.filePath(index)
    if file_path and QDir(file_path).exists():
        if QDir(file_path).isFile():
            self.load_file(file_path)
        else:
            self.tree.setRootIndex(self.model.index(file_path))  # 切换到选中的目录
