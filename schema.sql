-- Схема БД TechNova (SQLite). Безпечно запускати повторно.
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    price       REAL,
    description TEXT,
    image       TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);

INSERT OR IGNORE INTO categories (name) VALUES
    ('Смартфони'), ('Ноутбуки'), ('PlayStation'), ('Аксесуари');