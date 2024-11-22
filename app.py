from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="coding",  # Your MySQL username
        password="sqldarshu007",  # Your MySQL password
        database="irctc"
    )

# Home route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Implement login logic here
        session['logged_in'] = True  # Set session if login is successful
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('home.html', logged_in=session.get('logged_in'))

@app.route('/start_arrival', methods=['GET', 'POST'])
def start_arrival():
    if request.method == 'POST':
        start_station = request.form['start_station']
        arrival_station = request.form['arrival_station']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT trains.*, 
                   start_station.station_name AS start_station_name, 
                   arrival_station.station_name AS arrival_station_name
            FROM trains 
            JOIN stations AS start_station ON trains.start_station_id = start_station.station_id
            JOIN stations AS arrival_station ON trains.arrival_station_id = arrival_station.station_id
            WHERE start_station.station_name = %s AND arrival_station.station_name = %s
        ''', (start_station, arrival_station))
        trains = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('train_list.html', trains=trains)

    return render_template('start_arrival.html')

# Protected route for booking
# Route to book a ticket by selecting available trains
@app.route('/book_ticket', methods=['GET', 'POST'])
def book_ticket():
    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        date = request.form['date']

        # Query to find available trains based on source and destination
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT trains.*, 
                   start_station.station_name AS start_station_name, 
                   arrival_station.station_name AS arrival_station_name
            FROM trains 
            JOIN stations AS start_station ON trains.start_station_id = start_station.station_id
            JOIN stations AS arrival_station ON trains.arrival_station_id = arrival_station.station_id
            WHERE start_station.station_name = %s AND arrival_station.station_name = %s
        ''', (source, destination))
        
        trains = cursor.fetchall()
        cursor.close()
        conn.close()

        if not trains:
            flash("No trains available for the selected route.", "warning")
            return redirect(url_for('book_ticket'))

        # Render available trains with a book button
        return render_template('bookings.html', trains=trains, source=source, destination=destination, date=date)

    return render_template('book_ticket.html')

# Route to confirm the booking and save the ticket
@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    train_id = request.form['train_id']
    user_id = session.get('user_id', 1)  # Replace with actual user session management
    status = "Confirmed"

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert the booking into the tickets table
        cursor.execute(
            "INSERT INTO tickets (user_id, train_id, status) VALUES (%s, %s, %s)",
            (user_id, train_id, status)
        )
        conn.commit()

        ticket_id = cursor.lastrowid
        flash(f"Your Ticket ID is {ticket_id}", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f"Error during booking: {err}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('home'))  # Redirect to home after successful booking


@app.route('/check_status', methods=['GET', 'POST'])
def check_status():
    if request.method == 'POST':
        ticket_id = request.form['ticket_id']
        print(f"Ticket ID submitted: {ticket_id}")  # Debugging line to check ticket ID submission
        
        # Establish a database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query to get ticket details and station names based on ticket ID
        cursor.execute('''
            SELECT tickets.ticket_id, tickets.status, trains.train_name,
                   start_station.station_name AS start_station_name,
                   arrival_station.station_name AS arrival_station_name
            FROM tickets
            JOIN trains ON tickets.train_id = trains.train_id
            JOIN stations AS start_station ON trains.start_station_id = start_station.station_id
            JOIN stations AS arrival_station ON trains.arrival_station_id = arrival_station.station_id
            WHERE tickets.ticket_id = %s
        ''', (ticket_id,))
        ticket = cursor.fetchone()
        cursor.close()
        conn.close()

        # Debugging to check what ticket data is fetched
        print(f"Fetched ticket data: {ticket}")
        
        # Check if ticket exists and return details
        if ticket:
            return render_template('check_status.html', ticket=ticket)
        else:
            flash("Ticket not found")
            return redirect(url_for('check_status'))

    # If the request method is GET or there is no matching ticket, just render the page
    return render_template('check_status.html')


@app.route('/cancel_ticket', methods=['GET', 'POST'])
def cancel_ticket():
    if request.method == 'POST':
        ticket_id = request.form['ticket_id']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch ticket details before canceling to ensure it exists
        cursor.execute('''
            SELECT ticket_id, status, train_id FROM tickets WHERE ticket_id = %s
        ''', (ticket_id,))
        ticket = cursor.fetchone()

        if ticket:
            # Get the train details associated with the ticket, including station names
            cursor.execute('''
                SELECT train_name, 
                       start_station.station_name AS start_station_name,
                       arrival_station.station_name AS arrival_station_name
                FROM trains
                JOIN stations AS start_station ON trains.start_station_id = start_station.station_id
                JOIN stations AS arrival_station ON trains.arrival_station_id = arrival_station.station_id
                WHERE trains.train_id = %s
            ''', (ticket['train_id'],))
            train = cursor.fetchone()
            
            if train:
                if 'confirm' in request.form:  # Ensure 'confirm' was triggered
                    # Update ticket status to "Canceled"
                    cursor.execute("UPDATE tickets SET status = %s WHERE ticket_id = %s", ("Canceled", ticket_id))
                    conn.commit()  # Commit the change to the database
                    
                    flash("Ticket canceled successfully.")
                    cursor.close()
                    conn.close()
                    return redirect(url_for('home'))
                
                # Show ticket and train details with a confirmation button
                cursor.close()
                conn.close()
                return render_template('confirm_cancel.html', ticket=ticket, train=train)
            else:
                flash("Train information not found.")
                cursor.close()
                conn.close()
        else:
            flash("Ticket not found.")
            cursor.close()
            conn.close()

        return redirect(url_for('home'))

    return render_template('cancel_ticket.html')


if __name__ == '__main__':
    app.run(debug=True)
