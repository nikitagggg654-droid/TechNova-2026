import math
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, flash, redirect, render_template, request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "technova.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"

app = Flask(__name__)  # папки templates/ та static/ підхоплюються автоматично

# Секрети — лише зі змінних оточення (репозиторій публічний!)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("TECHNOVA_PRODUCTION") == "1",
    MAX_CONTENT_LENGTH=1024 * 1024,
)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
ALLOWED_IMAGE_TYPES = (".jpg", ".jpeg", ".png", ".webp", ".gif")

PRODUCT_SELECT = """
    SELECT p.id, p.name, c.name AS category,
           p.price, p.description, p.image
    FROM products p
    JOIN categories c ON c.id = p.category_id
"""

# ==================== БАЗА ДАНИХ ====================

@contextmanager
def get_db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with get_db() as db:
        db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

        # міграція старої таблиці users (без is_admin)
        columns = [r["name"] for r in db.execute("PRAGMA table_info(users)")]
        if "is_admin" not in columns:
            db.execute(
                "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"
            )
            db.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")

        if db.execute("SELECT 1 FROM users WHERE is_admin = 1").fetchone() is None:
            password = os.environ.get("TECHNOVA_ADMIN_PASSWORD", "")
            if len(password) < 8:
                raise RuntimeError(
                    "Задайте змінну оточення TECHNOVA_ADMIN_PASSWORD "
                    "(мінімум 8 символів) для створення адміністратора."
                )
            db.execute(
                "INSERT INTO users (username, password_hash, is_admin) "
                "VALUES (?, ?, 1)",
                ("admin", generate_password_hash(password)),
            )


def find_category_id(db, name):
    row = db.execute(
        "SELECT id FROM categories WHERE name = ?", (name,)
    ).fetchone()
    return row["id"] if row else None


def get_categories(db):
    return db.execute("SELECT id, name FROM categories ORDER BY id").fetchall()


# ==================== БЕЗПЕКА ====================

def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def csrf_protect():
    if request.method == "POST":
        sent = request.form.get("csrf_token", "").encode()
        real = session.get("csrf_token", "").encode()
        if not real or not secrets.compare_digest(sent, real):
            abort(400)


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Спочатку увійдіть в обліковий запис.", "error")
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            abort(403)
        return function(*args, **kwargs)
    return wrapper


@app.template_filter("price")
def price_filter(value):
    if value is None:
        return "Ціну не вказано"
    return f"{value:,.0f}".replace(",", "\u00a0") + " грн"


# ==================== ПУБЛІЧНІ СТОРІНКИ ====================

@app.get("/")
def index():
    selected = request.args.get("category", "").strip()
    query = request.args.get("q", "").strip()

    with get_db() as db:
        categories = get_categories(db)
        sql, params = PRODUCT_SELECT, ()
        if selected:
            sql += " WHERE c.name = ?"
            params = (selected,)
        rows = db.execute(sql + " ORDER BY p.id DESC", params).fetchall()

    needle = query.casefold()
    groups = {}
    for row in rows:
        text = f"{row['name']} {row['description'] or ''}".casefold()
        if needle and needle not in text:
            continue
        groups.setdefault(row["category"], []).append(row)

    total = sum(len(items) for items in groups.values())
    return render_template(
        "index.html", categories=categories, groups=groups,
        total=total, selected=selected, query=query,
    )


@app.get("/product/<int:product_id>")
def product_page(product_id):
    with get_db() as db:
        product = db.execute(
            PRODUCT_SELECT + " WHERE p.id = ?", (product_id,)
        ).fetchone()
    if product is None:
        abort(404)
    return render_template("product.html", product=product)


# ==================== РЕЄСТРАЦІЯ / ВХІД / ВИХІД ====================

