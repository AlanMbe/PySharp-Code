from PySide6.QtWidgets import QPlainTextEdit, QToolBar
from PySide6.QtGui import QAction

def init_debug_ui(self):
    """初始化调试界面"""
    self.debug_output = QPlainTextEdit()
    self.debug_output.setReadOnly(True)
    self.main_splitter.addWidget(self.debug_output)

    debug_toolbar = QToolBar("调试工具栏")
    start_debug_action = QAction("启动调试", self)
    start_debug_action.triggered.connect(self.start_debug)  # 调用 MainWindow 的方法
    debug_toolbar.addAction(start_debug_action)

    stop_debug_action = QAction("停止调试", self)
    stop_debug_action.triggered.connect(self.stop_debug)  # 调用 MainWindow 的方法
    debug_toolbar.addAction(stop_debug_action)

    self.addToolBar(debug_toolbar)
