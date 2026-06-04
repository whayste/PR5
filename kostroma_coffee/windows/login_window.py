import tkinter as tk
from tkinter import messagebox
from auth import authenticate


class LoginWindow(tk.Tk):
    def __init__(self, on_success):
        super().__init__()
        self.title("Kostroma Coffee Love — Вход")
        self.geometry("400x300")
        self.resizable(False, False)
        self.on_success = on_success

        tk.Label(self, text="☕ Kostroma Coffee Love",
                 font=("Arial", 15, "bold")).pack(pady=10)
        tk.Label(self, text="Вход для сотрудников",
                 font=("Arial", 10)).pack()

        tk.Label(self, text="Логин:").pack(pady=(10, 0))
        self.entry_login = tk.Entry(self, width=30)
        self.entry_login.pack(pady=2)

        tk.Label(self, text="Пароль:").pack()
        self.entry_password = tk.Entry(self, show="*", width=30)
        self.entry_password.pack(pady=2)
        self.entry_password.bind("<Return>", lambda e: self._login())

        tk.Button(self, text="Войти", width=20, command=self._login).pack(pady=8)
        tk.Button(self, text="Регистрация сотрудника", width=20,
                  command=self._open_register).pack()

    def _login(self):
        login = self.entry_login.get().strip()
        password = self.entry_password.get()
        ok, msg, user = authenticate(login, password)
        if ok:
            self.destroy()
            self.on_success(user)
        else:
            messagebox.showerror("Ошибка входа", msg)

    def _open_register(self):
        from windows.register_window import RegisterWindow
        self.withdraw()
        RegisterWindow(self, on_close=self.deiconify)