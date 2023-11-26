import json
import yaml

def read_yaml(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def write_yaml(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)

def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def read_jsonl(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def write_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def write_jsonl(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        for line in data:
            json.dump(line, f, ensure_ascii=False)
            f.write("\n")
        