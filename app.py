import os
import sqlite3
import urllib.parse
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = Flask(__name__)
app.secret_key = 'mauli_travel_secret_key_buldana'

# Ensure data directory exists
DATA_DIR = os.path.join(app.root_path, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'mauli_travel.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            whatsapp TEXT NOT NULL,
            pickup TEXT NOT NULL,
            destination TEXT NOT NULL,
            travel_date TEXT NOT NULL,
            travel_time TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Tours table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            route TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Admin Auth Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in first.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Public Routes
@app.route('/')
def index():
    conn = get_db_connection()
    tours = conn.execute('SELECT * FROM tours ORDER BY date ASC').fetchall()
    conn.close()
    return render_template('index.html', tours=tours)

@app.route('/availability')
def availability():
    return render_template('availability.html')

@app.route('/api/calendar-events')
def api_calendar_events():
    conn = get_db_connection()
    accepted_rows = conn.execute("SELECT travel_date FROM bookings WHERE status = 'accepted'").fetchall()
    conn.close()
    accepted_dates = [row['travel_date'] for row in accepted_rows]
    return jsonify({"accepted_dates": accepted_dates})

@app.route('/book', methods=['POST'])
def book():
    name = request.form.get('name', '').strip()
    whatsapp = request.form.get('whatsapp', '').strip()
    pickup = request.form.get('pickup', '').strip()
    destination = request.form.get('destination', '').strip()
    travel_date = request.form.get('travel_date', '').strip()
    travel_time = request.form.get('travel_time', '').strip()

    if not all([name, whatsapp, pickup, destination, travel_date, travel_time]):
        flash('Please fill out all required fields.', 'warning')
        return redirect(url_for('availability'))

    conn = get_db_connection()
    existing = conn.execute(
        "SELECT id FROM bookings WHERE travel_date = ? AND status = 'accepted'",
        (travel_date,)
    ).fetchone()

    if existing:
        conn.close()
        flash('This date is already booked. Please select another available date.', 'danger')
        return redirect(url_for('availability'))

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bookings (name, whatsapp, pickup, destination, travel_date, travel_time, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    ''', (name, whatsapp, pickup, destination, travel_date, travel_time))
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()

    msg = (
        f"Hello Mauli Travel,\n\n"
        f"I would like to book a ride.\n\n"
        f"Booking ID: #{booking_id}\n"
        f"Name: {name}\n"
        f"WhatsApp: {whatsapp}\n"
        f"From: {pickup}\n"
        f"To: {destination}\n"
        f"Date: {travel_date}\n"
        f"Time: {travel_time}\n\n"
        f"Please confirm my booking.\nThank you."
    )
    
    encoded_msg = urllib.parse.quote(msg)
    whatsapp_url = f"https://wa.me/917020138677?text={encoded_msg}"

    # Redirect with success modal parameters
    return redirect(url_for('availability', 
                            success=1, 
                            name=name, 
                            date=travel_date, 
                            time=travel_time, 
                            wa_url=whatsapp_url))

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    conn = get_db_connection()
    bookings = conn.execute('SELECT * FROM bookings ORDER BY id DESC').fetchall()
    tours = conn.execute('SELECT * FROM tours ORDER BY date ASC').fetchall()
    conn.close()
    return render_template('admin.html', bookings=bookings, tours=tours)

@app.route('/admin/booking/<int:booking_id>/<action>')
@login_required
def update_booking_status(booking_id, action):
    if action not in ['accept', 'reject']:
        flash('Invalid action.', 'danger')
        return redirect(url_for('admin_dashboard'))

    status = 'accepted' if action == 'accept' else 'rejected'

    conn = get_db_connection()
    if status == 'accepted':
        booking = conn.execute('SELECT travel_date FROM bookings WHERE id = ?', (booking_id,)).fetchone()
        if booking:
            t_date = booking['travel_date']
            conflict = conn.execute(
                "SELECT id FROM bookings WHERE travel_date = ? AND status = 'accepted' AND id != ?",
                (t_date, booking_id)
            ).fetchone()
            if conflict:
                flash(f'Cannot accept! Date {t_date} is already assigned to another accepted booking.', 'danger')
                conn.close()
                return redirect(url_for('admin_dashboard'))

    conn.execute('UPDATE bookings SET status = ? WHERE id = ?', (status, booking_id))
    conn.commit()
    conn.close()
    flash(f'Booking #{booking_id} marked as {status}.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/tour/add', methods=['POST'])
@login_required
def add_tour():
    title = request.form.get('title')
    date = request.form.get('date')
    route = request.form.get('route')
    details = request.form.get('details')

    if title and date and route and details:
        conn = get_db_connection()
        conn.execute('INSERT INTO tours (title, date, route, details) VALUES (?, ?, ?, ?)',
                     (title, date, route, details))
        conn.commit()
        conn.close()
        flash('Upcoming tour published successfully.', 'success')
    else:
        flash('Please fill in all tour details.', 'warning')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/tour/delete/<int:tour_id>', methods=['POST'])
@login_required
def delete_tour(tour_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tours WHERE id = ?', (tour_id,))
    conn.commit()
    conn.close()
    flash('Tour deleted successfully.', 'info')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)