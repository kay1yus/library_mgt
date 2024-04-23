# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Function to connect to SQLite database
def connect_db():
    return sqlite3.connect('library.db')

# User login required decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin login required decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('You need admin privileges to access this page', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Index route
@app.route('/')
def index():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = connect_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[3]
            flash('You have been logged in successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        conn = connect_db()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, hashed_password, 0))
        conn.commit()
        conn.close()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

# Books route
@app.route('/books')
def books():
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return render_template('books.html', books=books)

# Borrow route
@app.route('/borrow', methods=['GET', 'POST'])
@login_required
def borrow():
    if request.method == 'POST':
        book_id = request.form['book_id']
        conn = connect_db()
        c = conn.cursor()
        c.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        book = c.fetchone()
        if book and book[4] > 0:
            user_id = session['user_id']
            borrow_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            due_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
            c.execute("INSERT INTO borrowed_books (user_id, book_id, borrow_date, due_date, returned) VALUES (?, ?, ?, ?, 0)", (user_id, book_id, borrow_date, due_date))
            c.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = ?", (book_id,))
            conn.commit()
            conn.close()
            flash('Book borrowed successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Book is not available for borrowing', 'error')
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return render_template('borrow.html', books=books)

# Return route
@app.route('/return', methods=['GET', 'POST'])
@login_required
def return_book():
    if request.method == 'POST':
        borrowed_book_id = request.form['borrowed_book_id']
        conn = connect_db()
        c = conn.cursor()
        c.execute("SELECT * FROM borrowed_books WHERE id = ? AND user_id = ?", (borrowed_book_id, session['user_id']))
        borrowed_book = c.fetchone()
        if borrowed_book:
            due_date = datetime.datetime.strptime(borrowed_book[4], '%Y-%m-%d %H:%M:%S')
            current_date = datetime.datetime.now()
            fine = 0
            if current_date > due_date:
                days_overdue = (current_date - due_date).days
                fine = days_overdue * 5  # Assuming a fine of £5 per day
            book_id = borrowed_book[2]
            c.execute("UPDATE borrowed_books SET returned = 1, fine = ? WHERE id = ?", (fine, borrowed_book_id,))
            c.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id = ?", (book_id,))
            conn.commit()
            conn.close()
            flash(f'Book returned successfully. Fine: £{fine}', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid borrowed book ID', 'error')
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT b.id, b.title, u.username, bb.borrow_date, bb.due_date FROM borrowed_books bb JOIN books b ON bb.book_id = b.id JOIN users u ON bb.user_id = u.id WHERE bb.user_id = ? AND bb.returned = 0", (session['user_id'],))
    borrowed_books = c.fetchall()
    conn.close()
    return render_template('return.html', borrowed_books=borrowed_books)

# Admin books route
@app.route('/admin/books')
@admin_required
def admin_books():
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return render_template('admin_books.html', books=books)

# Admin users route
@app.route('/admin/users')
@admin_required
def admin_users():
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE is_admin = 0")
    users = c.fetchall()
    conn.close()
    return render_template('admin_users.html', users=users)

# Admin add book route
@app.route('/admin/add_book', methods=['GET', 'POST'])
@admin_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        total_copies = request.form['total_copies']
        conn = connect_db()
        c = conn.cursor()
        c.execute("INSERT INTO books (title, author, total_copies, available_copies) VALUES (?, ?, ?, ?)", (title, author, total_copies, total_copies))
        conn.commit()
        conn.close()
        flash('Book added successfully', 'success')
        return redirect(url_for('admin_books'))
    return render_template('add_book.html')

# Admin edit book route
@app.route('/admin/edit_book/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    conn = connect_db()
    c = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        total_copies = request.form['total_copies']
        c.execute("UPDATE books SET title = ?, author = ?, total_copies = ?, available_copies = ? WHERE id = ?", (title, author, total_copies, total_copies, book_id))
        conn.commit()
        conn.close()
        flash('Book updated successfully', 'success')
        return redirect(url_for('admin_books'))
    c.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = c.fetchone()
    conn.close()
    return render_template('edit_book.html', book=book)

# Admin delete book route
@app.route('/admin/delete_book/<int:book_id>')
@admin_required
def delete_book(book_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    flash('Book deleted successfully', 'success')
    return redirect(url_for('admin_books'))

if __name__ == '__main__':
    app.run(debug=True)
