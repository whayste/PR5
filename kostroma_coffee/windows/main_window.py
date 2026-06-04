import tkinter as tk
from tkinter import messagebox, ttk
from database import get_connection
from auth import toggle_theme
from logger import log_action


class MainWindow(tk.Tk):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.title(f"Kostroma Coffee Love — {user['full_name']} ({user['role_name']})")
        self.geometry("950x620")
        self._apply_theme()
        self._build_menu()
        self._build_content()
        self._load_stats()

    def _apply_theme(self):
        dark = bool(self.user.get("dark_theme", 0))
        bg = "#2b2b2b" if dark else "#f7f1e8"
        fg = "#e0e0e0" if dark else "#3b2a1a"
        accent = "#6f4e37" if not dark else "#c89f6d"
        self.configure(bg=bg)
        style = ttk.Style(self)
        if dark:
            style.theme_use("clam")
            style.configure("TFrame", background=bg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TLabelframe", background=bg, foreground=accent)
            style.configure("TLabelframe.Label", background=bg, foreground=accent)
            style.configure("TButton", background="#444", foreground=fg)
            style.configure("Treeview", background="#333", foreground=fg,
                            fieldbackground="#333")
            style.configure("Treeview.Heading", background="#555", foreground=fg)
        else:
            style.theme_use("clam")
            style.configure("TFrame", background=bg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TLabelframe", background=bg, foreground=accent)
            style.configure("TLabelframe.Label", background=bg, foreground=accent)

    def _build_menu(self):
        menubar = tk.Menu(self)
        nav = tk.Menu(menubar, tearoff=0)
        nav.add_command(label="☕ Напитки",
                        command=lambda: self._open("drinks"))
        nav.add_command(label="👥 Сотрудники",
                        command=lambda: self._open("employees"))
        nav.add_command(label="🏠 Кофейни",
                        command=lambda: self._open("cafes"))
        menubar.add_cascade(label="Разделы", menu=nav)

        profile = tk.Menu(menubar, tearoff=0)
        self.theme_var = tk.BooleanVar(value=bool(self.user.get("dark_theme", 0)))
        profile.add_checkbutton(label="🌙 Тёмная тема",
                                variable=self.theme_var,
                                command=self._toggle_theme)
        profile.add_separator()
        profile.add_command(label="🚪 Выход", command=self._logout)
        menubar.add_cascade(label="Профиль", menu=profile)
        self.config(menu=menubar)

    def _toggle_theme(self):
        toggle_theme(self.user["id"], self.theme_var.get())
        self.user["dark_theme"] = int(self.theme_var.get())
        self._apply_theme()

    def _build_content(self):
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(self.main_frame,
                  text=f"☕ Добро пожаловать, {self.user['full_name']}!",
                  font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Label(self.main_frame,
                  text=f"Должность: {self.user['position']}   |   "
                       f"Роль: {self.user['role_name']}",
                  font=("Arial", 10)).pack(anchor="w", pady=(0, 15))

        self.stats_frame = ttk.LabelFrame(self.main_frame, text="Сводка по сети")
        self.stats_frame.pack(fill="x", pady=5)

        self.recent_frame = ttk.LabelFrame(self.main_frame,
                                           text="Последние добавленные напитки")
        self.recent_frame.pack(fill="both", expand=True, pady=5)

    def _load_stats(self):
        conn = get_connection()
        cur = conn.cursor()
        stats = {}
        for table in ("drinks", "employees", "cafes"):
            cur.execute(f"SELECT COUNT(*) as c FROM {table}")
            stats[table] = cur.fetchone()["c"]

        for child in self.stats_frame.winfo_children():
            child.destroy()
        ttk.Label(self.stats_frame,
                  text=f"Напитков в меню: {stats['drinks']}   |   "
                       f"Сотрудников: {stats['employees']}   |   "
                       f"Кофеен: {stats['cafes']}",
                  font=("Arial", 11)).pack(pady=10)

        for child in self.recent_frame.winfo_children():
            child.destroy()
        cur.execute("SELECT name, category, price FROM drinks ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()
        if rows:
            tree = ttk.Treeview(self.recent_frame,
                                columns=("name", "category", "price"),
                                show="headings", height=5)
            tree.heading("name", text="Название")
            tree.heading("category", text="Категория")
            tree.heading("price", text="Цена, ₽")
            tree.column("name", width=300)
            tree.column("category", width=150)
            tree.column("price", width=100)
            for r in rows:
                tree.insert("", "end", values=(r["name"], r["category"], r["price"]))
            tree.pack(fill="both", expand=True, padx=5, pady=5)
        else:
            ttk.Label(self.recent_frame,
                      text="Меню пока пустое. Добавьте первый напиток!").pack(pady=20)
        conn.close()

    def _open(self, entity: str):
        if entity == "drinks":
            from windows.drinks_window import DrinksWindow
            DrinksWindow(self, self.user)
        elif entity == "employees":
            from windows.employees_window import EmployeesWindow
            EmployeesWindow(self, self.user)
        elif entity == "cafes":
            from windows.cafes_window import CafesWindow
            CafesWindow(self, self.user)

    def _logout(self):
        if messagebox.askyesno("Выход",
                               "Вы уверены, что хотите выйти?"):
            log_action(self.user["login"], self.user["role_name"],
                       "LOGOUT", "SUCCESS")
            self.destroy()