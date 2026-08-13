from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import requests

app = Flask(__name__)
CORS(app)

DATABASE = "library.db"

# ----------------------------
# Database Connection
# ----------------------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------------
# Create Database Table
# ----------------------------
def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        price REAL,
        description TEXT,
        image TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ----------------------------
# Home Page
# ----------------------------
@app.route("/")
def home():
    return render_template("index.html")

# ----------------------------
# Get All Books
# ----------------------------
@app.route("/books", methods=["GET"])
def get_books():

    conn = get_db()

    books = conn.execute("SELECT * FROM books").fetchall()

    conn.close()

    return jsonify([dict(book) for book in books])

# ----------------------------
# Add Book
# ----------------------------
@app.route("/books", methods=["POST"])
def add_book():

    data = request.json

    conn = get_db()

    conn.execute("""
    INSERT INTO books(title,author,price,description,image)
    VALUES(?,?,?,?,?)
    """,(

        data["title"],
        data["author"],
        data["price"],
        data["description"],
        data["image"]

    ))

    conn.commit()
    conn.close()

    return jsonify({"message":"Book Added Successfully"})

# ----------------------------
# Delete Book
# ----------------------------
@app.route("/books/<int:id>", methods=["DELETE"])
def delete_book(id):

    conn = get_db()

    conn.execute("DELETE FROM books WHERE id=?",(id,))

    conn.commit()
    conn.close()

    return jsonify({"message":"Book Deleted Successfully"})

# ----------------------------
# Search Book
# ----------------------------
@app.route("/search")
def search():

    keyword = request.args.get("q","")

    conn = get_db()

    books = conn.execute("""

    SELECT * FROM books

    WHERE title LIKE ?

    OR author LIKE ?

    """,(

        f"%{keyword}%",

        f"%{keyword}%"

    )).fetchall()

    conn.close()

    return jsonify([dict(book) for book in books])

# ----------------------------
# Import Real Books
# ----------------------------
@app.route("/import")
def import_books():

    keyword = request.args.get("q","python")

    url = f"https://www.googleapis.com/books/v1/volumes?q={keyword}&maxResults=20"

    response = requests.get(url)

    data = response.json()

    conn = get_db()

    count = 0

    for item in data.get("items",[]):

        info = item.get("volumeInfo",{})

        title = info.get("title","Unknown")

        author = ", ".join(info.get("authors",["Unknown"]))

        description = info.get("description","No Description Available")

        image = ""

        if "imageLinks" in info:
            image = info["imageLinks"].get("thumbnail","")

        # Prevent duplicate books
        exists = conn.execute(
            "SELECT * FROM books WHERE title=? AND author=?",
            (title,author)
        ).fetchone()

        if exists:
            continue

        conn.execute("""
        INSERT INTO books(title,author,price,description,image)
        VALUES(?,?,?,?,?)
        """,(

            title,
            author,
            499,
            description[:300],
            image

        ))

        count += 1

    conn.commit()

    conn.close()

    return jsonify({

        "message":"Books Imported Successfully",

        "books_added":count

    })

# ----------------------------
# Run Flask
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)