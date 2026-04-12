from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

def db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# DB CREATE
def init_db():
    conn = db()
    conn.execute("""
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
def home():
    conn = db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("index.html", products=products)

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    qty = request.form["qty"]
    price = request.form["price"]

    conn = db()
    conn.execute("INSERT INTO products (name, qty, price) VALUES (?, ?, ?)",
                 (name, qty, price))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/sell/<int:id>")
def sell(id):
    conn = db()
    conn.execute("UPDATE products SET qty = qty - 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/return/<int:id>")
def ret(id):
    conn = db()
    conn.execute("UPDATE products SET qty = qty + 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/delete/<int:id>")
def delete(id):
    conn = db()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0")
