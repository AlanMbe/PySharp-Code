import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLoggingCategory
from ide.mainwindow import MainWindow
from ide.debugger import Debugger
from ide.lang_manager import LangManager
import os

# 初始化日志系统
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# 禁用 Qt 样式表警告
QLoggingCategory.setFilterRules("*.debug=false\n*.info=false")

# 禁用 log4cplus 警告
logging.getLogger("AdSyncNamespace").setLevel(logging.CRITICAL)

if __name__ == "__main__":
    # 禁用 Qt 未测试版本警告
    if sys.platform == "win32":
        os.environ["QT_LOGGING_RULES"] = "qt.*=false"

    app = QApplication(sys.argv)
    lang_manager = LangManager("ide/translations/translations.json", "zh")  # 初始化语言管理器
    debugger = Debugger()
    window = MainWindow(debugger=debugger)
    window.lang_manager = lang_manager  # 传递语言管理器
    # 不再调用 window.apply_theme_and_font
    window.show()
    sys.exit(app.exec())