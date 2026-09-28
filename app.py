import os
import sqlite3
import urllib.parse
from functools import wraps

import psycopg2
from psycopg2.extras import RealDictCursor

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify
)

app = Flask(__name__)

# Use environment variable for secret in production
app.secret_key = os.environ.get(
    'SECRET_KEY',
    'mauli_travel_secret_key_buldana'
)

# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DATABASE_URL = os.environ.get('DATABASE_URL')

# Local development:
# If DATABASE_URL is not available, SQLite will be used.
DATA_DIR = os.path.join(app.root_path, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, 'mauli_travel.db')


def get_db_connection():
    """
    Use PostgreSQL on Render.
    Use SQLite locally when DATABASE_URL is not available.
    """

    if DATABASE_URL:
        # Some hosting providers may provide postgres://
        # psycopg2 expects postgresql://
        database_url = DATABASE_URL

        if database_url.startswith('postgres://'):
            database_url = database_url.replace(
                'postgres://',
                'postgresql://',
                1
            )

        conn = psycopg2.connect(database_url)
        conn.cursor_factory = RealDictCursor
        return conn

    # Local SQLite connection
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def is_postgres():
    return bool(DATABASE_URL)


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = get_db_connection()
    cursor = conn.cursor()

    if is_postgres():

        # PostgreSQL tables

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tours (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                route TEXT NOT NULL,
                details TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    else:

        # SQLite tables for local development

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


# =========================================================
# SQL HELPER
# =========================================================

def execute_query(conn, query, params=()):
    """
    PostgreSQL uses %s placeholders.
    SQLite uses ? placeholders.
    """

    if is_postgres():
        query = query.replace('?', '%s')

    return conn.execute(query, params)


# =========================================================
# ADMIN AUTH DECORATOR
# =========================================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not session.get('admin_logged_in'):
            flash('Please log in first.', 'danger')
            return redirect(url_for('admin_login'))

        return f(*args, **kwargs)

    return decorated_function


# =========================================================
# PUBLIC ROUTES
# =========================================================

@app.route('/')
def index():

    conn = get_db_connection()

    tours = execute_query(
        conn,
        'SELECT * FROM tours ORDER BY date ASC'
    ).fetchall()

    conn.close()

    return render_template(
        'index.html',
        tours=tours
    )


@app.route('/availability')
def availability():

    return render_template('availability.html')


# =========================================================
# CALENDAR API
# =========================================================

@app.route('/api/calendar-events')
def api_calendar_events():

    conn = get_db_connection()

    accepted_rows = execute_query(
        conn,
        "SELECT travel_date FROM bookings WHERE status = 'accepted'"
    ).fetchall()

    conn.close()

    accepted_dates = [
        row['travel_date']
        for row in accepted_rows
    ]

    return jsonify({
        "accepted_dates": accepted_dates
    })


# =========================================================
# BOOKING
# =========================================================

@app.route('/book', methods=['POST'])
def book():

    name = request.form.get('name', '').strip()
    whatsapp = request.form.get('whatsapp', '').strip()
    pickup = request.form.get('pickup', '').strip()
    destination = request.form.get('destination', '').strip()
    travel_date = request.form.get('travel_date', '').strip()
    travel_time = request.form.get('travel_time', '').strip()

    if not all([
        name,
        whatsapp,
        pickup,
        destination,
        travel_date,
        travel_time
    ]):

        flash(
            'Please fill out all required fields.',
            'warning'
        )

        return redirect(url_for('availability'))

    conn = get_db_connection()

    # Check whether date is already accepted/booked
    existing = execute_query(
        conn,
        """
        SELECT id
        FROM bookings
        WHERE travel_date = ?
        AND status = 'accepted'
        """,
        (travel_date,)
    ).fetchone()

    if existing:

        conn.close()

        flash(
            'This date is already booked. Please select another available date.',
            'danger'
        )

        return redirect(url_for('availability'))

    # Insert booking
    if is_postgres():

        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO bookings
            (
                name,
                whatsapp,
                pickup,
                destination,
                travel_date,
                travel_time,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
            RETURNING id
            ''',
            (
                name,
                whatsapp,
                pickup,
                destination,
                travel_date,
                travel_time
            )
        )

        booking_id = cursor.fetchone()['id']

    else:

        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO bookings
            (
                name,
                whatsapp,
                pickup,
                destination,
                travel_date,
                travel_time,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
            ''',
            (
                name,
                whatsapp,
                pickup,
                destination,
                travel_date,
                travel_time
            )
        )

        booking_id = cursor.lastrowid

    conn.commit()
    conn.close()

    # WhatsApp message
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
        f"Please confirm my booking.\n"
        f"Thank you."
    )

    encoded_msg = urllib.parse.quote(msg)

    whatsapp_url = (
        f"https://wa.me/917020138677"
        f"?text={encoded_msg}"
    )

    return redirect(
        url_for(
            'availability',
            success=1,
            name=name,
            date=travel_date,
            time=travel_time,
            wa_url=whatsapp_url
        )
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'admin123':

            session['admin_logged_in'] = True

            flash(
                'Logged in successfully.',
                'success'
            )

            return redirect(
                url_for('admin_dashboard')
            )

        else:

            flash(
                'Invalid admin credentials.',
                'danger'
            )

    return render_template(
        'admin_login.html'
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route('/admin/logout')
def admin_logout():

    session.pop(
        'admin_logged_in',
        None
    )

    flash(
        'Logged out successfully.',
        'info'
    )

    return redirect(
        url_for('admin_login')
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():

    conn = get_db_connection()

    bookings = execute_query(
        conn,
        'SELECT * FROM bookings ORDER BY id DESC'
    ).fetchall()

    tours = execute_query(
        conn,
        'SELECT * FROM tours ORDER BY date ASC'
    ).fetchall()

    conn.close()

    return render_template(
        'admin.html',
        bookings=bookings,
        tours=tours
    )


# =========================================================
# ACCEPT / REJECT BOOKING
# =========================================================

@app.route('/admin/booking/<int:booking_id>/<action>')
@login_required
def update_booking_status(
    booking_id,
    action
):

    if action not in [
        'accept',
        'reject'
    ]:

        flash(
            'Invalid action.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )

    status = (
        'accepted'
        if action == 'accept'
        else 'rejected'
    )

    conn = get_db_connection()

    # Check booking date before accepting
    if status == 'accepted':

        booking = execute_query(
            conn,
            '''
            SELECT travel_date
            FROM bookings
            WHERE id = ?
            ''',
            (booking_id,)
        ).fetchone()

        if booking:

            t_date = booking['travel_date']

            conflict = execute_query(
                conn,
                '''
                SELECT id
                FROM bookings
                WHERE travel_date = ?
                AND status = 'accepted'
                AND id != ?
                ''',
                (
                    t_date,
                    booking_id
                )
            ).fetchone()

            if conflict:

                flash(
                    f'Cannot accept! Date {t_date} '
                    f'is already assigned to another '
                    f'accepted booking.',
                    'danger'
                )

                conn.close()

                return redirect(
                    url_for('admin_dashboard')
                )

    execute_query(
        conn,
        '''
        UPDATE bookings
        SET status = ?
        WHERE id = ?
        ''',
        (
            status,
            booking_id
        )
    )

    conn.commit()
    conn.close()

    flash(
        f'Booking #{booking_id} marked as {status}.',
        'success'
    )

    return redirect(
        url_for('admin_dashboard')
    )


# =========================================================
# ADD UPCOMING TOUR
# =========================================================

@app.route('/admin/tour/add', methods=['POST'])
@login_required
def add_tour():

    title = request.form.get('title')
    date = request.form.get('date')
    route = request.form.get('route')
    details = request.form.get('details')

    if title and date and route and details:

        conn = get_db_connection()

        execute_query(
            conn,
            '''
            INSERT INTO tours
            (
                title,
                date,
                route,
                details
            )
            VALUES (?, ?, ?, ?)
            ''',
            (
                title,
                date,
                route,
                details
            )
        )

        conn.commit()
        conn.close()

        flash(
            'Upcoming tour published successfully.',
            'success'
        )

    else:

        flash(
            'Please fill in all tour details.',
            'warning'
        )

    return redirect(
        url_for('admin_dashboard')
    )


# =========================================================
# DELETE UPCOMING TOUR
# =========================================================

@app.route(
    '/admin/tour/delete/<int:tour_id>',
    methods=['POST']
)
@login_required
def delete_tour(tour_id):

    conn = get_db_connection()

    execute_query(
        conn,
        'DELETE FROM tours WHERE id = ?',
        (tour_id,)
    )

    conn.commit()
    conn.close()

    flash(
        'Tour deleted successfully.',
        'info'
    )

    return redirect(
        url_for('admin_dashboard')
    )


# =========================================================
# RUN APP
# =========================================================

if __name__ == '__main__':

    app.run(
        debug=True
    )