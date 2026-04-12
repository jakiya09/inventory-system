from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "lifebasket"

# ---------------- DB INIT ----------------
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

# ---------------- HOME ----------------
@app.route("/")
def index():
    init_db()  # 🔥 IMPORTANT FIX

    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    return render_template("index.html", products=products)

# ---------------- ADD PRODUCT ----------------
@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    qty = request.form["qty"]
    price = request.form["price"]

    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, qty, price) VALUES (?, ?, ?)",
                   (name, qty, price))
    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    init_db()

    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, qty FROM products")
    data = cursor.fetchall()
    conn.close()

    names = [d[0] for d in data]
    qtys = [d[1] for d in data]

    return render_template("dashboard.html", names=names, qtys=qtys)

# ---------------- LOGIN SIMPLE ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "1234":
            session["user"] = "admin"
            return redirect("/")
        return "Wrong login"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000)
