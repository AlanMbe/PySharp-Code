from PySide6.QtWidgets import QPlainTextEdit, QLineEdit, QVBoxLayout, QWidget
from PySide6.QtCore import QProcess
import os

def init_terminal(self):
    """初始化集成终端"""
    self.terminal_output = QPlainTextEdit()
    self.terminal_output.setReadOnly(True)
    self.terminal_input = QLineEdit()
    self.terminal_input.returnPressed.connect(self.execute_command_from_input)

    self.process = QProcess(self)
    self.process.setProgram("powershell" if os.name == "nt" else "bash")
    self.process.setArguments(["-NoLogo", "-NoExit"])
    self.process.start()

    terminal_layout = QVBoxLayout()
    terminal_layout.addWidget(self.terminal_output)
    terminal_layout.addWidget(self.terminal_input)

    terminal_widget = QWidget()
    terminal_widget.setLayout(terminal_layout)
    self.editor_terminal_splitter.addWidget(terminal_widget)

def execute_command_from_input(self):
    """从输入框执行命令"""
    command = self.terminal_input.text().strip()
    if command:
        self.terminal_output.appendPlainText(f"> {command}")
        if self.process.state() == QProcess.Running:
            self.process.write((command + "\n").encode("utf-8"))
        else:
            self.terminal_output.appendPlainText("终端未运行，无法执行命令！")
        self.terminal_input.clear()

def close_terminal(self):
    """关闭终端"""
    if hasattr(self, 'process') and self.process.state() == QProcess.Running:
        self.process.kill()  # 强制终止进程
        self.process.close()  # 释放资源
