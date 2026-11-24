
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / "technova.db"

print("Проверяем базу:", db_path)

with sqlite3.connect(db_path) as db:
    # Показываем все таблицы базы данных
    tables = db.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()

    print("\nТАБЛИЦЫ БАЗЫ ДАННЫХ:")

    for (table,) in tables:
        print(f"\n--- Таблица: {table} ---")

        # Показываем столбцы и первичные ключи
        columns = db.execute(
            f'PRAGMA table_info("{table}")'
        ).fetchall()

        for column in columns:
            print(
                f"Столбец: {column[1]}, "
                f"тип: {column[2]}, "
                f"первичный ключ: {'Да' if column[5] else 'Нет'}"
            )

        # Показываем внешние ключи
        foreign_keys = db.execute(
            f'PRAGMA foreign_key_list("{table}")'
        ).fetchall()

        if foreign_keys:
            print("Внешние ключи:")
            for key in foreign_keys:
                print(
                    f"  {key[3]} -> "
                    f"{key[2]}.{key[4]}"
                )
        else:
            print("Внешние ключи: нет")

    # Отдельно проверяем количество товаров
    try:
        count = db.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]
        print(f"\nВсего товаров: {count}")
    except sqlite3.OperationalError:
        print("\nТаблица products не найдена.")
