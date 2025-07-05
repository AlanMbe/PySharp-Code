import os, json, subprocess, traceback, re, sys
from PySide6.QtWidgets import (
    QMainWindow, QTextEdit, QFileDialog, QPushButton, QVBoxLayout, QWidget, QTreeView,
    QFileSystemModel, QHBoxLayout, QSplitter, QMessageBox, QInputDialog, QMenu, 
    QToolButton, QLabel, QListWidget, QListWidgetItem, QFrame, QFormLayout, QSpinBox, 
    QCheckBox, QComboBox, QSlider, QProgressBar, QLineEdit, QPlainTextEdit, QToolBar, QDialog, QDialogButtonBox, QApplication, QCompleter, QGroupBox, QTabWidget, QTabBar
)
from PySide6.QtCore import Qt, QDir, QSize, QThread, Signal, QPoint, QMimeData, QProcess, QTranslator, QEvent, QTimer, QRect
from PySide6.QtGui import QFont, QAction, QKeySequence, QIcon, QDrag, QPainter, QColor, QCursor, QTextCursor, QTextFormat
from .filemanager import FileManager
from .highlighter import PythonHighlighter, CSharpHighlighter
from .dialogs import SettingsDialog, AboutDialog, HelpDialog
from .lang_manager import LangManager
import shutil
import ctypes

class CodeRunnerThread(QThread):
    output_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, command, parent=None):
        super().__init__(parent)
        self.command = command
        self.process = None

    def run(self):
        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            stdout, stderr = self.process.communicate()
            if stdout:
                self.output_signal.emit(stdout)
            if stderr:
                self.error_signal.emit(stderr)
        except Exception as e:
            self.error_signal.emit(f"运行时发生异常：\n{e}")

    def terminate(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
        super().terminate()

class DraggableListItem(QListWidgetItem):
    def __init__(self, text, widget_type):
        super().__init__(text)
        self.widget_type = widget_type

class Canvas(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: white; border: 1px solid gray;")
        self.grid_size = 10
        self.widgets = []
        self.parent = parent  # 引用父窗口以访问属性面板

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QColor(230, 230, 230))
        for x in range(0, self.width(), self.grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), self.grid_size):
            painter.drawLine(0, y, self.width(), y)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        widget_type = event.mimeData().text()
        pos = self.snap_to_grid(event.position().toPoint())
        self.add_widget(widget_type, pos)

    def snap_to_grid(self, point):
        return QPoint(
            round(point.x() / self.grid_size) * self.grid_size,
            round(point.y() / self.grid_size) * self.grid_size
        )

    def add_widget(self, widget_type, pos):
        widget = None
        if widget_type == "QPushButton":
            widget = QPushButton("按钮", self)
        elif widget_type == "QLabel":
            widget = QLabel("标签", self)
        elif widget_type == "QLineEdit":
            widget = QLineEdit(self)
        elif widget_type == "QCheckBox":
            widget = QCheckBox("勾选项", self)
        elif widget_type == "QComboBox":
            widget = QComboBox(self)
            widget.addItems(["选项1", "选项2", "选项3"])
        elif widget_type == "QSlider":
            widget = QSlider(Qt.Horizontal, self)
        elif widget_type == "QProgressBar":
            widget = QProgressBar(self)
        elif widget_type == "QTextEdit":
            widget = QTextEdit(self)

        if widget:
            widget.setGeometry(pos.x(), pos.y(), 120, 30 if not isinstance(widget, QTextEdit) else 80)
            widget.show()
            widget.mousePressEvent = lambda event, w=widget: self.select_widget(w)  # 绑定选择事件
            self.widgets.append({
                "type": widget_type,
                "x": pos.x(),
                "y": pos.y(),
                "w": 120,
                "h": 30 if not isinstance(widget, QTextEdit) else 80,
                "value": widget.text() if hasattr(widget, "text") else None,
                "events": {}  # 新增：事件绑定字典
            })

    def select_widget(self, widget):
        """选择控件并更新属性面板"""
        self.parent.prop_panel.set_target(widget)

    def export_layout(self):
        return self.widgets

class PropertyPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setStyleSheet("background-color: #f0f0f0; border: 1px solid gray;")
        self.layout = QFormLayout(self)
        self.target = None

        # 添加文本、大小、位置和其他参数的控件
        self.text_edit = QLineEdit()
        self.x_spin = QSpinBox()
        self.y_spin = QSpinBox()
        self.w_spin = QSpinBox()
        self.h_spin = QSpinBox()
        self.font_size_spin = QSpinBox()
        self.color_edit = QLineEdit()

        for spin in [self.x_spin, self.y_spin, self.w_spin, self.h_spin, self.font_size_spin]:
            spin.setRange(0, 2000)

        self.layout.addRow("文本:", self.text_edit)
        self.layout.addRow("X:", self.x_spin)
        self.layout.addRow("Y:", self.y_spin)
        self.layout.addRow("宽:", self.w_spin)
        self.layout.addRow("高:", self.h_spin)
        self.layout.addRow("字体大小:", self.font_size_spin)
        self.layout.addRow("颜色:", self.color_edit)

        # 事件绑定面板
        self.event_group = QGroupBox("事件绑定")
        self.event_layout = QFormLayout()
        self.event_group.setLayout(self.event_layout)
        self.clicked_event_edit = QLineEdit()
        self.event_layout.addRow("clicked:", self.clicked_event_edit)
        self.clicked_event_edit.textChanged.connect(self.apply_event_changes)
        self.layout.addRow(self.event_group)

        # 绑定事件
        self.text_edit.textChanged.connect(self.apply_changes)
        self.x_spin.valueChanged.connect(self.apply_changes)
        self.y_spin.valueChanged.connect(self.apply_changes)
        self.w_spin.valueChanged.connect(self.apply_changes)
        self.h_spin.valueChanged.connect(self.apply_changes)
        self.font_size_spin.valueChanged.connect(self.apply_changes)
        self.color_edit.textChanged.connect(self.apply_changes)

    def set_target(self, widget):
        """设置当前选中的控件"""
        self.target = widget
        geo = widget.geometry()

        # 更新属性面板的值
        text = ""
        if hasattr(widget, "text"):
            text = widget.text()
        elif isinstance(widget, QTextEdit):
            text = widget.toPlainText()

        self.text_edit.setText(text)
        self.x_spin.setValue(geo.x())
        self.y_spin.setValue(geo.y())
        self.w_spin.setValue(geo.width())
        self.h_spin.setValue(geo.height())
        self.font_size_spin.setValue(widget.font().pointSize() if widget.font() else 12)
        self.color_edit.setText(widget.styleSheet().split("color:")[-1].strip(";") if "color:" in widget.styleSheet() else "")

        # 事件绑定区
        events = getattr(widget, "events", {})
        self.clicked_event_edit.setText(events.get("clicked", ""))

    def apply_event_changes(self):
        if not self.target:
            return
        if not hasattr(self.target, "events"):
            self.target.events = {}
        self.target.events["clicked"] = self.clicked_event_edit.text()
        # 同步到Canvas.widgets
        for w in self.parent.canvas.widgets:
            # 通过位置和类型唯一定位
            if hasattr(self.target, "geometry") and w["type"] == self.target.__class__.__name__:
                geo = self.target.geometry()
                if w["x"] == geo.x() and w["y"] == geo.y():
                    w["events"] = getattr(self.target, "events", {})

    def apply_changes(self):
        """将属性面板的值应用到控件"""
        if not self.target:
            return
        # 更新控件的几何属性
        self.target.setGeometry(self.x_spin.value(), self.y_spin.value(),
                                 self.w_spin.value(), self.h_spin.value())
        # 更新控件的文本属性
        if hasattr(self.target, "setText"):
            self.target.setText(self.text_edit.text())
        elif isinstance(self.target, QTextEdit):
            self.target.setPlainText(self.text_edit.text())
        # 更新字体大小
        font = self.target.font() or QFont()
        font.setPointSize(self.font_size_spin.value())
        self.target.setFont(font)
        # 更新颜色
        color = self.color_edit.text.strip()
        if color:
            self.target.setStyleSheet(f"color: {color};")
        else:
            self.target.setStyleSheet("")  # 清除颜色样式
        # 事件同步
        self.apply_event_changes()

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

    def mousePressEvent(self, event):
        block_height = self.codeEditor.fontMetrics().height()
        y = event.pos().y()
        block_number = y // block_height + self.codeEditor.firstVisibleBlock().blockNumber()
        line = block_number + 1
        if line in self.codeEditor.breakpoints:
            self.codeEditor.breakpoints.remove(line)
        else:
            self.codeEditor.breakpoints.add(line)
        self.codeEditor.lineNumberArea.update()

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        # self.breakpoints = set()  # 断点集合，已去除

    def lineNumberAreaWidth(self):
        digits = len(str(self.blockCount()))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(245, 245, 245))
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.gray)
                painter.drawText(14, top, self.lineNumberArea.width() - 16, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(232, 242, 254)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

class DesignerWindow(QMainWindow):
    def __init__(self, lang_manager):
        super().__init__()
        self.lang_manager = lang_manager
        self.setWindowTitle(self.lang_manager.t("Widget Designer"))
        self.resize(1000, 600)

        central = QWidget()
        layout = QHBoxLayout(central)

        self.toolbox = QListWidget()
        self.toolbox.setFixedWidth(140)
        widgets = [
            ("按钮", "QPushButton"),
            ("标签", "QLabel"),
            ("输入框", "QLineEdit"),
            ("复选框", "QCheckBox")
        ]
        for name, wtype in widgets:
            self.toolbox.addItem(DraggableListItem(name, wtype))

        self.toolbox.itemPressed.connect(self.start_drag)

        self.canvas = Canvas(self)
        self.prop_panel = PropertyPanel(self)

        layout.addWidget(self.toolbox)
        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.prop_panel)
        self.setCentralWidget(central)

        self.init_menu()
        self.init_toolbar()

    def start_drag(self, item):
        """开始拖拽控件"""
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(item.widget_type)
        drag.setMimeData(mime)
        drag.exec(Qt.MoveAction)

    def init_menu(self):
        """初始化菜单栏"""
        t = self.lang_manager.t
        menu_bar = self.menuBar()
        menu_bar.clear()
        file_menu = QMenu(t("File"), self)
        export_pyside_action = QAction(t("Export to PySide"), self)
        export_pyside_action.triggered.connect(lambda: self.export_layout("pyside"))
        file_menu.addAction(export_pyside_action)
        export_tkinter_action = QAction(t("Export to Tkinter"), self)
        export_tkinter_action.triggered.connect(lambda: self.export_layout("tkinter"))
        file_menu.addAction(export_tkinter_action)
        export_winform_action = QAction(t("Export to WinForms"), self)
        export_winform_action.triggered.connect(lambda: self.export_layout("winform"))
        file_menu.addAction(export_winform_action)
        menu_bar.addMenu(file_menu)

    def init_toolbar(self):
        """初始化工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet("QToolBar { background: transparent; border: none; }")

        export_button = QToolButton()
        export_button.setIcon(QIcon(r".\icons\export.svg"))
        export_button.setToolTip("导出布局")
        export_button.clicked.connect(self.show_export_menu)

        toolbar.addWidget(export_button)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

    def show_export_menu(self):
        """显示导出菜单"""
        menu = QMenu()
        t = self.lang_manager.t
        menu.addAction(t("Export to PySide"), lambda: self.export_layout("pyside"))
        menu.addAction(t("Export to Tkinter"), lambda: self.export_layout("tkinter"))
        menu.addAction(t("Export to WinForms"), lambda: self.export_layout("winform"))
        menu.exec_(QCursor.pos())

    def export_layout(self, framework):
        layout = self.canvas.export_layout()
        code = self.generate_code(layout, framework)
        path, _ = QFileDialog.getSaveFileName(self, f"{self.lang_manager.t('Export to')} {framework}", f"layout_{framework}.py", "Python Files (*.py)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(code)
                QMessageBox.information(self, self.lang_manager.t("Export Successful"), f"{self.lang_manager.t('Layout successfully exported to')} {framework} format!")
            except Exception as e:
                QMessageBox.warning(self, self.lang_manager.t("Export Failed"), str(e))

    def generate_code(self, layout, framework):
        if framework == "pyside":
            return self.generate_pyside_code(layout)
        elif framework == "tkinter":
            return self.generate_tkinter_code(layout)
        elif framework == "winform":
            return self.generate_winform_code(layout)

    def generate_pyside_code(self, layout):
        code = "from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QCheckBox, QComboBox, QSlider, QProgressBar, QTextEdit\n"
        code += "from PySide6.QtCore import QRect\n\n"
        code += "class MainWindow(QWidget):\n"
        code += "    def __init__(self):\n"
        code += "        super().__init__()\n"
        code += "        self.setWindowTitle('PySide Layout')\n"
        code += "        self.setGeometry(100, 100, 800, 600)\n\n"
        for widget in layout:
            code += f"        self.{widget['type'].lower()} = {widget['type']}(self)\n"
            code += f"        self.{widget['type'].lower()}.setGeometry(QRect({widget['x']}, {widget['y']}, {widget['w']}, {widget['h']}))\n"
            if widget["value"]:
                if widget["type"] in ["QPushButton", "QLabel", "QLineEdit", "QTextEdit"]:
                    code += f"        self.{widget['type'].lower()}.setText('{widget['value']}')\n"
                elif widget["type"] == "QComboBox":
                    code += f"        self.{widget['type'].lower()}.setCurrentIndex({widget['value']})\n"
                elif widget["type"] in ["QSlider", "QProgressBar"]:
                    code += f"        self.{widget['type'].lower()}.setValue({widget['value']})\n"
        code += "\nif __name__ == '__main__':\n"
        code += "    app = QApplication([])\n"
        code += "    win = MainWindow()\n"
        code += "    win.show()\n"
        code += "    app.exec()\n"
        return code

    def generate_tkinter_code(self, layout):
        code = "import tkinter as tk\n\n"
        code += "class MainWindow(tk.Tk):\n"
        code += "    def __init__(self):\n"
        code += "        super().__init__()\n"
        code += "        self.title('Tkinter Layout')\n"
        code += "        self.geometry('800x600')\n\n"
        for widget in layout:
            if widget["type"] == "QPushButton":
                code += f"        self.{widget['type'].lower()} = tk.Button(self, text='{widget['value']}')\n"
            elif widget["type"] == "QLabel":
                code += f"        self.{widget['type'].lower()} = tk.Label(self, text='{widget['value']}')\n"
            elif widget["type"] == "QLineEdit":
                code += f"        self.{widget['type'].lower()} = tk.Entry(self)\n"
                code += f"        self.{widget['type'].lower()}.insert(0, '{widget['value']}')\n"
            elif widget["type"] == "QCheckBox":
                code += f"        self.{widget['type'].lower()} = tk.Checkbutton(self, text='{widget['value']}')\n"
            elif widget["type"] == "QComboBox":
                code += f"        self.{widget['type'].lower()} = tk.OptionMenu(self, tk.StringVar(value='{widget['value']}'), '选项1', '选项2', '选项3')\n"
            elif widget["type"] == "QSlider":
                code += f"        self.{widget['type'].lower()} = tk.Scale(self, from_=0, to=100, orient='horizontal')\n"
                code += f"        self.{widget['type'].lower()}.set({widget['value']})\n"
            elif widget["type"] == "QProgressBar":
                code += f"        self.{widget['type'].lower()} = tk.Label(self, text='进度: {widget['value']}%')\n"
            elif widget["type"] == "QTextEdit":
                code += f"        self.{widget['type'].lower()} = tk.Text(self, height=4, width=30)\n"
                code += f"        self.{widget['type'].lower()}.insert('1.0', '{widget['value']}')\n"
            code += f"        self.{widget['type'].lower()}.place(x={widget['x']}, y={widget['y']}, width={widget['w']}, height={widget['h']})\n"
        code += "\nif __name__ == '__main__':\n"
        code += "    win = MainWindow()\n"
        code += "    win.mainloop()\n"
        return code

    def generate_winform_code(self, layout):
        code = "using System;\nusing System.Windows.Forms;\n\n"
        code += "public class MainForm : Form\n"
        code += "{\n"
        code += "    public MainForm()\n"
        code += "    {\n"
        code += "        this.Text = \"WinForms Layout\";\n"
        code += "        this.ClientSize = new System.Drawing.Size(800, 600);\n\n"
        for widget in layout:
            code += f"        var {widget['type'].lower()} = new {widget['type']}();\n"
            code += f"        {widget['type'].lower()}.SetBounds({widget['x']}, {widget['y']}, {widget['w']}, {widget['h']});\n"
            if widget["value"]:
                if widget["type"] in ["Button", "Label", "TextBox"]:
                    code += f"        {widget['type'].lower()}.Text = \"{widget['value']}\";\n"
                elif widget["type"] == "ComboBox":
                    code += f"        {widget['type'].lower()}.SelectedIndex = {widget['value']};\n"
                elif widget["type"] in ["TrackBar", "ProgressBar"]:
                    code += f"        {widget['type'].lower()}.Value = {widget['value']};\n"
            code += f"        this.Controls.Add({widget['type'].lower()});\n\n"
        code += "    }\n"
        code += "}\n\n"
        code += "public static class Program\n"
        code += "{\n"
        code += "    [STAThread]\n"
        code += "    public static void Main()\n"
        code += "    {\n"
        code += "        Application.EnableVisualStyles();\n"
        code += "        Application.SetCompatibleTextRenderingDefault(false);\n"
        code += "        Application.Run(new MainForm());\n"
        code += "    }\n"
        code += "}\n"
        return code

    def retranslate_ui(self):
        """重新翻译控件设计器界面"""
        t = self.lang_manager.t
        self.setWindowTitle(t("Widget Designer"))
        self.toolbox.clear()
        widgets = [
            (t("Button"), "QPushButton"),
            (t("Label"), "QLabel"),
            (t("Input Box"), "QLineEdit"),
            (t("Checkbox"), "QCheckBox"),
            (t("Dropdown"), "QComboBox"),
            (t("Slider"), "QSlider"),
            (t("Progress Bar"), "QProgressBar"),
            (t("Multiline Text"), "QTextEdit")
        ]
        for name, wtype in widgets:
            self.toolbox.addItem(DraggableListItem(name, wtype))
        self.init_menu()

class MainWindow(QMainWindow):
    def __init__(self, debugger):
        super().__init__()
        self.debugger = debugger
        self.lang_manager = LangManager("ide/translations/translations.json", "zh")
        self.project_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "project.json")
        self.setWindowTitle(self.lang_manager.t("PySharp Code"))
        self.theme = 'Light'
        self.font_name = 'JetBrains Mono'
        self.font_size = 12
        self.scale_factor = 1.0
        base_dir = os.path.abspath(os.path.dirname(__file__))
        icon_dir = os.path.join(base_dir, "icons")

        # 多标签页编辑器
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.open_files = []  # 跟踪每个标签的文件路径
        self.current_file = None  # 新增：同步当前文件
        self.add_new_tab()  # 此时还没有popup

        # 美化标签页关闭按钮
        # 移除QSS中的image: url(icons/close.svg);，改为用QIcon设置关闭按钮图标
        self.tab_widget.setStyleSheet('''
QTabBar::close-button {
    subcontrol-position: right;
    min-width: 22px;
    min-height: 22px;
    font-size: 18px;
    color: #888;
    border-radius: 11px;
    background: transparent;
}
QTabBar::close-button::hover {
    background: #e74c3c;
    color: white;
}
QTabBar::close-button::pressed {
    background: #c0392b;
    color: white;
}
''')
        # 设置关闭按钮图标
        close_icon = QIcon(os.path.join(icon_dir, "close.svg"))
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setDocumentMode(True)
        tab_bar.setTabsClosable(True)
        tab_bar.setMovable(True)
        # 动态设置每个tab的关闭按钮图标
        def set_close_icon(index):
            btn = tab_bar.tabButton(index, QTabBar.RightSide)
            if btn and hasattr(btn, 'setIcon'):
                btn.setIcon(close_icon)
        for i in range(tab_bar.count()):
            set_close_icon(i)
        self.tab_widget.tabBar().tabCloseRequested.connect(lambda idx: set_close_icon(idx))

        self.terminal_widget = self.init_terminal()
        self.status_bar = self.statusBar()
        self.log_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "error.log")
        self._skip_auto_indent = False
        self.init_layout()  # 只负责组装splitter
        self.init_menu_bar()
        self.init_file_manager()
        self.apply_theme_and_font()
        self.init_run_button(icon_dir)
        self.load_project()
        self.init_version_selector()
        self.init_debug_toolbar()
        self.debug_toolbar.hide()  # 初始化时隐藏调试工具栏

    def add_new_tab(self, file_path=None, content=""):
        editor = CodeEditor()
        editor.setPlaceholderText("代码编辑区")
        editor.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))
        editor.setStyleSheet("QTextEdit { background-color: #f9f9f9; }")
        editor.installEventFilter(self)
        if content:
            editor.setPlainText(content)
        if file_path and file_path.endswith('.py'):
            from .highlighter import PythonHighlighter
            editor.highlighter = PythonHighlighter(editor.document(), dark_mode=("Dark" in self.theme))
        elif file_path and file_path.endswith('.cs'):
            from .highlighter import CSharpHighlighter
            editor.highlighter = CSharpHighlighter(editor.document(), dark_mode=("Dark" in self.theme))
        else:
            editor.highlighter = None
        tab_name = os.path.basename(file_path) if file_path else "未命名"
        self.tab_widget.addTab(editor, tab_name)
        self.tab_widget.setCurrentWidget(editor)
        if file_path:
            self.open_files.append(file_path)
        else:
            self.open_files.append(None)
        self.current_file = file_path  # 新增：同步当前文件
        # 自定义关闭按钮
        tab_bar = self.tab_widget.tabBar()
        idx = self.tab_widget.indexOf(editor)
        # 隐藏原生关闭按钮
        tab_bar.setTabButton(idx, QTabBar.RightSide, None)
        # 添加自定义QToolButton
        from PySide6.QtWidgets import QToolButton
        icon_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons")
        close_icon = QIcon(os.path.join(icon_dir, "close.svg"))
        close_btn = QToolButton()
        close_btn.setIcon(close_icon)
        close_btn.setIconSize(QSize(18, 18))
        close_btn.setStyleSheet('''
            QToolButton {
                border: none;
                background: transparent;
                min-width: 22px;
                min-height: 22px;
                border-radius: 11px;
            }
            QToolButton:hover {
                background: #e74c3c;
            }
            QToolButton:pressed {
                background: #c0392b;
            }
        ''')
        def close_tab():
            self.close_tab(idx)
        close_btn.clicked.connect(close_tab)
        tab_bar.setTabButton(idx, QTabBar.RightSide, close_btn)
        # 不再自定义QToolButton关闭按钮，完全用QTabWidget自带的关闭按钮

    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        self.open_files.pop(index)
        if self.tab_widget.count() == 0:
            self.add_new_tab()

    def on_tab_changed(self, index):
        if 0 <= index < len(self.open_files):
            self.current_file = self.open_files[index]
        else:
            self.current_file = None
        # 可在此处切换高亮、补全等

    def current_editor(self):
        try:
            if hasattr(self, "tab_widget") and self.tab_widget:
                return self.tab_widget.currentWidget()
            return None
        except RuntimeError:
            return None

    def new_file_action(self):
        self.add_new_tab()

    def open_file_action(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开文件", "", "所有文件 (*.*)")
        if path:
            # 路径自动转换成长路径
            path = self.get_long_path_name(path)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.add_new_tab(file_path=path, content=content)

    def save_file_action(self):
        index = self.tab_widget.currentIndex()
        file_path = self.open_files[index]
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "所有文件 (*.*)")
            if not file_path:
                return
            self.open_files[index] = file_path
            self.tab_widget.setTabText(index, os.path.basename(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.current_editor().toPlainText())
        QMessageBox.information(self, "保存成功", f"文件已保存到 {file_path}")

    def load_file(self, path):
        # 路径自动转换成长路径
        path = self.get_long_path_name(path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.add_new_tab(file_path=path, content=content)

    def get_installed_python_versions(self):
        """获取本机已安装的 Python 版本列表"""
        try:
            result = subprocess.run(['py', '-0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            lines = result.stdout.splitlines()
            versions = []
            for line in lines:
                line = line.strip()
                if line.startswith('-V:'):
                    ver = line.split()[0][3:]
                    versions.append(ver)
            return ['默认（当前系统）'] + versions
        except Exception as e:
            print(f"无法获取 Python 版本：{e}")
            return ['默认（当前系统）']

    def get_installed_dotnet_versions(self):
        """只获取本机已安装的 .NET Desktop Runtime 版本"""
        versions = []
        try:
            output = subprocess.check_output("dotnet --list-runtimes", shell=True, text=True, encoding="utf-8", errors="ignore")
            for line in output.splitlines():
                if line.startswith("Microsoft.WindowsDesktop.App"):
                    ver = line.split()[1]
                    versions.append(ver)
        except Exception as e:
            print(f"Failed to get .NET Desktop Runtime versions: {e}")
        return versions or ["默认"]

    def init_version_selector(self):
        """初始化右下角的版本选择器"""
        version_frame = QFrame(self)
        version_layout = QHBoxLayout(version_frame)
        version_layout.setContentsMargins(5, 5, 5, 5)

        python_label = QLabel("Python版本：", self)
        self.python_version_combo = QComboBox(self)
        self.python_version_combo.addItems(self.get_installed_python_versions())
        version_layout.addWidget(python_label)
        version_layout.addWidget(self.python_version_combo)

        # 添加 .NET 版本选择器
        dotnet_label = QLabel(".NET版本：", self)
        self.dotnet_version_combo = QComboBox(self)
        self.dotnet_version_combo.addItems(self.get_installed_dotnet_versions())
        version_layout.addWidget(dotnet_label)
        version_layout.addWidget(self.dotnet_version_combo)

        self.statusBar().addPermanentWidget(version_frame)

    def load_project(self):
        """加载项目配置"""
        try:
            # 确保在打包后可以找到 project.json 文件
            project_file = os.path.join(os.path.dirname(sys.argv[0]), "project.json")
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.theme = data.get('theme', 'Light')
                self.font_name = data.get('font_name', 'JetBrains Mono')
                self.font_size = data.get('font_size', 12)
                last_directory = data.get('last_directory', QDir.currentPath())
                last_file = data.get('last_file', None)

                # 应用主题和字体
                self.apply_theme_and_font()

                # 设置文件树的根目录
                self.tree.setRootIndex(self.model.index(last_directory))

                # 打开上次编辑的文件
                if last_file and os.path.isfile(last_file):
                    self.load_file(last_file)
        except FileNotFoundError:
            # 如果配置文件不存在，使用默认值
            self.theme = 'Light'
            self.font_name = 'JetBrains Mono'
            self.font_size = 12

    def save_project(self):
        """保存项目配置"""
        try:
            # 确保在打包后可以保存到 project.json 文件
            project_file = os.path.join(os.path.dirname(sys.argv[0]), "project.json")
            data = {
                'theme': self.theme,
                'font_name': self.font_name,
                'font_size': self.font_size,
                'last_directory': self.tree.model().filePath(self.tree.rootIndex()),
                'last_file': getattr(self, 'current_file', None)
            }
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"保存项目配置失败：{e}")

    def closeEvent(self, event):
        """确保关闭窗口时保存项目配置"""
        self.save_project()
        if hasattr(self, 'process') and self.process.state() == QProcess.Running:
            self.process.kill()  # 立即终止进程
        event.accept()

    def keyPressEvent(self, event):
        """重写键盘事件以支持缩放逻辑和补全框导航"""
        if event.modifiers() == Qt.ControlModifier:
            if event.key() in (Qt.Key_Plus, Qt.Key_Equal):  # 支持 Ctrl+= 触发放大
                self.zoom_in()
                return
            elif event.key() == Qt.Key_Minus:
                self.zoom_out()
                return
        if self.popup.isVisible():
            if event.key() == Qt.Key_Down:
                # 向下导航补全框
                self.popup.setCurrentRow((self.popup.currentRow() + 1) % self.popup.count())
                return
            elif event.key() == Qt.Key_Up:
                # 向上导航补全框
                self.popup.setCurrentRow((self.popup.currentRow() - 1) % self.popup.count())
                return
            elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
                # 插入选中的补全项
                current_item = self.popup.currentItem()
                if current_item:
                    self.insert_completion(current_item.text())
                    self.popup.hide()
                    return
            elif event.key() == Qt.Key_Escape:
                # 按下 Esc 键关闭补全框
                self.popup.hide()
                return
        super().keyPressEvent(event)

    def zoom_in(self):
        """放大字体和图标"""
        if self.scale_factor < 3.0:  # 最大缩放因子为 3.0
            self.scale_factor += 0.1
            self.apply_zoom()

    def zoom_out(self):
        """缩小字体和图标"""
        if self.scale_factor > 0.5:  # 最小缩放因子为 0.5
            self.scale_factor -= 0.1
            self.apply_zoom()

    def apply_zoom(self):
        """应用缩放到字体和图标"""
        font = QFont(self.font_name, max(1, int(self.font_size * self.scale_factor)))
        font.setStyleStrategy(QFont.PreferAntialias)  # 优化字体渲染
        self.current_editor().setFont(font)
        self.terminal_output.setFont(font)
        self.terminal_input.setFont(font)
        self.tree.setFont(font)

        # 调整左侧菜单图标大小
        icon_size = max(16, int(64 * self.scale_factor))  # 确保图标大小不小于 16
        for btn in self.left_menu.findChildren(QLabel):
            icon = QIcon(btn.pixmap().cacheKey())
            btn.setPixmap(icon.pixmap(icon_size, icon_size))

        # 调整属性面板字体
        if hasattr(self, "designer_window") and self.designer_window:
            self.designer_window.prop_panel.setFont(font)

        # 强制刷新界面
        self.updateGeometry()

        # 主题切换后同步高亮器配色
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            highlighter = getattr(editor, 'highlighter', None)
            if highlighter and hasattr(highlighter, 'set_dark_mode'):
                highlighter.set_dark_mode("Dark" in self.theme)
        if hasattr(self, 'highlighter') and self.highlighter and hasattr(self.highlighter, 'set_dark_mode'):
            self.highlighter.set_dark_mode("Dark" in self.theme)

    def insert_completion(self, text):
        """插入选中的补全项到编辑器"""
        cursor = self.current_editor().textCursor()
        cursor.select(QTextCursor.WordUnderCursor)  # 选中当前单词
        cursor.insertText(text)
        self.current_editor().setTextCursor(cursor)

    def eventFilter(self, obj, event):
        # 防止 tab_widget 已被销毁时报错
        if not hasattr(self, "tab_widget") or self.tab_widget is None:
            return False
        if obj == self.current_editor() and event.type() == QEvent.KeyPress:
            key = event.key()
            # --- 智能 Tab 逻辑 ---
            if key == Qt.Key_Tab:
                # 获取光标前的内容
                cursor = self.current_editor().textCursor()
                pos = cursor.position()
                doc_text = self.current_editor().toPlainText()
                if pos > 0:
                    prev_char = doc_text[pos - 1]
                    if prev_char.isalpha():  # 是字母
                        if self.completion_popup and self.completion_popup.isVisible():
                            self.completion_popup.insert_completion()
                        return True
                    elif prev_char.isspace():  # 是空格
                        cursor.insertText(" " * 4)
                        return True
                else:
                    cursor.insertText(" " * 4)
                    return True
            elif key == Qt.Key_Backspace:
                # Backspace：智能删除缩进
                cursor = self.current_editor().textCursor()
                block_text = cursor.block().text()
                pos_in_block = cursor.position() - cursor.block().position()
                if pos_in_block >= 4 and block_text[pos_in_block - 4:pos_in_block] == " " * 4:
                    cursor.movePosition(cursor.Left, cursor.KeepAnchor, 4)
                    cursor.removeSelectedText()
                    return True

            # Enter 自动缩进
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                cursor = self.current_editor().textCursor()
                current_line = cursor.block().text()
                leading_spaces = len(current_line) - len(current_line.lstrip())
                indent = " " * leading_spaces
                if current_line.rstrip().endswith(":"):
                    indent += " " * 4
                cursor.insertText("\n" + indent)
                return True

            # 动态显示补全框
            text = event.text()
            if text.isalnum():  # 输入的是字母或数字
                cursor = self.current_editor().textCursor()
                block_text = cursor.block().text()
                pos_in_block = cursor.position() - cursor.block().position()
                current_prefix = block_text[:pos_in_block].split()[-1] if block_text.strip() else ""

                # 调用 CompletionPopup 的 generate_completions 方法
                completions = self.completion_popup.generate_completions(current_prefix)
                if completions:
                    position = self.current_editor().mapToGlobal(self.current_editor().cursorRect().bottomRight())
                    self.completion_popup.show_completions(completions, position)
                    self.completion_popup.setCurrentRow(0)  # 默认选中第一项
                else:
                    self.completion_popup.hide()
            elif key in (Qt.Key_Escape, Qt.Key_Return):
                self.completion_popup.hide()
        return super().eventFilter(obj, event)

    def apply_language(self):
        """应用语言到整个界面"""
        self.retranslate_ui()

    def retranslate_ui(self):
        """重新翻译整个界面"""
        t = self.lang_manager.t
        # 主窗口标题
        self.setWindowTitle(t("PySharp Code"))

        # 菜单栏
        self.init_menu_bar()

        # 左侧按钮 ToolTips
        for btn in self.left_menu.findChildren(QLabel):
            tooltip_map = {
                "project": t("Project Tree"),
                "template": t("File Templates"),
                "settings": t("Settings"),
                "debug": t("Debug"),
                "designer": t("Widget Designer")
            }
            icon_name = btn.toolTip().lower().replace(" ", "").replace("-", "")
            for key, value in tooltip_map.items():
                if key in icon_name:
                    btn.setToolTip(value)

        # 编辑器占位符
        self.current_editor().setPlaceholderText(t("Code Editor Area"))

        # 终端输入提示
        self.terminal_input.setPlaceholderText(t("Type a command and press Enter"))

        # 状态栏
        self.status_bar.showMessage(t("Language switched successfully"), 3000)

        # 同步刷新对话框
        if hasattr(self, "settings_dialog"):
            self.settings_dialog.lang_manager = self.lang_manager
            self.settings_dialog.retranslate_ui()
        if hasattr(self, "about_dialog"):
            self.about_dialog.lang_manager = self.lang_manager
            self.about_dialog.retranslate_ui()
        if hasattr(self, "help_dialog"):
            self.help_dialog.lang_manager = self.lang_manager
            self.help_dialog.retranslate_ui()

    def toggle_language(self):
        """切换语言"""
        new_lang = "en" if self.lang_manager.lang == "zh" else "zh"
        self.lang_manager.set_lang(new_lang)
        self.retranslate_ui()

    def start_debug(self):
        """开始调试，自动区分Python和C#"""
        self.debug_toolbar.show()  # 显示调试工具栏
        if not self.current_file:
            QMessageBox.warning(self, "调试", "未打开任何文件！")
            return
        if self.current_file.endswith('.py'):
            self.start_python_debug()
        elif self.current_file.endswith('.cs'):
            self.start_csharp_debug()
        else:
            QMessageBox.warning(self, "调试", "仅支持.py和.cs文件调试！")

    def start_python_debug(self):
        """用PDB调试当前Python文件，自动设置断点"""
        file_path = self.current_file
        breakpoints = sorted(getattr(self.current_editor(), 'breakpoints', set()))
        if not os.path.isfile(file_path):
            QMessageBox.warning(self, "调试", "文件不存在！")
            return
        # 路径自动转换成长路径
        file_path = self.get_long_path_name(file_path)
        # 构造pdb命令脚本
        pdb_cmds = "".join([f"break {file_path}:{b}\n" for b in breakpoints]) + "continue\n"
        script = f"import pdb; pdb.run('exec(open(\\'{file_path}\\').read()', globals())"
        cmd = [sys.executable, '-m', 'pdb', file_path]
        # 用QProcess启动pdb
        self.process = QProcess(self)
        self.process.setProgram(sys.executable)
        self.process.setArguments(['-m', 'pdb', file_path])
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_terminal_output)
        self.process.readyReadStandardError.connect(self.read_terminal_output)
        self.process.start()
        # 自动输入断点命令
        QTimer.singleShot(500, lambda: self.process.write(pdb_cmds.encode('utf-8')))
        self.status_bar.showMessage("Python调试已启动")

    def start_csharp_debug(self):
        """用dotnet CLI调试C#，提示用户插入Debugger.Break()"""
        file_path = self.current_file
        QMessageBox.information(self, "C#调试提示", "请在需要断点的地方插入System.Diagnostics.Debugger.Break();\n然后点击继续运行。\n如需源码级调试，请用VS或vsdbg。")
        # 启动dotnet run
        project_dir = os.path.dirname(file_path)
        csproj_path = next((os.path.join(project_dir, f) for f in os.listdir(project_dir) if f.endswith('.csproj')), None)
        if csproj_path:
            # 路径自动转换成长路径
            csproj_path = self.get_long_path_name(csproj_path)
            cmd = f'dotnet run --project "{csproj_path}"'
            self.execute_command(cmd)
        else:
            QMessageBox.warning(self, "调试", "未找到csproj项目文件，无法调试！")
        self.status_bar.showMessage("C#调试已启动")

    def continue_debug(self):
        """继续调试"""
        if hasattr(self, 'process') and self.process and self.process.state() == QProcess.Running:
            self.process.write(b'continue\n')
            self.status_bar.showMessage("继续调试")

    def step_debug(self):
        """单步调试"""
        if hasattr(self, 'process') and self.process and self.process.state() == QProcess.Running:
            self.process.write(b'next\n')
            self.status_bar.showMessage("单步调试")

    def stop_debug(self):
        """停止调试"""
        self.debug_toolbar.hide()  # 隐藏调试工具栏
        if hasattr(self, 'process') and self.process and self.process.state() == QProcess.Running:
            self.process.write(b'quit\n')
            self.process.kill()
            self.status_bar.showMessage("调试已停止")

    def init_run_button(self, icon_dir):
        """初始化右侧运行按钮"""
        run_button = QToolButton(self)
        run_button.setIcon(QIcon(os.path.join(icon_dir, "run.svg")) if os.path.exists(os.path.join(icon_dir, "run.svg")) else QIcon())
        run_button.setToolTip("运行代码 (F5)")
        run_button.setStyleSheet("margin: 4px; border: none;")
        run_button.clicked.connect(self.run_code)

        # 添加到右侧
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet("QToolBar { background: transparent; border: none; }")
        toolbar.addWidget(run_button)
        self.addToolBar(Qt.RightToolBarArea, toolbar)

    def init_sidebar(self):
        tree = QTreeView()
        tree.setModel(QFileSystemModel())
        tree.setRootIndex(tree.model().index(QDir.currentPath()))
        tree.setStyleSheet("background-color: #f3f3f3;")
        tree.clicked.connect(self.open_file_from_tree)
        tree.setTextElideMode(Qt.ElideNone)
        return tree

    def init_terminal(self):
        self.terminal_output = QPlainTextEdit()
        self.terminal_output.setReadOnly(True)
        # 初始样式：根据当前主题
        if "Dark" in self.theme:
            self.terminal_output.setStyleSheet("background-color: black; color: white; font-family: Consolas;")
        else:
            self.terminal_output.setStyleSheet("background-color: white; color: black; font-family: Consolas;")
        self.terminal_output.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.terminal_input = QLineEdit()
        if "Dark" in self.theme:
            self.terminal_input.setStyleSheet("background-color: black; color: white; font-family: Consolas;")
        else:
            self.terminal_input.setStyleSheet("background-color: white; color: black; font-family: Consolas;")
        self.terminal_input.returnPressed.connect(self.execute_command_from_input)
        # 初始化 QProcess 用于运行命令
        self.process = QProcess(self)
        if os.name == "nt":
            self.process.setProgram("powershell")
            # 启动时自动切换到65001编码页
            self.process.setArguments(["-NoLogo", "-NoExit", "-Command", "chcp 65001;"])
        else:
            self.process.setProgram("bash")
            self.process.setArguments(["-i"])
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_terminal_output)
        self.process.readyReadStandardError.connect(self.read_terminal_output)
        self.process.start()

        terminal_layout = QVBoxLayout()
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        terminal_layout.setSpacing(0)
        terminal_layout.addWidget(self.terminal_output)
        terminal_layout.addWidget(self.terminal_input)

        terminal_widget = QWidget()
        terminal_widget.setLayout(terminal_layout)
        return terminal_widget

    def init_layout(self):
        # 左侧：菜单 + 项目树（水平分割）
        left_splitter = QSplitter(Qt.Horizontal)
        left_splitter.addWidget(self.left_menu)
        left_splitter.addWidget(self.tree)
        left_splitter.setSizes([60, 220])

        # 右侧：编辑器 + 终端（垂直分割）
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self.tab_widget)
        right_splitter.addWidget(self.terminal_widget)
        right_splitter.setSizes([400, 120])

        # 主分割
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([280, 800])

        self.setCentralWidget(main_splitter)

    def init_file_manager(self):
        """初始化文件管理器"""
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.currentPath()))
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_tree_context_menu)

    def show_tree_context_menu(self, point):
        """显示文件树右键菜单"""
        index = self.tree.indexAt(point)
        if not index.isValid():
            return
        file_path = self.model.filePath(index)
        menu = QMenu()
        new_file_action = menu.addAction("New File")
        new_folder_action = menu.addAction("New Folder")
        rename_action = menu.addAction("Rename")
        copy_path_action = menu.addAction("Copy Path")
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.tree.viewport().mapToGlobal(point))
        if action == new_file_action:
            self.new_file()
        elif action == new_folder_action:
            self.new_folder()
        elif action == rename_action:
            self.rename_file(file_path)
        elif action == copy_path_action:
            self.copy_file_path(file_path)
        elif action == delete_action:
            self.delete_file(file_path)

    def rename_file(self, file_path):
        """重命名文件或文件夹"""
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=os.path.basename(file_path))
        if ok and new_name.strip():
            new_path = os.path.join(os.path.dirname(file_path), new_name)
            try:
                os.rename(file_path, new_path)
                self.model.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Rename failed: {e}")
                
    def copy_file_path(self, file_path):
        """复制文件路径到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(file_path)
        QMessageBox.information(self, "Path Copied", f"Path copied to clipboard:\n{file_path}")

    def new_file(self):
        """创建新文件"""
        folder = QFileDialog.getExistingDirectory(self, "Select Target Folder")
        if folder:
            file_name, ok = QInputDialog.getText(self, "New File", "Enter file name (with extension)")
            if ok and file_name:
                open(os.path.join(folder, file_name), 'w', encoding='utf-8').close()
                self.model.refresh()

    def new_folder(self):
        """创建新文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "Select Target Location")
        if folder:
            folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name")
            if ok and folder_name:
                os.makedirs(os.path.join(folder, folder_name), exist_ok=True)
                self.model.refresh()

    def delete_file(self, path):
        """删除文件或文件夹"""
        reply = QMessageBox.question(self, "Confirm Delete", f"Confirm delete {path}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    os.rmdir(path)
                self.model.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Delete failed: {e}")

    def log_error(self, message):
        """记录错误日志"""
        with open(self.log_file, "a", encoding="utf-8") as log:
            log.write(f"{message}\n")

    def execute_command(self, command):
        """执行终端命令"""
        if not hasattr(self, 'process') or self.process.state() != QProcess.Running:
            QMessageBox.warning(self, self.tr("Error"), self.tr("终端未运行，无法执行命令！"))
            return

        self.terminal_output.appendPlainText(f"> {command}")
        self.process.write((command + "\n").encode("utf-8"))

    def read_terminal_output(self):
        """读取终端输出"""
        # 统一用utf-8解码，确保chcp 65001后不会乱码
        output = self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        self.terminal_output.appendPlainText(output)
        self.status_bar.showMessage(self.tr("终端输出已更新"), 3000)  # 更新状态栏消息

    def execute_command_from_input(self):
        """从输入框执行命令"""
        command = self.terminal_input.text().strip()
        if command:
            self.terminal_output.appendPlainText(f"> {command}")
            if self.process.state() == QProcess.Running:
                self.process.write((command + "\n").encode("utf-8"))  # 统一为utf-8编码
            else:
                QMessageBox.warning(self, "Error", "终端未运行，无法执行命令！")
            self.terminal_input.clear()

    def init_left_menu(self, icon_dir):
        left_menu = QWidget()
        left_layout = QVBoxLayout(left_menu)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 项目树按钮
        btn_project = QLabel()
        btn_project.setPixmap(QIcon(os.path.join(icon_dir, "project.svg")).pixmap(QSize(32, 32)))
        btn_project.setAlignment(Qt.AlignCenter)
        btn_project.setToolTip(self.tr("项目树"))
        btn_project.mousePressEvent = lambda event: self.toggle_project_tree()
        left_layout.addWidget(btn_project)

        # 文件模板按钮
        btn_template = QLabel()
        btn_template.setPixmap(QIcon(os.path.join(icon_dir, "template.svg")).pixmap(QSize(32, 32)))
        btn_template.setAlignment(Qt.AlignCenter)
        btn_template.setToolTip(self.tr("文件模板"))
        btn_template.mousePressEvent = lambda event: self.open_file_template_window()
        left_layout.addWidget(btn_template)

        # 设置按钮
        btn_settings = QLabel()
        btn_settings.setPixmap(QIcon(os.path.join(icon_dir, "settings.svg")).pixmap(QSize(32, 32)))
        btn_settings.setAlignment(Qt.AlignCenter)
        btn_settings.setToolTip(self.tr("设置"))
        btn_settings.mousePressEvent = lambda event: self.show_settings()
        left_layout.addWidget(btn_settings)

        # 拖控件按钮
        btn_designer = QLabel()
        btn_designer.setPixmap(QIcon(os.path.join(icon_dir, "designer.svg")).pixmap(QSize(32, 32)))
        btn_designer.setAlignment(Qt.AlignCenter)
        btn_designer.setToolTip(self.tr("控件设计器"))
        btn_designer.mousePressEvent = lambda event: self.open_designer_window()
        left_layout.addWidget(btn_designer)

        left_layout.addStretch()
        left_menu.setStyleSheet("""
            QLabel {
                background-color: transparent;
                padding: 8px;
            }
            QLabel:hover {
                background-color: #3498db;
            }
            QLabel:pressed {
                background-color: #2980b9;
            }
        """)
        return left_menu

    def show_debug_menu(self):
        """显示调试菜单"""
        menu = QMenu(self)
        menu.addAction(QIcon(r".\icons\start_debug.svg"), "Start Debug", self.start_debug)
        menu.addAction(QIcon(r".\icons\stop_debug.svg"), "Stop Debug", self.stop_debug)
        menu.addAction(QIcon(r".\icons\step_over.svg"), "Step Over", self.step_over)
        menu.addAction(QIcon(r".\icons\step_into.svg"), "Step Into", self.step_into)
        menu.addAction(QIcon(r".\icons\step_out.svg"), "Step Out", self.step_out)
        menu.exec_(QCursor.pos())

    def toggle_project_tree(self):
        """收起/打开项目树"""
        if self.tree.isVisible():
            self.tree.hide()
        else:
            self.tree.show()

    def open_file_template_window(self):
        """将文件模板面板切换为窗口"""
        dialog = QDialog(self)
        translations = self.lang_manager.translations
        dialog.setWindowTitle(translations.get("File Templates", "File Templates"))
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)
        label = QLabel(translations.get("Select a file template:", "Select a file template:"))
        layout.addWidget(label)

        list_widget = QListWidget()
        templates = {
            translations.get("Standard C# File", "Standard C# File"): "console",
            translations.get("WinForms File", "WinForms File"): "winforms",
            translations.get("WPF File", "WPF File"): "wpf",
            translations.get("ASP.NET File", "ASP.NET File"): "webapp"
        }
        for name in templates.keys():
            list_widget.addItem(name)
        layout.addWidget(list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec_() == QDialog.Accepted:
            selected_item = list_widget.currentItem()
            if selected_item:
                template_name = selected_item.text()
                template_type = templates[template_name]
                self.generate_template(template_name, template_type)

    def generate_template(self, template_name, template_type):
        """使用 dotnet new 命令生成文件模板"""
        folder = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if not folder:
            return
        project_name, ok = QInputDialog.getText(self, "项目名称", "请输入项目名称：")
        if not ok or not project_name.strip():
            QMessageBox.warning(self, "错误", "项目名称不能为空！")
            return

        command = f'dotnet new {template_type} -n "{project_name}"'
        process = subprocess.Popen(
            command, cwd=folder, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8"
        )
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            QMessageBox.information(self, "成功", f"{template_name} 模板已生成！\n路径: {os.path.join(folder, project_name)}")
        else:
            QMessageBox.critical(self, "失败", f"生成模板失败！\n错误信息:\n{stderr}")

    def show_settings(self):
        """显示设置对话框，去除导入主题按钮"""
        dialog = SettingsDialog(self.lang_manager, self)
        # 不再添加导入主题按钮
        if dialog.exec_():
            self.theme = dialog.theme_box.currentText()
            self.font_name = dialog.font_box.currentText()
            self.font_size = int(dialog.font_size_box.currentText())
            self.apply_theme_and_font()

    def open_designer_window(self):
        """打开控件设计器窗口"""
        designer_window = DesignerWindow(self.lang_manager)
        designer_window.show()

    def open_file_from_tree(self, index):
        """从文件树中打开文件"""
        file_path = self.tree.model().filePath(index)
        if os.path.isfile(file_path):
            self.load_file(file_path)

    def apply_theme_and_font(self, theme_file=None, **kwargs):
        """应用主题和字体，支持深灰/浅灰和自定义QSS"""
        from .theme import apply_theme_and_font
        if theme_file and theme_file.endswith('.qss'):
            # 导入QSS主题
            with open(theme_file, 'r', encoding='utf-8') as f:
                qss = f.read()
            self.setStyleSheet(qss)
        else:
            apply_theme_and_font(self, theme_file=theme_file)
        # 强制刷新界面
        self.update()

    def update_left_menu_theme(self):
        """根据主题更新左侧菜单样式"""
        if "Dark" in self.theme:
            self.left_menu.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    padding: 8px;
                }
                QLabel:hover {
                    background-color: #3498db;
                }
                QLabel:pressed {
                    background-color: #2980b9;
                }
            """)
        else:
            self.left_menu.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    padding: 8px;
                }
                QLabel:hover {
                    background-color: #3498db;
                }
                QLabel:pressed {
                    background-color: #2980b9;
                }
            """)

    def run_code(self):
        """运行代码"""
        code = self.current_editor().toPlainText()
        if not code.strip():
            QMessageBox.warning(self, self.tr("Error"), self.tr("代码为空，无法运行！"))
            return
        try:
            if self.current_file and self.current_file.endswith('.py'):
                file_path = self.current_file
                # 自动插入强制utf-8输出代码
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                utf8_code = "import sys\nif hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')\n"
                # 检查是否已插入
                if not any('reconfigure' in line and 'utf-8' in line for line in lines):
                    # 跳过shebang和编码声明，插入到合适位置
                    insert_idx = 0
                    for i, line in enumerate(lines[:2]):
                        if line.startswith('#!') or 'coding' in line:
                            insert_idx = i + 1
                    lines.insert(insert_idx, utf8_code)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                # 路径自动转换成长路径并规范化
                file_path = self.get_long_path_name(file_path)
                file_path = os.path.abspath(file_path)
                file_path = os.path.normpath(file_path)
                # 版本到绝对路径映射（如有其它版本请自行扩展）
                python_path_map = {
                    '3.7': r'D:/Python37/python.exe',
                    '3.9': r'D:/Python39/python.exe',
                }
                py_version = self.python_version_combo.currentText()
                py_version_short = py_version.split('-')[0].strip() if py_version else ''
                # 检查是否有中文
                if any('\u4e00' <= ch <= '\u9fff' for ch in file_path):
                    python_path = python_path_map.get(py_version_short, 'python')
                    # 只有当python_path有空格时才加引号
                    if ' ' in python_path:
                        python_path = f'"{python_path}"'
                    command = f'{python_path} "{file_path}"'
                else:
                    if py_version and py_version != '默认（当前系统）':
                        command = f'py -{py_version_short} "{file_path}"'
                    else:
                        command = f'python "{file_path}"'
                self.execute_command(command)
            elif self.current_file and self.current_file.endswith('.cs'):
                dotnet_version = self.dotnet_version_combo.currentText()
                project_dir = os.path.dirname(self.current_file)
                csproj_path = next((os.path.join(project_dir, f) for f in os.listdir(project_dir) if f.endswith('.csproj')), None)
                if csproj_path:
                    # 路径自动转换成长路径并规范化
                    csproj_path = self.get_long_path_name(csproj_path)
                    csproj_path = os.path.abspath(csproj_path)
                    csproj_path = os.path.normpath(csproj_path)
                    command = f'dotnet run --fx-version {dotnet_version} --project "{csproj_path}"'
                    self.execute_command(command)
            else:
                QMessageBox.warning(self, self.tr("Error"), self.tr("不支持的文件类型！"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def get_long_path_name(self, path):
        """将路径自动转换为长路径，兼容中文和特殊字符，仅在Windows下生效"""
        if os.name != 'nt':
            return path
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            get_long = getattr(ctypes.windll.kernel32, 'GetLongPathNameW', None)
            if get_long:
                get_long(str(path), buf, 260)
                long_path = buf.value
                if long_path:
                    return long_path
        except Exception:
            pass
        return path

    def init_menu_bar(self):
        """初始化菜单栏"""
        t = self.lang_manager.t
        menu_bar = self.menuBar()
        menu_bar.clear()  # 清空菜单栏，防止重复添加菜单项

        # 文件菜单
        file_menu = QMenu(t("File"), self)
        new_action = QAction(t("New"), self)
        new_action.triggered.connect(self.new_file_action)
        open_action = QAction(t("Open"), self)
        open_action.triggered.connect(self.open_file_action)
        open_folder_action = QAction(t("Open Folder"), self)
        open_folder_action.triggered.connect(self.open_folder_action)
        save_action = QAction(t("Save"), self)
        save_action.triggered.connect(self.save_file_action)
        exit_action = QAction(t("Exit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(open_folder_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = QMenu(t("Edit"), self)
        undo_action = QAction(t("Undo"), self)
        undo_action.triggered.connect(self.current_editor().undo)
        redo_action = QAction(t("Redo"), self)
        redo_action.triggered.connect(self.current_editor().redo)
        cut_action = QAction(t("Cut"), self)
        cut_action.triggered.connect(self.current_editor().cut)
        copy_action = QAction(t("Copy"), self)
        copy_action.triggered.connect(self.current_editor().copy)
        paste_action = QAction(t("Paste"), self)
        paste_action.triggered.connect(self.current_editor().paste)
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(cut_action)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)

        # 调试菜单
        debug_menu = QMenu(t("Debug"), self)
        start_debug_action = QAction(t("Start Debug"), self)
        start_debug_action.triggered.connect(self.start_debug)
        stop_debug_action = QAction(t("Stop Debug"), self)
        stop_debug_action.triggered.connect(self.stop_debug)
        debug_menu.addAction(start_debug_action)
        debug_menu.addAction(stop_debug_action)

        # 设置菜单
        settings_menu = QMenu(t("Settings"), self)
        language_action = QAction(t("Switch Language"), self)
        language_action.triggered.connect(self.toggle_language)
        settings_menu.addAction(language_action)

        # 帮助菜单
        help_menu = QMenu(t("Help"), self)
        about_action = QAction(t("About"), self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        # 添加菜单到菜单栏
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(edit_menu)
        menu_bar.addMenu(debug_menu)
        menu_bar.addMenu(settings_menu)
        menu_bar.addMenu(help_menu)

    def init_debug_toolbar(self):
        """初始化播放器式调试控制栏"""
        self.debug_toolbar = QToolBar("Debug Toolbar", self)
        self.debug_toolbar.setMovable(False)
        self.debug_toolbar.setIconSize(QSize(24, 24))
        # 开始调试
        start_btn = QToolButton()
        start_btn.setIcon(QIcon.fromTheme("media-playback-start"))
        start_btn.setToolTip("开始调试")
        start_btn.clicked.connect(self.start_debug)
        self.debug_toolbar.addWidget(start_btn)
        # 继续
        cont_btn = QToolButton()
        cont_btn.setIcon(QIcon.fromTheme("media-seek-forward"))
        cont_btn.setToolTip("继续")
        cont_btn.clicked.connect(self.continue_debug)
        self.debug_toolbar.addWidget(cont_btn)
        # 单步
        step_btn = QToolButton()
        step_btn.setIcon(QIcon.fromTheme("media-skip-forward"))
        step_btn.setToolTip("单步")
        step_btn.clicked.connect(self.step_debug)
        self.debug_toolbar.addWidget(step_btn)
        # 停止
        stop_btn = QToolButton()
        stop_btn.setIcon(QIcon.fromTheme("media-playback-stop"))
        stop_btn.setToolTip("停止调试")
        stop_btn.clicked.connect(self.stop_debug)
        self.debug_toolbar.addWidget(stop_btn)
        self.addToolBar(Qt.TopToolBarArea, self.debug_toolbar)

    def update_tree_theme(self):
        """更新项目树的主题"""
        if "Dark" in self.theme:
            self.tree.setStyleSheet("""
                QTreeView {
                    background-color: #1e1e1e;
                    color: #dddddd;
                    border: none;
                    outline: none;
                }
            """)
        else:
            self.tree.setStyleSheet("""
                QTreeView {
                    background-color: #f9f9f9;
                    color: #000000;
                    border: none;
                    outline: none;
                }
            """)

    def update_status_bar_theme(self):
        """更新状态栏的主题"""
        if "Dark" in self.theme:
            self.statusBar().setStyleSheet("background-color: #1e1e1e; color: #dddddd;")
        else:
            self.statusBar().setStyleSheet("background-color: #f3f3f3; color: #000000;")

    def update_splitter_theme(self):
        """更新主Splitter的主题"""
        if "Dark" in self.theme:
            self.centralWidget().setStyleSheet("background-color: #1e1e1e;")
        else:
            self.centralWidget().setStyleSheet("background-color: #ffffff;")

    def update_all_widgets_theme(self):
        """批量更新所有关键控件的主题"""
        main_bg = "#1e1e1e" if "Dark" in self.theme else "#ffffff"
        main_fg = "#dddddd" if "Dark" in self.theme else "#000000"

        # 编辑器（多标签）只设置背景色，不设置 color，避免覆盖高亮
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if hasattr(editor, 'setStyleSheet'):
                editor.setStyleSheet(f"background-color: {main_bg};")

        # 终端
        if "Dark" in self.theme:
            self.terminal_output.setStyleSheet("background-color: black; color: white; font-family: Consolas;")
            self.terminal_input.setStyleSheet("background-color: black; color: white; font-family: Consolas;")
        else:
            self.terminal_output.setStyleSheet("background-color: white; color: black; font-family: Consolas;")
            self.terminal_input.setStyleSheet("background-color: white; color: black; font-family: Consolas;")

        # 项目树
        if "Dark" in self.theme:
            self.tree.setStyleSheet("""
                QTreeView {
                    background-color: #1e1e1e;
                    color: #dddddd;
                    border: none;
                    outline: none;
                }
            """)
        else:
            self.tree.setStyleSheet("""
                QTreeView {
                    background-color: #f9f9f9;
                    color: #000000;
                    border: none;
                    outline: none;
                }
            """)

        # 左侧菜单
        self.update_left_menu_theme()

    def open_folder_action(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.tree.setRootIndex(self.model.index(folder))

    def show_about_dialog(self):
        QMessageBox.about(self, "关于", "PySharp Code\n版本 1.0\n作者: Your Name")