@app.route("/register", methods=["GET", "POST"])
def register():
    username = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        error = None

        if not USERNAME_RE.match(username):
            error = "Логін: 3–30 символів, латиниця, цифри та _."
        elif len(password) < 8:
            error = "Пароль має містити щонайменше 8 символів."
        elif password != confirm:
            error = "Паролі не збігаються."
        else:
            try:
                with get_db() as db:
                    db.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, generate_password_hash(password)),
                    )
            except sqlite3.IntegrityError:
                error = "Такий логін уже зайнятий."

        if error is None:
            flash("Реєстрація успішна. Тепер увійдіть.", "success")
            return redirect(url_for("login"))

        flash(error, "error")
        return render_template("register.html", username=username), 400

    return render_template("register.html", username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db() as db:
            user = db.execute(
                "SELECT id, username, password_hash, is_admin "
                "FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Невірний логін або пароль.", "error")
            return render_template("login.html", username=username), 401

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["is_admin"] = bool(user["is_admin"])
        flash("Вхід виконано.", "success")
        return redirect(url_for("admin_panel" if user["is_admin"] else "index"))

    return render_template("login.html", username="")


@app.post("/logout")
def logout():
    session.clear()
    flash("Ви вийшли з облікового запису.", "success")
    return redirect(url_for("index"))


# ==================== АДМІН-ПАНЕЛЬ (CRUD) ====================

def validate_product(data):
    name = data.get("name", "").strip()
    category = data.get("category", "").strip()
    description = data.get("description", "").strip()
    image = data.get("image", "").strip()

    if not name:
        return None, "Вкажіть назву товару."
    if len(name) > 150:
        return None, "Назва не має перевищувати 150 символів."
    if not category:
        return None, "Оберіть категорію."
    if len(description) > 2000:
        return None, "Опис не має перевищувати 2000 символів."
    if len(image) > 500:
        return None, "Занадто довгий шлях до зображення."

    try:
        price = float(data.get("price", "").replace(",", "."))
        if not math.isfinite(price) or price < 0 or price > 100000000:
            raise ValueError
    except ValueError:
        return None, "Вкажіть коректну ціну."

    if image:
        path = Path(image)
        if (
            not image.startswith("images/")
            or path.is_absolute()
            or ".." in path.parts
            or "\\" in image
            or ":" in image
            or any(part.startswith(".") for part in path.parts)
        ):
            return None, "Зображення має бути всередині static/images/."
        if path.suffix.lower() not in ALLOWED_IMAGE_TYPES:
            return None, "Непідтримуваний формат зображення."

    return {
        "name": name, "category": category, "price": price,
        "description": description, "image": image,
    }, None


@app.get("/admin")
@admin_required
def admin_panel():
    with get_db() as db:
        products = db.execute(PRODUCT_SELECT + " ORDER BY p.id DESC").fetchall()
    return render_template("admin.html", products=products)


def save_product(product_id=None):
    form = request.form.to_dict()
    data, error = validate_product(form)

    with get_db() as db:
        categories = get_categories(db)

        if error is None:
            category_id = find_category_id(db, data["category"])
            if category_id is None:
                error = "Оберіть існуючу категорію."

        if error is None:
            values = (
                data["name"], category_id, data["price"],
                data["description"], data["image"],
            )
            if product_id is None:
                db.execute(
                    "INSERT INTO products "
                    "(name, category_id, price, description, image) "
                    "VALUES (?, ?, ?, ?, ?)",
                    values,
                )
                flash("Товар додано.", "success")
            else:
                cursor = db.execute(
                    "UPDATE products SET name = ?, category_id = ?, price = ?, "
                    "description = ?, image = ? WHERE id = ?",
                    values + (product_id,),
                )
                if cursor.rowcount == 0:
                    abort(404)
                flash("Зміни збережено.", "success")
            return redirect(url_for("admin_panel"))

    flash(error, "error")
    return render_template(
        "product_form.html", categories=categories,
        product=form, product_id=product_id,
    ), 400


@app.route("/admin/products/new", methods=["GET", "POST"])
@admin_required
def product_new():
    if request.method == "POST":
        return save_product()
    with get_db() as db:
        categories = get_categories(db)
    return render_template(
        "product_form.html", categories=categories, product={}, product_id=None
    )


@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def product_edit(product_id):
    if request.method == "POST":
        return save_product(product_id)
    with get_db() as db:
        categories = get_categories(db)
        row = db.execute(
            PRODUCT_SELECT + " WHERE p.id = ?", (product_id,)
        ).fetchone()
    if row is None:
        abort(404)
    return render_template(
        "product_form.html", categories=categories,
        product=dict(row), product_id=product_id,
    )


@app.post("/admin/products/<int:product_id>/delete")
@admin_required
def product_delete(product_id):
    with get_db() as db:
        cursor = db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    if cursor.rowcount == 0:
        abort(404)
    flash("Товар видалено.", "success")
    return redirect(url_for("admin_panel"))


# ==================== СТОРІНКИ ПОМИЛОК ====================

ERROR_TEXT = {
    400: "Некоректний запит. Оновіть сторінку та спробуйте ще раз.",
    403: "Недостатньо прав для перегляду цієї сторінки.",
    404: "Сторінку не знайдено.",
    500: "Внутрішня помилка сервера.",
}


def render_error(error):
    code = getattr(error, "code", 500)
    return render_template(
        "error.html", code=code,
        message=ERROR_TEXT.get(code, "Сталася помилка."),
    ), code


for _code in ERROR_TEXT:
    app.register_error_handler(_code, render_error)

# ==================== ЗАПУСК ====================

initialize_database()  # також на хостингу (WSGI)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)