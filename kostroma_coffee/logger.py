import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "kostroma_coffee.log")


def log_action(username: str, role: str, action: str, result: str):
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{username}] [{role}] [{action}] [{result}]\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)