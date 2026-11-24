
import sqlite3

DB_NAME = "technova.db"

CATEGORIES = [
    "Смартфони",
    "Ноутбуки",
    "PlayStation",
    "Аксесуари"
]


def connect_db():
    return sqlite3.connect(DB_NAME)


def create_database():
    with connect_db() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                price REAL,
                description TEXT,
                image TEXT,
                FOREIGN KEY (category_id)
                    REFERENCES categories(id)
            )
        """)

        for category in CATEGORIES:
            cursor.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                (category,)
            )

    print("База данных создана!")
    print(f"Файл: {DB_NAME}")


def show_categories():
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()

    for category_id, name in rows:
        print(f"{category_id}. {name}")


def add_product():
    print("\nКатегории товарів:")
    show_categories()

    try:
        category_id = int(input("Номер категории: "))
        name = input("Название товара: ").strip()
        price_text = input("Цена (грн): ").strip()
        description = input("Описание: ").strip()
        image = input("Имя файла изображения: ").strip()

        if not name:
            print("Название не может быть пустым.")
            return

        price = float(price_text) if price_text else None

        if price is not None and price < 0:
            print("Цена не может быть отрицательной.")
            return

        with connect_db() as connection:
            category = connection.execute(
                "SELECT id FROM categories WHERE id = ?",
                (category_id,)
            ).fetchone()

            if category is None:
                print("Такой категории нет.")
                return

            connection.execute("""
                INSERT INTO products
                    (name, category_id, price, description, image)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                category_id,
                price,
                description,
                image
            ))

        print("Товар успешно добавлен!")

    except ValueError:
        print("Проверь номер категории и цену.")


def show_products():
    with connect_db() as connection:
        products = connection.execute("""
            SELECT
                products.id,
                products.name,
                categories.name,
                products.price
            FROM products
            JOIN categories
                ON products.category_id = categories.id
            ORDER BY products.id
        """).fetchall()

    if not products:
        print("В базе пока нет товаров.")
        return

    print("\nКАТАЛОГ TECHNOVA")

    for product_id, name, category, price in products:
        price_text = f"{price:.2f} грн" if price is not None else "Цена не указана"
        print(f"{product_id}. {name} | {category} | {price_text}")


def main():
    create_database()

    while True:
        print("\n--- TECHNOVA ---")
        print("1. Добавить товар")
        print("2. Показать все товары")
        print("3. Показать категории")
        print("0. Выход")

        choice = input("Выбери действие: ").strip()

        if choice == "1":
            add_product()
        elif choice == "2":
            show_products()
        elif choice == "3":
            show_categories()
        elif choice == "0":
            print("Работа завершена.")
            break
        else:
            print("Выбери пункт из меню.")


if __name__ == "__main__":
    main()
