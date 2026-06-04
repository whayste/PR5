import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from database import get_connection
from exporter import export_to_csv
from logger import log_action
from validators import (validate_non_empty, validate_min_length,
                        validate_positive_number, validate_number)


class DrinksWindow(tk.Toplevel):
    def __init__(self, parent, user):
        super().__init__(parent)
        self.user = user
        self.title("Меню — Напитки")
        self.geometry("900x520")
        self._build()
        self._load()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=5)

        ttk.Button(top, text="➕ Добавить", command=self._add).pack(side="left", padx=2)
        ttk.Button(top, text="✏️ Редактировать", command=self._edit).pack(side="left", padx=2)
        ttk.Button(top, text="🗑 Удалить", command=self._delete).pack(side="left", padx=2)
        ttk.Button(top, text="📤 Экспорт в CSV", command=self._export).pack(side="left", padx=2)

        ttk.Label(top, text="Поиск:").pack(side="left", padx=(20, 2))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        ttk.Entry(top, textvariable=self.search_var, width=25).pack(side="left")

        cols = ("id", "name", "category", "price", "volume_ml")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.heading("id", text="№")
        self.tree.heading("name", text="Название")
        self.tree.heading("category", text="Категория")
        self.tree.heading("price", text="Цена, ₽")
        self.tree.heading("volume_ml", text="Объём, мл")
        self.tree.column("id", width=40)
        self.tree.column("name", width=280)
        self.tree.column("category", width=150)
        self.tree.column("price", width=100)
        self.tree.column("volume_ml", width=100)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        q = self.search_var.get().strip().lower()
        sql = "SELECT * FROM drinks"
        params = ()
        if q:
            sql += " WHERE LOWER(name) LIKE ? OR LOWER(category) LIKE ?"
            params = (f"%{q}%", f"%{q}%")
        sql += " ORDER BY id DESC"
        for r in conn.execute(sql, params):
            self.tree.insert("", "end", values=(
                r["id"], r["name"], r["category"],
                r["price"], r["volume_ml"] or ""
            ))
        conn.close()

    def _form(self, existing=None):
        win = tk.Toplevel(self)
        win.title("Напиток" if not existing else f"Напиток №{existing['id']}")
        win.geometry("420x340")
        win.grab_set()

        fields = {}
        for label, key in [("Название", "name"), ("Категория", "category"),
                           ("Цена, ₽", "price"), ("Объём, мл", "volume_ml")]:
            ttk.Label(win, text=label + ":").pack(anchor="w", padx=10, pady=(8, 0))
            e = ttk.Entry(win, width=45)
            e.pack(padx=10)
            fields[key] = e
            if existing and existing.get(key) is not None:
                e.insert(0, existing[key])

        self.error_label = tk.Label(win, text="", fg="red")
        self.error_label.pack(pady=5)

        def save():
            data = {k: v.get().strip() for k, v in fields.items()}
            checks = [
                validate_non_empty(data["name"], "Название"),
                validate_min_length(data["name"], "Название", 3),
                validate_non_empty(data["category"], "Категория"),
                validate_min_length(data["category"], "Категория", 3),
                validate_positive_number(data["price"], "Цена"),
                validate_number(data["volume_ml"], "Объём"),
            ]
            for ok, msg in checks:
                if not ok:
                    self.error_label.config(text=msg)
                    messagebox.showerror("Ошибка", msg, parent=win)
                    return
            self.error_label.config(text="")

            conn = get_connection()
            try:
                if existing:
                    conn.execute("""
                        UPDATE drinks SET name=?, category=?, price=?, volume_ml=?
                        WHERE id=?
                    """, (data["name"], data["category"],
                          float(data["price"]),
                          int(data["volume_ml"]) if data["volume_ml"] else None,
                          existing["id"]))
                    log_action(self.user["login"], self.user["role_name"],
                               "UPDATE_DRINK", "SUCCESS")
                else:
                    conn.execute("""
                        INSERT INTO drinks (name, category, price, volume_ml, created_by)
                        VALUES (?, ?, ?, ?, ?)
                    """, (data["name"], data["category"],
                          float(data["price"]),
                          int(data["volume_ml"]) if data["volume_ml"] else None,
                          self.user["id"]))
                    log_action(self.user["login"], self.user["role_name"],
                               "CREATE_DRINK", "SUCCESS")
                conn.commit()
            except Exception as e:
                err = str(e)
                if "UNIQUE" in err:
                    self.error_label.config(text="Название напитка уже существует")
                    messagebox.showerror("Уникальность",
                                         "Напиток с таким названием уже есть в меню",
                                         parent=win)
                else:
                    messagebox.showerror("Ошибка БД", err, parent=win)
                log_action(self.user["login"], self.user["role_name"],
                           "SAVE_DRINK", f"FAIL_{e}")
                return
            finally:
                conn.close()
            win.destroy()
            self._load()

        ttk.Button(win, text="Сохранить", command=save).pack(pady=15)

    def _add(self):
        if self.user["role_name"] != "admin":
            messagebox.showinfo("Доступ", "Только администратор может добавлять напитки")
            return
        self._form()

    def _edit(self):
        if self.user["role_name"] != "admin":
            messagebox.showinfo("Доступ", "Только администратор может редактировать")
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Инфо", "Выберите запись")
            return
        item = self.tree.item(sel[0])["values"]
        conn = get_connection()
        row = conn.execute("SELECT * FROM drinks WHERE id=?", (item[0],)).fetchone()
        conn.close()
        self._form(dict(row))

    def _delete(self):
        if self.user["role_name"] != "admin":
            messagebox.showinfo("Доступ", "Только администратор может удалять")
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Инфо", "Выберите запись")
            return
        item = self.tree.item(sel[0])["values"]
        if not messagebox.askyesno(
                "Подтверждение",
                f"Вы действительно хотите удалить запись №{item[0]}? "
                "Это действие нельзя отменить, и все ваши котики умрут от грусти"):
            return
        conn = get_connection()
        conn.execute("DELETE FROM drinks WHERE id=?", (item[0],))
        conn.commit()
        conn.close()
        log_action(self.user["login"], self.user["role_name"],
                   "DELETE_DRINK", "SUCCESS")
        self._load()

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Экспорт меню"
        )
        if not path:
            return
        conn = get_connection()
        rows = conn.execute("SELECT id, name, category, price, volume_ml FROM drinks").fetchall()
        conn.close()
        export_to_csv(path,
                      ["ID", "Название", "Категория", "Цена", "Объём_мл"],
                      [tuple(r) for r in rows])
        log_action(self.user["login"], self.user["role_name"],
                   "EXPORT_DRINKS", "SUCCESS")
        messagebox.showinfo("Экспорт", f"Сохранено: {path}")