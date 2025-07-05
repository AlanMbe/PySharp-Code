import os
from PySide6.QtCore import QDir
from PySide6.QtWidgets import QFileSystemModel

class FileManager:
    def __init__(self, model: QFileSystemModel):
        self.model = model

    def open_file(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def save_file(self, path, content):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def delete_file(self, path):
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            os.rmdir(path)

    def refresh_model(self):
        self.model.refresh()