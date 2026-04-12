from flask import Flask, render_template, request, redirect, session, Response
import sqlite3, os, csv, io
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract

app = Flask(__name__)
app.secret_key = "lifebasket_pro"
DB = "database.db"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

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
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["user"] = "admin"
            return redirect("/")
        return "Invalid login"
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

# ================= ADD PRODUCT =================
@app.route("/add", methods=["POST"])
def add():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name, qty, price) VALUES (?,?,?)",
                (request.form["name"], request.form["qty"], request.form["price"]))
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

# ================= CSV/EXCEL IMPORT =================
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.reader(stream)

    next(reader)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    for row in reader:
        cur.execute("INSERT INTO products (name,qty,price) VALUES (?,?,?)",
                    (row[0],row[1],row[2]))

    conn.commit()
    conn.close()
    return redirect("/")

# ================= AI OCR IMAGE =================
@app.route("/ocr", methods=["POST"])
def ocr():
    file = request.files["image"]
    path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file.filename))
    file.save(path)

    text = pytesseract.image_to_string(Image.open(path))

    return f"<pre>{text}</pre>"

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
