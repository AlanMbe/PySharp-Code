import json
import os
import sys

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    elif getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    else:
        return os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), relative_path)

class LangManager:
    def __init__(self, lang_file="translations/translations.json", lang="zh"):
        lang_file_path = resource_path(lang_file)
        if not os.path.exists(lang_file_path):
            raise FileNotFoundError(f"Translation file not found: {lang_file_path}")
        with open(lang_file_path, "r", encoding="utf-8") as f:
            self.translations = json.load(f)
        self.lang = lang

    def set_lang(self, lang):
        """设置当前语言"""
        self.lang = lang

    def t(self, key):
        """获取翻译内容"""
        return self.translations.get(self.lang, {}).get(key, key)

    def check_missing_keys(self):
        """检查翻译文件中是否存在缺失的键值"""
        keys_zh = set(self.translations.get("zh", {}).keys())
        keys_en = set(self.translations.get("en", {}).keys())
        missing_in_en = keys_zh - keys_en
        missing_in_zh = keys_en - keys_zh
        if missing_in_en or missing_in_zh:
            print("Missing in EN:", missing_in_en)
            print("Missing in ZH:", missing_in_zh)
        else:
            print("No missing keys in translations.")
