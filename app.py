from flask import Flask, render_template, request, redirect, session, Response
import sqlite3, os, csv, io

app = Flask(__name__)
app.secret_key = "lifebasket_final"

DB = "database.db"

# ================= DB INIT =================
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
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
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        if u == "admin" and p == "admin":
            session["user"] = "admin"
            return redirect("/")
        return redirect("/login")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= DASHBOARD =================
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    data = cur.fetchall()
    conn.close()

    return render_template("index.html", products=data)


# ================= ADD =================
@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect("/login")

    name = request.form["name"]
    qty = request.form["qty"]
    price = request.form["price"]

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name,qty,price) VALUES (?,?,?)",
                (name, qty, price))
    conn.commit()
    conn.close()

    return redirect("/")


# ================= DELETE =================
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


# ================= CSV EXPORT =================
@app.route("/export")
def export():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name,qty,price FROM products")
    rows = cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name","qty","price"])
    writer.writerows(rows)

    return Response(output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition":"attachment;filename=inventory.csv"})


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
