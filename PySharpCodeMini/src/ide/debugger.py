import subprocess
from threading import Thread  # 替换 QThread 为标准线程
from PySide6.QtCore import QObject, Signal

class Debugger(QObject):
    output_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.running = False

    def start_debugging(self, command):
        """启动调试进程"""
        if self.process and self.process.poll() is None:
            self.error_signal.emit("调试已在运行中！")
            return

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )
            self.running = True
            Thread(target=self._read_output, daemon=True).start()  # 修复线程启动问题
        except Exception as e:
            self.error_signal.emit(f"启动调试失败：{e}")

    def _read_output(self):
        """实时读取调试输出"""
        if not self.process:
            return

        try:
            while self.running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    self.output_signal.emit(line)
            stderr = self.process.stderr.read()
            if stderr:
                self.error_signal.emit(stderr)
            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(f"读取调试输出失败：{e}")

    def stop_debugging(self):
        """停止调试进程"""
        if self.process and self.process.poll() is None:
            self.running = False
            self.process.terminate()
            self.process = None
            self.finished_signal.emit()

    def step_over(self):
        """执行单步跳过"""
        if self.process:
            self.process.stdin.write("n\n")
            self.process.stdin.flush()

    def step_into(self):
        """执行单步进入"""
        if self.process:
            self.process.stdin.write("s\n")
            self.process.stdin.flush()

    def step_out(self):
        """执行单步退出"""
        if self.process:
            self.process.stdin.write("r\n")
            self.process.stdin.flush()
