from flask import Flask, render_template, request, redirect
import sqlite3
import os

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

with app.app_context():
    init_db()

@app.route("/")
def home():
    conn = db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("index.html", products=products)

if __name__ == "__main__":
    app.run(host="0.0.0.0")
