from flask import render_template, request, redirect, url_for, session
from backend import app, get_db_connection

@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE U_id = %s AND Password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            session['user_id'] = user['U_id']
            return redirect(url_for('user_dashboard'))
        else:
            return "Invalid username or password"
    return render_template('login.html')

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('user_dashboard.html')

@app.route('/search_trains', methods=['POST'])
def search_trains():
    start = request.form['start']
    end = request.form['end']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM consist_of 
        JOIN train ON consist_of.Train_id = train.Train_id
        WHERE Start = %s AND End = %s
    """, (start, end))
    trains = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('train_availability.html', trains=trains)

@app.route('/book/<int:train_id>', methods=['GET', 'POST'])
def book(train_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Assuming you have a form to handle the booking
        # You can implement the booking logic here.
        # For example:
        passenger_name = request.form['passenger_name']
        # Add booking to the database (you need to implement this logic).
        return redirect(url_for('user_dashboard'))

    return render_template('booking.html', train_id=train_id)

@app.route('/check_status', methods=['GET', 'POST'])
def check_status():
    if request.method == 'POST':
        booking_id = request.form['booking_id']
        # Fetch the booking status from the database (implement this).
        # For example:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bookings WHERE booking_id = %s", (booking_id,))
        booking_info = cursor.fetchone()
        cursor.close()
        conn.close()
        return render_template('check_status.html', booking_info=booking_info)

    return render_template('check_status.html')

@app.route('/train_details', methods=['POST'])
def train_details():
    train_id = request.form['train_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM train WHERE Train_id = %s", (train_id,))
    train = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('train_details.html', train=train)

@app.route('/station_details', methods=['POST'])
def station_details():
    station = request.form['station']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM station 
        JOIN route ON station.Station_id = route.Station_id
        WHERE Station_name = %s
    """, (station,))
    station_info = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('station_details.html', station_info=station_info)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))
