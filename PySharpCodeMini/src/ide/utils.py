def get_file_path(file_name):
    import os
    return os.path.join(os.path.dirname(__file__), file_name)

def load_json(file_path):
    import json
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path, data):
    import json
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_resource_path(resource_name):
    import os
    return os.path.join(get_file_path('..', 'resources'), resource_name)