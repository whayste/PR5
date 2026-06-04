import sqlite3
import hashlib

DB_NAME = "kostroma_coffee.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        position TEXT NOT NULL,           -- специфичное поле для кофейни
        cafe_id INTEGER,
        role_id INTEGER NOT NULL,
        dark_theme INTEGER DEFAULT 0,
        failed_attempts INTEGER DEFAULT 0,
        locked_until TEXT,
        FOREIGN KEY (role_id) REFERENCES roles(id),
        FOREIGN KEY (cafe_id) REFERENCES cafes(id)
    );

    CREATE TABLE IF NOT EXISTS cafes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT UNIQUE NOT NULL,
        work_hours TEXT NOT NULL,
        manager_name TEXT,
        created_by INTEGER,
        FOREIGN KEY (created_by) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS drinks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,           -- Coffee / Tea / Dessert / Other
        price REAL NOT NULL,
        volume_ml INTEGER,
        created_by INTEGER,
        FOREIGN KEY (created_by) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        position TEXT NOT NULL,
        phone TEXT,
        hire_date TEXT,
        cafe_id INTEGER NOT NULL,
        created_by INTEGER,
        FOREIGN KEY (cafe_id) REFERENCES cafes(id),
        FOREIGN KEY (created_by) REFERENCES users(id)
    );

    INSERT OR IGNORE INTO roles (name) VALUES ('admin'), ('barista');
    """)
    conn.commit()

    # Дефолтный админ: admin / Admin123!
    cur.execute("SELECT id FROM users WHERE login = 'admin'")
    if not cur.fetchone():
        pwd_hash = hashlib.sha256("Admin123!".encode()).hexdigest()
        cur.execute(
            "INSERT INTO users (login, password_hash, email, full_name, position, role_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", pwd_hash, "owner@kostromacoffee.ru",
             "Управляющий сетью", "Директор", 1)
        )
        conn.commit()
    conn.close()