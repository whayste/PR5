import tkinter as tk
from tkinter import messagebox, ttk
from database import get_connection
from logger import log_action
from validators import (validate_non_empty, validate_min_length, validate_number)


class EmployeesWindow(tk.Toplevel):
    def __init__(self, parent, user):
        super().__init__(parent)
        self.user = user
        self.title("Сотрудники")
        self.geometry("900x520")
        self._build()
        self._load()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=5)

        ttk.Button(top, text="➕ Добавить", command=self._add).pack(side="left", padx=2)
        ttk.Button(top, text="✏️ Редактировать", command=self._edit).pack(side="left", padx=2)
        ttk.Button(top, text="🗑 Удалить", command=self._delete).pack(side="left", padx=2)

        ttk.Label(top, text="Поиск:").pack(side="left", padx=(20, 2))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        ttk.Entry(top, textvariable=self.search_var, width=25).pack(side="left")

        cols = ("id", "full_name", "position", "phone", "hire_date", "cafe")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.heading("id", text="№"); self.tree.column("id", width=40)
        self.tree.heading("full_name", text="ФИО"); self.tree.column("full_name", width=220)
        self.tree.heading("position", text="Должность"); self.tree.column("position", width=140)
        self.tree.heading("phone", text="Телефон"); self.tree.column("phone", width=130)
        self.tree.heading("hire_date", text="Дата найма"); self.tree.column("hire_date", width=110)
        self.tree.heading("cafe", text="Кофейня"); self.tree.column("cafe", width=200)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        q = self.search_var.get().strip().lower()
        # Бариста видит только сотрудников своей кофейни
        where = ""
        params = ()
        if self.user["role_name"] != "admin" and self.user.get("cafe_id"):
            where = " WHERE e.cafe_id = ?"
            params = (self.user["cafe_id"],)
        if q:
            where += (" AND " if where else " WHERE ") + \
                     "(LOWER(e.full_name) LIKE ? OR LOWER(e.position) LIKE ?)"
            params = params + (f"%{q}%", f"%{q}%")
        sql = f"""
            SELECT e.id, e.full_name, e.position, e.phone, e.hire_date, c.address as cafe
            FROM employees e LEFT JOIN cafes c ON e.cafe_id = c.id
            {where}
            ORDER BY e.id DESC
        """
        for r in conn.execute(sql, params):
            self.tree.insert("", "end", values=(
                r["id"], r["full_name"], r["position"],
                r["phone"] or "", r["hire_date"] or "", r["cafe"] or ""
            ))
        conn.close()

    def _form(self, existing=None):
        win = tk.Toplevel(self)
        win.title("Сотрудник")
        win.geometry("420x380")
        win.grab_set()

        fields = {}
        for label, key in [("ФИО", "full_name"), ("Должность", "position"),
                           ("Телефон", "phone"), ("Дата найма (ГГГГ-ММ-ДД)", "hire_date"),
                           ("ID кофейни", "cafe_id")]:
            ttk.Label(win, text=label + ":").pack(anchor="w", padx=10, pady=(8, 0))
            e = ttk.Entry(win, width=45)
            e.pack(padx=10)
            fields[key] = e
            if existing and existing.get(key) is not None:
                e.insert(0, existing[key])

        def save():
            data = {k: v.get().strip() for k, v in fields.items()}
            checks = [
                validate_non_empty(data["full_name"], "ФИО"),
                validate_min_length(data["full_name"], "ФИО", 3),
                validate_non_empty(data["position"], "Должность"),
                validate_min_length(data["position"], "Должность", 3),
                validate_number(data["cafe_id"], "ID кофейни", allow_empty=False),
            ]
            for ok, msg in checks:
                if not ok:
                    messagebox.showerror("Ошибка", msg, parent=win)
                    return
            conn = get_connection()
            try:
                if existing:
                    conn.execute("""
                        UPDATE employees SET full_name=?, position=?, phone=?,
                        hire_date=?, cafe_id=? WHERE id=?
                    """, (data["full_name"], data["position"],
                          data["phone"] or None, data["hire_date"] or None,
                          int(data["cafe_id"]), existing["id"]))
                    log_action(self.user["login"], self.user["role_name"],
                               "UPDATE_EMPLOYEE", "SUCCESS")
                else:
                    conn.execute("""
                        INSERT INTO employees (full_name, position, phone, hire_date,
                        cafe_id, created_by) VALUES (?,?,?,?,?,?)
                    """, (data["full_name"], data["position"],
                          data["phone"] or None, data["hire_date"] or None,
                          int(data["cafe_id"]), self.user["id"]))
                    log_action(self.user["login"], self.user["role_name"],
                               "CREATE_EMPLOYEE", "SUCCESS")
                conn.commit()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e), parent=win)
                return
            finally:
                conn.close()
            win.destroy()
            self._load()

        ttk.Button(win, text="Сохранить", command=save).pack(pady=15)

    def _add(self):
        if self.user["role_name"] != "admin":
            messagebox.showinfo("Доступ", "Только администратор может добавлять сотрудников")
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
        row = conn.execute("SELECT * FROM employees WHERE id=?", (item[0],)).fetchone()
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
        conn.execute("DELETE FROM employees WHERE id=?", (item[0],))
        conn.commit()
        conn.close()
        log_action(self.user["login"], self.user["role_name"],
                   "DELETE_EMPLOYEE", "SUCCESS")
        self._load()