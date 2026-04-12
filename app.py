import sqlite3, csv, io
from flask import Flask, render_template, request, redirect, send_file

app = Flask(__name__)

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

init_db()

@app.route("/")
def home():
    conn = db()
    products = conn.execute("SELECT * FROM products").fetchall()
    total = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    conn.close()
    return render_template("index.html", products=products, total=total)

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

@app.route("/delete/<int:id>")
def delete(id):
    conn = db()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/edit/<int:id>", methods=["POST"])
def edit(id):
    name = request.form["name"]
    qty = request.form["qty"]
    price = request.form["price"]

    conn = db()
    conn.execute("UPDATE products SET name=?, qty=?, price=? WHERE id=?",
                 (name, qty, price, id))
    conn.commit()
    conn.close()
    return redirect("/")

# ✅ CSV Export
@app.route("/export")
def export():
    conn = db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Qty", "Price"])

    for p in products:
        writer.writerow([p["name"], p["qty"], p["price"]])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype="text/csv",
                     download_name="inventory.csv",
                     as_attachment=True)

# ✅ Excel Upload (CSV file)
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]

    stream = io.StringIO(file.stream.read().decode("UTF8"))
    csv_reader = csv.reader(stream)

    conn = db()

    for row in csv_reader:
        if len(row) == 3:
            conn.execute("INSERT INTO products (name, qty, price) VALUES (?, ?, ?)",
                         (row[0], row[1], row[2]))

    conn.commit()
    conn.close()

    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
