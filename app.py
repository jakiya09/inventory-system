from flask import Flask, render_template, request, redirect, Response, session
import sqlite3, os, re
import pandas as pd
from PIL import Image
import pytesseract
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# OCR path (change if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# DB init
def init_db():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        qty INTEGER,
        price REAL,
        date TEXT
    )
    """)
    conn.commit()
    conn.close()

# Login
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "1234":
            session["user"] = "admin"
            return redirect("/")
    return render_template("login.html")

# Home
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    total = sum([p[2] for p in products])

    return render_template("index.html", products=products, total=total)

# Add product (with date)
@app.route("/add", methods=["POST"])
def add():
    name = request.form.get("name")
    qty = int(request.form.get("qty",0))
    price = float(request.form.get("price",0))
    date = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, qty, price, date) VALUES (?,?,?,?)",
        (name, qty, price, date)
    )
    conn.commit()
    conn.close()

    return redirect("/")

# CSV Export
@app.route("/export")
def export():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, qty, price, date FROM products")
    data = cursor.fetchall()
    conn.close()

    def generate():
        yield "Name,Qty,Price,Date\n"
        for row in data:
            yield f"{row[0]},{row[1]},{row[2]},{row[3]}\n"

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition":"attachment;filename=data.csv"})

# CSV Upload
@app.route("/upload-csv", methods=["POST"])
def upload_csv():
    file = request.files.get("file")
    if not file:
        return redirect("/")

    df = pd.read_csv(file)

    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()

    for _, row in df.iterrows():
        name = row.get("Name","")
        qty = int(row.get("Qty",0) or 0)
        price = float(row.get("Price",0) or 0)
        date = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("INSERT INTO products (name, qty, price, date) VALUES (?,?,?,?)",
                       (name, qty, price, date))

    conn.commit()
    conn.close()

    return redirect("/")

# AI Detect
@app.route("/detect-image", methods=["POST"])
def detect_image():
    file = request.files.get("image")
    if not file:
        return "No file"

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    img = Image.open(path)
    text = pytesseract.image_to_string(img)

    numbers = re.findall(r'\d+', text)
    total = sum([int(n) for n in numbers])

    return f"Detected Total Quantity: {total}"

# Dashboard (date-wise)
@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, SUM(qty) FROM products GROUP BY date")
    data = cursor.fetchall()
    conn.close()

    dates = [d[0] for d in data]
    qtys = [d[1] for d in data]

    return render_template("dashboard.html", dates=dates, qtys=qtys)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000)
