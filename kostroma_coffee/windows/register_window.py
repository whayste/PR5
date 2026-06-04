import tkinter as tk
from tkinter import messagebox
from auth import register_user
from validators import (validate_email, validate_password,
                        validate_non_empty, validate_min_length)


class RegisterWindow(tk.Tk):
    def __init__(self, parent, on_close):
        super().__init__()
        self.parent = parent
        self.on_close = on_close
        self.title("Регистрация сотрудника")
        self.geometry("420x430")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._close)

        tk.Label(self, text="☕ Новый сотрудник Kostroma Coffee Love",
                 font=("Arial", 12, "bold")).pack(pady=8)

        fields = ["Логин", "Пароль", "Повтор пароля",
                  "Email", "ФИО", "Должность (бариста/кассир и т.д.)"]
        self.entries = {}
        for f in fields:
            tk.Label(self, text=f + ":").pack()
            e = tk.Entry(self, width=38,
                         show="*" if "ароль" in f else "")
            e.pack(pady=1)
            self.entries[f] = e

        tk.Button(self, text="Зарегистрироваться",
                  width=22, command=self._submit).pack(pady=12)

    def _submit(self):
        data = {k: v.get().strip() for k, v in self.entries.items()}
        checks = [
            validate_non_empty(data["Логин"], "Логин"),
            validate_min_length(data["Логин"], "Логин", 3),
            validate_non_empty(data["Email"], "Email"),
            validate_email(data["Email"]),
            validate_non_empty(data["ФИО"], "ФИО"),
            validate_min_length(data["ФИО"], "ФИО", 3),
            validate_non_empty(data["Должность (бариста/кассир и т.д.)"], "Должность"),
            validate_min_length(data["Должность (бариста/кассир и т.д.)"], "Должность", 3),
            validate_password(data["Пароль"]),
        ]
        if data["Пароль"] != data["Повтор пароля"]:
            checks.append((False, "Пароли не совпадают"))

        for ok, msg in checks:
            if not ok:
                messagebox.showerror("Ошибка валидации", msg)
                return

        ok, msg = register_user(
            data["Логин"], data["Пароль"], data["Email"],
            data["ФИО"], data["Должность (бариста/кассир и т.д.)"]
        )
        if ok:
            messagebox.showinfo("Успех", "Сотрудник зарегистрирован!")
            self._close()
        else:
            messagebox.showerror("Ошибка", msg)

    def _close(self):
        self.destroy()
        if self.on_close:
            self.on_close()