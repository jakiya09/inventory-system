from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = "lifebasket_pro_key"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        qty INTEGER,
        price REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username,password) VALUES (?,?)",
                    ("admin","admin"))

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
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        user = cur.fetchone()
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


# ================= DASHBOARD =================
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    conn.close()

    return render_template("index.html", products=products)


# ================= ADD =================
@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    qty = request.form["qty"]
    price = request.form["price"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name,qty,price) VALUES (?,?,?)",
                (name,qty,price))
    conn.commit()
    conn.close()

    return redirect("/")


# ================= DELETE =================
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


# ================= CSV EXPORT =================
@app.route("/export")
def export():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM products", conn)
    df.to_csv("inventory.csv", index=False)
    conn.close()
    return "CSV Export Done"


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
