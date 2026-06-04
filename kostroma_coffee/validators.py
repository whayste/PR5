import re


def validate_email(email: str) -> tuple[bool, str]:
    """
    Валидация email согласно ТЗ практической работы №5.
    1. Базовая проверка формата: наличие @, точки в доменной части,
       допустимые символы, разумная длина.
    2. Бизнес-правило предметной области «Kostroma Coffee Love»:
       email не должен содержать подстроку "admin" в любой части адреса
       в любом регистре. Это защита от имперсонации администрации сети.
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return False, "Некорректный формат email"
    if len(email) > 254:
        return False, "Email слишком длинный"
    if "admin" in email.lower():
        return False, "Email не может содержать 'admin' (политика сети)"
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Минимум 8 символов"
    if not re.search(r"[A-Z]", password):
        return False, "Нужна хотя бы одна заглавная буква"
    if not re.search(r"[0-9]", password):
        return False, "Нужна хотя бы одна цифра"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`]", password):
        return False, "Нужен хотя бы один спецсимвол"
    return True, ""


def validate_non_empty(value, field_name: str) -> tuple[bool, str]:
    if value is None or not str(value).strip():
        return False, f"Поле '{field_name}' не может быть пустым"
    return True, ""


def validate_min_length(value: str, field_name: str, min_len: int = 3) -> tuple[bool, str]:
    if len(str(value).strip()) < min_len:
        return False, f"'{field_name}' — минимум {min_len} символа"
    return True, ""


def validate_number(value, field_name: str, allow_empty: bool = True) -> tuple[bool, str]:
    if value is None or str(value).strip() == "":
        if allow_empty:
            return True, ""
        return False, f"Поле '{field_name}' обязательно"
    try:
        float(value)
        return True, ""
    except (ValueError, TypeError):
        return False, f"'{field_name}' должно быть числом"


def validate_positive_number(value, field_name: str) -> tuple[bool, str]:
    ok, msg = validate_number(value, field_name, allow_empty=False)
    if not ok:
        return False, msg
    if float(value) <= 0:
        return False, f"'{field_name}' должно быть больше нуля"
    return True, ""