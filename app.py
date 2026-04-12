from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = "lifebasket_secret"

# ================= DB INIT =================
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        qty INTEGER,
        price REAL,
        date TEXT DEFAULT (date('now'))
    )
    """)

    cursor.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1,'admin','admin')")

    conn.commit()
    conn.close()

init_db()

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        user = cursor.fetchone()

        conn.close()

        if user:
            session["user"] = u
            return redirect("/")
        return "Login Failed"

    return render_template("login.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= HOME =================
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    conn.close()

    return render_template("index.html", products=products)

# ================= ADD PRODUCT =================
@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    qty = request.form["qty"]
    price = request.form["price"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO products (name, qty, price) VALUES (?,?,?)",
                   (name, qty, price))

    conn.commit()
    conn.close()

    return redirect("/")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()

    chart_data = df.groupby("date")["qty"].sum().to_dict()

    return render_template("dashboard.html", data=chart_data)

# ================= CSV EXPORT =================
@app.route("/export")
def export():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM products", conn)
    df.to_csv("inventory.csv", index=False)
    conn.close()
    return "CSV Exported!"

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
