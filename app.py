from flask import Flask, render_template, request, redirect, url_for, session, flash
import qrcode
import os
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database file
DB_FILE = "library.db"

# QR code directory
QR_CODE_OUTPUT_DIR = "qr_codes"
if not os.path.exists(QR_CODE_OUTPUT_DIR):
    os.makedirs(QR_CODE_OUTPUT_DIR)

# Admin credentials
ADMIN_CREDENTIALS = {"anshulsahu1042@gmail.com": "password123"}
logged_in_admin = None


def execute_query(query, params=(), fetch=False):
    """Execute a query on the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        conn.commit()


def generate_qr_code_for_shelf(shelf_id):
    """Generate QR code for a shelf."""
    base_url = "http://192.168.43.51:5000"
    url = f"{base_url}/shelf/{shelf_id}"
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    output_file = os.path.join(QR_CODE_OUTPUT_DIR, f"{shelf_id}_qrcode.png")
    img.save(output_file)
    return output_file


@app.route("/")
def home():
    if "admin_email" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    global logged_in_admin
    email = request.form["email"]
    password = request.form["password"]

    if logged_in_admin:
        flash("Another admin is already logged in.", "danger")
        return redirect(url_for("home"))

    if ADMIN_CREDENTIALS.get(email) == password:
        session["admin_email"] = email
        logged_in_admin = email
        flash("Login successful!", "success")
        return redirect(url_for("dashboard"))
    else:
        flash("Invalid credentials.", "danger")
        return redirect(url_for("home"))


@app.route("/logout")
def logout():
    """Log out the admin and redirect to the login page."""
    global logged_in_admin
    logged_in_admin = None
    session.pop("admin_email", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if "admin_email" not in session:
        return redirect(url_for("home"))
    shelves = execute_query("SELECT * FROM shelves", fetch=True)
    return render_template("dashboard.html", shelves=shelves)


@app.route("/add_edit_shelf", methods=["GET", "POST"])
def add_edit_shelf():
    if "admin_email" not in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        shelf_id = request.form["shelf_id"]
        rack_id = request.form["rack_id"]
        book_name = request.form["book_name"]
        author = request.form["author"]
        quantity = int(request.form["quantity"])

        # Ensure the shelf exists
        execute_query("INSERT OR IGNORE INTO shelves (shelf_id) VALUES (?)", (shelf_id,))

        # Get shelf ID for rack
        shelf_db_id = execute_query("SELECT id FROM shelves WHERE shelf_id = ?", (shelf_id,), fetch=True)[0][0]

        # Ensure the rack exists
        execute_query(
            "INSERT OR IGNORE INTO racks (rack_id, shelf_id) VALUES (?, ?)", (rack_id, shelf_db_id)
        )

        # Get rack ID for book
        rack_db_id = execute_query("SELECT id FROM racks WHERE rack_id = ?", (rack_id,), fetch=True)[0][0]

        # Insert or update book
        existing_books = execute_query(
            "SELECT id, quantity FROM books WHERE name = ? AND rack_id = ?", (book_name, rack_db_id), fetch=True
        )
        if existing_books:
            book_id, current_quantity = existing_books[0]
            new_quantity = current_quantity + quantity
            execute_query("UPDATE books SET quantity = ? WHERE id = ?", (new_quantity, book_id))
        else:
            execute_query(
                "INSERT INTO books (name, author, quantity, rack_id) VALUES (?, ?, ?, ?)",
                (book_name, author, quantity, rack_db_id),
            )

        generate_qr_code_for_shelf(shelf_id)
        flash(f"Shelf {shelf_id} updated successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_edit_shelf.html")


@app.route("/shelf/<shelf_id>")
def shelf_details(shelf_id):
    racks = execute_query(
        "SELECT racks.rack_id, books.name, books.author, books.quantity FROM racks "
        "JOIN books ON racks.id = books.rack_id "
        "WHERE racks.shelf_id = (SELECT id FROM shelves WHERE shelf_id = ?)",
        (shelf_id,),
        fetch=True,
    )
    return render_template("shelf_details.html", shelf_id=shelf_id, racks=racks)


@app.route("/borrowed_books")
def borrowed_books():
    borrowed_books = execute_query(
        "SELECT books.name, borrow_logs.student_name, borrow_logs.due_date "
        "FROM borrow_logs "
        "JOIN books ON borrow_logs.book_id = books.id",
        fetch=True,
    )
    return render_template("borrowed_books.html", borrowed_books=borrowed_books)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

