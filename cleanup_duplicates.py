
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "technova.db"

with sqlite3.connect(DB_PATH) as db:
    db.row_factory = sqlite3.Row

    # Проверяем товар, который нужно сохранить
    keep = db.execute("""
        SELECT id, name, price, image
        FROM products
        WHERE id = 29
    """).fetchone()

    if keep is None:
        raise SystemExit("ОШИБКА: товар с ID 29 не найден.")

    if (
        keep["name"] != "Samsung Galaxy A56"
        or keep["price"] != 15999
        or keep["image"] != "images/smartphones/samsung-a56.jpg"
    ):
        raise SystemExit(
            "ОШИБКА: данные товара ID 29 не совпадают. "
            "Ничего не удалено."
        )

    # Проверяем, что ID 30, 31 и 32 — дубликаты
    duplicates = db.execute("""
        SELECT id, name
        FROM products
        WHERE id IN (30, 31, 32)
        ORDER BY id
    """).fetchall()

    if (
        len(duplicates) != 3
        or any(row["name"] != "Samsung Galaxy A56"
               for row in duplicates)
    ):
        raise SystemExit(
            "ОШИБКА: записи отличаются от ожидаемых. "
            "Ничего не удалено."
        )

    print("Будет сохранён:")
    print(dict(keep))
    print("Будут удалены:")
    for row in duplicates:
        print(dict(row))

    answer = input("Для подтверждения введи УДАЛИТЬ: ")

    if answer != "УДАЛИТЬ":
        raise SystemExit("Отменено. Изменения не внесены.")

    db.execute("""
        DELETE FROM products
        WHERE id IN (30, 31, 32)
    """)

    print("Готово! Удалены только дубликаты ID 30, 31, 32.")
