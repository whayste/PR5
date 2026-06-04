import hashlib
import sqlite3
from datetime import datetime, timedelta
from database import get_connection
from logger import log_action

LOCK_SECONDS = 30


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(login: str, password: str, email: str,
                  full_name: str, position: str) -> tuple[bool, str]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (login, password_hash, email, full_name, position, role_id) "
            "VALUES (?, ?, ?, ?, ?, 2)",
            (login, _hash(password), email, full_name, position)
        )
        conn.commit()
        log_action(login, "barista", "REGISTER", "SUCCESS")
        return True, ""
    except sqlite3.IntegrityError as e:
        msg = str(e)
        if "login" in msg:
            return False, "Логин уже занят"
        if "email" in msg:
            return False, "Email уже зарегистрирован"
        return False, "Ошибка регистрации"
    finally:
        conn.close()


def authenticate(login: str, password: str) -> tuple[bool, str, dict | None]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.*, r.name as role_name
        FROM users u JOIN roles r ON u.role_id = r.id
        WHERE u.login = ?
    """, (login,))
    row = cur.fetchone()

    if not row:
        log_action(login, "unknown", "LOGIN", "FAIL_USER_NOT_FOUND")
        conn.close()
        return False, "Пользователь не найден", None

    if row["locked_until"]:
        locked_until = datetime.fromisoformat(row["locked_until"])
        if datetime.now() < locked_until:
            remaining = int((locked_until - datetime.now()).total_seconds())
            log_action(login, row["role_name"], "LOGIN", f"FAIL_LOCKED_{remaining}s")
            conn.close()
            return False, f"Аккаунт заблокирован. Подождите {remaining} сек.", None
        else:
            cur.execute("UPDATE users SET locked_until=NULL, failed_attempts=0 WHERE id=?",
                        (row["id"],))
            conn.commit()

    if row["password_hash"] != _hash(password):
        attempts = row["failed_attempts"] + 1
        if attempts >= 3:
            until = (datetime.now() + timedelta(seconds=LOCK_SECONDS)).isoformat()
            cur.execute("UPDATE users SET failed_attempts=?, locked_until=? WHERE id=?",
                        (attempts, until, row["id"]))
            log_action(login, row["role_name"], "LOGIN", "FAIL_LOCKED")
            conn.commit()
            conn.close()
            return False, "Превышено число попыток. Блокировка на 30 секунд.", None
        else:
            cur.execute("UPDATE users SET failed_attempts=? WHERE id=?",
                        (attempts, row["id"]))
            conn.commit()
            conn.close()
            log_action(login, row["role_name"], "LOGIN", f"FAIL_WRONG_PASSWORD_{attempts}")
            return False, f"Неверный пароль. Попыток осталось: {3 - attempts}", None

    cur.execute("UPDATE users SET failed_attempts=0, locked_until=NULL WHERE id=?",
                (row["id"],))
    conn.commit()
    log_action(login, row["role_name"], "LOGIN", "SUCCESS")
    user = dict(row)
    conn.close()
    return True, "", user


def toggle_theme(user_id: int, enabled: bool):
    conn = get_connection()
    conn.execute("UPDATE users SET dark_theme=? WHERE id=?", (int(enabled), user_id))
    conn.commit()
    conn.close()