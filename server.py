
import json
import sqlite3
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "technova.db"
HOST = "127.0.0.1"
PORT = 8000


class TechNovaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/products":
            self.send_products()
            return

        if path == "/api/categories":
            self.send_categories()
            return

        super().do_GET()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_products(self):
        if not DB_PATH.exists():
            self.send_json({"error": "База technova.db не найдена"}, 500)
            return

        try:
            with sqlite3.connect(DB_PATH) as connection:
                connection.row_factory = sqlite3.Row

                rows = connection.execute("""
                    SELECT
                        p.id,
                        p.name,
                        c.name AS category,
                        p.price,
                        p.description,
                        p.image
                    FROM products AS p
                    JOIN categories AS c ON c.id = p.category_id
                    ORDER BY p.id
                """).fetchall()

                products = [dict(row) for row in rows]

            self.send_json(products)

        except sqlite3.Error as error:
            self.send_json(
                {"error": f"Ошибка базы данных: {error}"},
                500
            )

    def send_categories(self):
        if not DB_PATH.exists():
            self.send_json({"error": "База technova.db не найдена"}, 500)
            return

        try:
            with sqlite3.connect(DB_PATH) as connection:
                rows = connection.execute("""
                    SELECT id, name
                    FROM categories
                    ORDER BY id
                """).fetchall()

            self.send_json([
                {"id": row[0], "name": row[1]}
                for row in rows
            ])

        except sqlite3.Error as error:
            self.send_json(
                {"error": f"Ошибка базы данных: {error}"},
                500
            )


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), TechNovaHandler)

    print("TechNova запущен!")
    print("Сайт: http://127.0.0.1:8000/")
    print("Товары: http://127.0.0.1:8000/api/products")
    print("Категории: http://127.0.0.1:8000/api/categories")
    print("Для остановки нажми Ctrl+C.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        server.server_close()
