from flask import Flask, render_template, request, redirect, send_file, session
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "lifebasket-secret"

DB = "database.db"

# ---------------- DB INIT ----------------
def init_db():
    conn = sqlite3.connect(DB)
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

init_db()

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form["username"]
        return redirect("/")
    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- HOME ----------------
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    return render_template("index.html", products=products)

# ---------------- ADD PRODUCT ----------------
@app.route("/add", methods=["POST"])
def add():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO products (name, qty, price) VALUES (?, ?, ?)",
        (request.form["name"], request.form["qty"], request.form["price"])
    )

    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- CSV EXPORT ----------------
@app.route("/export")
def export():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()

    file = "products.csv"
    df.to_csv(file, index=False)

    return send_file(file, as_attachment=True)

# ---------------- CSV IMPORT ----------------
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    df = pd.read_csv(file)

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute(
            "INSERT INTO products (name, qty, price) VALUES (?, ?, ?)",
            (row["name"], row["qty"], row["price"])
        )

    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
