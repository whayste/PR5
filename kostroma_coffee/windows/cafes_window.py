import tkinter as tk
from tkinter import messagebox, ttk
from database import get_connection
from logger import log_action
from validators import validate_non_empty, validate_min_length


class CafesWindow(tk.Toplevel):
    def __init__(self, parent, user):
        super().__init__(parent)
        self.user = user
        self.title("Кофейни сети")
        self.geometry("850x480")
        self._build()
        self._load()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=5)
        ttk.Button(top, text="➕ Добавить", command=self._add).pack(side="left", padx=2)
        ttk.Button(top, text="✏️ Редактировать", command=self._edit).pack(side="left", padx=2)
        ttk.Button(top, text="🗑 Удалить", command=self._delete).pack(side="left", padx=2)

        cols = ("id", "address", "work_hours", "manager_name")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.heading("id", text="№"); self.tree.column("id", width=40)
        self.tree.heading("address", text="Адрес"); self.tree.column("address", width=320)
        self.tree.heading("work_hours", text="Режим работы"); self.tree.column("work_hours", width=150)
        self.tree.heading("manager_name", text="Управляющий")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        for r in conn.execute("SELECT * FROM cafes ORDER BY id DESC"):
            self.tree.insert("", "end", values=(
                r["id"], r["address"], r["work_hours"], r["manager_name"] or ""
            ))
        conn.close()

    def _form(self, existing=None):
        win = tk.Toplevel(self)
        win.title("Кофейня")
        win.geometry("420x300")
        win.grab_set()

        fields = {}
        for label, key in [("Адрес", "address"), ("Режим работы", "work_hours"),
                           ("Управляющий", "manager_name")]:
            ttk.Label(win, text=label + ":").pack(anchor="w", padx=10, pady=(8, 0))
            e = ttk.Entry(win, width=45)
            e.pack(padx=10)
            fields[key] = e
            if existing and existing.get(key):
                e.insert(0, existing[key])

        self.error_label = tk.Label(win, text="", fg="red")
        self.error_label.pack(pady=5)

        def save():
            data = {k: v.get().strip() for k, v in fields.items()}
            checks = [
                validate_non_empty(data["address"], "Адрес"),
                validate_min_length(data["address"], "Адрес", 3),
                validate_non_empty(data["work_hours"], "Режим работы"),
                validate_min_length(data["work_hours"], "Режим работы", 3),
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
                        UPDATE cafes SET address=?, work_hours=?, manager_name=? WHERE id=?
                    """, (data["address"], data["work_hours"],
                          data["manager_name"] or None, existing["id"]))
                    log_action(self.user["login"], self.user["role_name"],
                               "UPDATE_CAFE", "SUCCESS")
                else:
                    conn.execute("""
                        INSERT INTO cafes (address, work_hours, manager_name, created_by)
                        VALUES (?,?,?,?)
                    """, (data["address"], data["work_hours"],
                          data["manager_name"] or None, self.user["id"]))
                    log_action(self.user["login"], self.user["role_name"],
                               "CREATE_CAFE", "SUCCESS")
                conn.commit()
            except Exception as e:
                err = str(e)
                if "UNIQUE" in err:
                    self.error_label.config(text="Кофейня с таким адресом уже есть")
                    messagebox.showerror("Уникальность",
                                         "Кофейня по такому адресу уже зарегистрирована",
                                         parent=win)
                else:
                    messagebox.showerror("Ошибка БД", err, parent=win)
                return
            finally:
                conn.close()
            win.destroy()
            self._load()

        ttk.Button(win, text="Сохранить", command=save).pack(pady=15)

    def _add(self):
        if self.user["role_name"] != "admin":
            messagebox.showinfo("Доступ", "Только администратор может добавлять кофейни")
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
        row = conn.execute("SELECT * FROM cafes WHERE id=?", (item[0],)).fetchone()
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
        conn.execute("DELETE FROM cafes WHERE id=?", (item[0],))
        conn.commit()
        conn.close()
        log_action(self.user["login"], self.user["role_name"],
                   "DELETE_CAFE", "SUCCESS")
        self._load()