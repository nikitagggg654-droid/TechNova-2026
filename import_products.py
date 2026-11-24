
import sqlite3

DB_NAME = "technova.db"

products = [
    # Смартфони
    ("iPhone 16 Pro", "Смартфони", 49999, 'Екран 6.3", Apple A18 Pro, 8 ГБ RAM, 256 ГБ, камера 48 Мп', "images/smartphones/iphone.jpg"),
    ("Samsung Galaxy S25", "Смартфони", 39999, '6.2", 256 ГБ, 5G', "images/smartphones/samsung.jpg"),
    ("Xiaomi 15", "Смартфони", 29999, '6.36", 512 ГБ, 5G', "images/smartphones/xiaomi.jpg"),
    ("Google Pixel 9", "Смартфони", 31999, '6.3", 128 ГБ, 5G', "images/smartphones/pixel.jpg"),

    # Ноутбуки
    ("Apple MacBook Air 15", "Ноутбуки", 54999, '15.3", Apple M3, 16 ГБ', "images/laptops/macbook-air.jpg"),
    ("ASUS Vivobook 16", "Ноутбуки", 32999, '16", Intel Core i5, 16 ГБ', "images/laptops/asus-vivobook.jpg"),
    ("Lenovo IdeaPad 5", "Ноутбуки", 29999, '15.6", Ryzen 5, 16 ГБ', "images/laptops/lenovo-ideapad.jpg"),
    ("HP Pavilion 15", "Ноутбуки", 31999, '15.6", Intel Core i5, 16 ГБ', "images/laptops/hp-pavilion.jpg"),
    ("Acer Aspire 5", "Ноутбуки", 27999, '15.6", Intel Core i5, 16 ГБ', "images/laptops/acer-aspire.jpg"),
    ("Dell Inspiron 15", "Ноутбуки", 36999, '15.6", Intel Core i7, 16 ГБ', "images/laptops/dell-inspiron.jpg"),
    ("MSI Katana 15", "Ноутбуки", 49999, '15.6", Core i7, RTX 4060', "images/laptops/msi-katana.jpg"),
    ("Samsung Galaxy Book4", "Ноутбуки", 42999, '15.6", Intel Core i7, 16 ГБ', "images/laptops/samsung-galaxy-book.jpg"),

    # PlayStation
    ("PlayStation 5", "PlayStation", 24999, '4K, SSD 1 ТБ, DualSense', "images/playstation/ps5.jpg"),
    ("PlayStation 5 Slim", "PlayStation", 26999, '4K, SSD 1 ТБ, 120 Гц', "images/playstation/ps5-slim.jpg"),
    ("PlayStation 5 Pro", "PlayStation", 34999, '4K, SSD 2 ТБ, 8K', "images/playstation/ps5-pro.jpg"),
    ("PlayStation 4 Pro", "PlayStation", 16999, '4K, HDR, SSD', "images/playstation/ps4-pro.jpg"),
    ("PlayStation 4 Slim", "PlayStation", 12999, 'Full HD, 500 ГБ, HDR', "images/playstation/ps4-slim.jpg"),
    ("PlayStation Portal", "PlayStation", 10999, '8", Full HD, Wi-Fi', "images/playstation/playstation-portal.jpg"),
    ("PlayStation VR2", "PlayStation", 22999, 'VR, OLED, 2000×2040', "images/playstation/playstation-vr2.jpg"),
    ("DualSense Wireless Controller", "PlayStation", 2999, 'PS5, Wireless, USB-C', "images/playstation/dualsense.jpg"),

    # Аксесуари
    ("AirPods Pro", "Аксесуари", 8999, 'ANC, Bluetooth, USB-C', "images/accessories/airpods-pro.jpg"),
    ("Magic Keyboard", "Аксесуари", 4999, 'Wireless, Bluetooth, USB-C', "images/accessories/magic-keyboard.jpg"),
    ("Gaming Mouse Pro", "Аксесуари", 2499, '26000 DPI, RGB, Wireless', "images/accessories/gaming-mouse.jpg"),
    ("TechCam 4K", "Аксесуари", 3499, '4K, 30 FPS, Microphone', "images/accessories/webcam.jpg"),
    ("PowerBank Ultra", "Аксесуари", 2299, '20 000 мА·год, 65W, USB-C', "images/accessories/powerbank.jpg"),
    ("Docking Station Pro", "Аксесуари", 3999, 'USB-C, HDMI, 10 портів', "images/accessories/docking-station.jpg"),
    ("SmartWatch X", "Аксесуари", 4499, 'AMOLED, GPS, Bluetooth', "images/accessories/smartwatch.jpg"),
    ("SoundBox Mini", "Аксесуари", 2799, 'Bluetooth, 20W, 12 год', "images/accessories/speaker.jpg"),
]


def import_products():
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()

        # Создаём таблицы, если их ещё нет
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
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        # Добавляем категории
        categories = [
            "Смартфони",
            "Ноутбуки",
            "PlayStation",
            "Аксесуари"
        ]

        for category in categories:
            cursor.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                (category,)
            )

        added = 0
        skipped = 0

        # Переносим товары в базу
        for name, category, price, description, image in products:
            category_row = cursor.execute(
                "SELECT id FROM categories WHERE name = ?",
                (category,)
            ).fetchone()

            category_id = category_row[0]

            existing = cursor.execute(
                "SELECT id FROM products WHERE name = ?",
                (name,)
            ).fetchone()

            if existing:
                skipped += 1
                continue

            cursor.execute("""
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

            added += 1

        total = cursor.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

    print("Импорт завершён!")
    print(f"Добавлено товаров: {added}")
    print(f"Пропущено повторов: {skipped}")
    print(f"Всего товаров в базе: {total}")


if __name__ == "__main__":
    import_products()
