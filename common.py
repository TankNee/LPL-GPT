import functools
import json
import time

import yaml
from loguru import logger


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


def create_logger(log_file="./logs/download.log"):
    logger.add(
        log_file,
        level="DEBUG",
        rotation="10 MB",
        compression="zip",
    )


def retry(retry_times, default=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(retry_times):
                try:
                    output = func(*args, **kwargs)
                    return output if output is not None else default
                except Exception as e:
                    logger.warning(f"Function execution failed, retrying... {e}")
                    time.sleep(30)

            raise Exception("Function execution failed after multiple retries.")

        return wrapper

    return decorator
