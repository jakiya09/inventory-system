from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DB init
def init_db():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        qty INTEGER,
        price REAL
    )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    total = sum([p[2] for p in products])

    return render_template("index.html", products=products, total=total)

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    qty = int(request.form["qty"])
    price = float(request.form["price"])

    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, qty, price) VALUES (?, ?, ?)", (name, qty, price))
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/add-daily", methods=["POST"])
def add_daily():
    name = request.form["name"]
    qty = int(request.form["qty"])

    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET qty = qty - ? WHERE name = ?", (qty, name))
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/upload-image", methods=["POST"])
def upload_image():
    file = request.files["image"]
    if file:
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, qty FROM products")
    data = cursor.fetchall()
    conn.close()

    names = [d[0] for d in data]
    qtys = [d[1] for d in data]

    return render_template("dashboard.html", names=names, qtys=qtys)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
