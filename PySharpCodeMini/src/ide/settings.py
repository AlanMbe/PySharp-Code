import json

class Settings:
    def __init__(self):
        self.theme = 'Light'
        self.font_name = 'JetBrains Mono'
        self.font_size = 12
        self.project_file = 'project.json'
        self.load_settings()

    def load_settings(self):
        try:
            with open(self.project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.theme = data.get('theme', self.theme)
                self.font_name = data.get('font_name', self.font_name)
                self.font_size = data.get('font_size', self.font_size)
        except FileNotFoundError:
            self.save_settings()

    def save_settings(self):
        data = {
            'theme': self.theme,
            'font_name': self.font_name,
            'font_size': self.font_size
        }
        with open(self.project_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)