from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# =========================
# ✅ DATABASE INIT
# =========================
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        qty INTEGER NOT NULL,
        price REAL NOT NULL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# 🏠 HOME PAGE
# =========================
@app.route("/")
def index():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    conn.close()

    return render_template("index.html", products=products)

# =========================
# ➕ ADD PRODUCT
# =========================
@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    qty = request.form["qty"]
    price = request.form["price"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO products (name, qty, price) VALUES (?, ?, ?)",
        (name, qty, price)
    )

    conn.commit()
    conn.close()

    return redirect("/")

# =========================
# ▶️ RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True)
