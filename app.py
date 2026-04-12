from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

def db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

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

with app.app_context():
    init_db()

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "1234":
            session["user"] = "admin"
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# HOME + SEARCH
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    search = request.args.get("q", "")

    conn = db()
    if search:
        products = conn.execute(
            "SELECT * FROM products WHERE name LIKE ?",
            ('%' + search + '%',)
        ).fetchall()
    else:
        products = conn.execute("SELECT * FROM products").fetchall()

    conn.close()
    return render_template("index.html", products=products)

# ADD
@app.route("/add", methods=["POST"])
def add():
    conn = db()
    conn.execute("INSERT INTO products (name, qty, price) VALUES (?, ?, ?)",
                 (request.form["name"], request.form["qty"], request.form["price"]))
    conn.commit()
    conn.close()
    return redirect("/")

# SELL
@app.route("/sell/<int:id>")
def sell(id):
    conn = db()
    conn.execute("UPDATE products SET qty = qty - 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

# RETURN
@app.route("/return/<int:id>")
def ret(id):
    conn = db()
    conn.execute("UPDATE products SET qty = qty + 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

# DELETE
@app.route("/delete/<int:id>")
def delete(id):
    conn = db()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
