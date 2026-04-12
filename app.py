from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import pytesseract

app = Flask(__name__)
app.secret_key = "lifebasket_secret"

# ================= DB INIT =================
def init_db():
    conn = sqlite3.connect("database.db")
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

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u == "admin" and p == "admin":
            session["user"] = u
            return redirect("/")
        return "Invalid Login"

    return render_template("login.html")


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
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO products (name, qty, price) VALUES (?, ?, ?)",
        (request.form["name"], request.form["qty"], request.form["price"])
    )

    conn.commit()
    conn.close()
    return redirect("/")


# ================= DELETE =================
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


# ================= CSV EXPORT =================
@app.route("/export")
def export():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM products", conn)
    file = "export.csv"
    df.to_csv(file, index=False)
    conn.close()
    return send_file(file, as_attachment=True)


# ================= CSV IMPORT =================
@app.route("/import", methods=["POST"])
def import_csv():
    file = request.files["file"]
    df = pd.read_csv(file)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("INSERT INTO products (name, qty, price) VALUES (?, ?, ?)",
                       (row["name"], row["qty"], row["price"]))

    conn.commit()
    conn.close()
    return redirect("/")


# ================= AI SCREENSHOT OCR =================
@app.route("/ai_upload", methods=["POST"])
def ai_upload():
    img = Image.open(request.files["image"])
    text = pytesseract.image_to_string(img)

    return f"<h3>Detected Text:</h3><pre>{text}</pre>"


# ================= DASHBOARD CHART =================
@app.route("/chart")
def chart():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT name, qty FROM products", conn)

    plt.figure(figsize=(5,3))
    plt.bar(df["name"], df["qty"])
    plt.xticks(rotation=45)
    plt.tight_layout()

    file = "chart.png"
    plt.savefig(file)
    conn.close()

    return send_file(file, mimetype="image/png")


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
