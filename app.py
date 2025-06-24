from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use a secure secret key in production

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'faculty_leave_db'

mysql = MySQL(app)

# Home Redirect
@app.route('/')
def home():
    return redirect('/login')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM faculty WHERE email = %s", (email,))
        account = cur.fetchone()

        if account:
            msg = 'Email already registered!'
        else:
            cur.execute("INSERT INTO faculty (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
            mysql.connection.commit()
            msg = 'Registered successfully!'
        cur.close()

    return render_template('register.html', msg=msg)

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        email_or_username = request.form['email']
        password = request.form['password']
        role = request.form['role']

        cur = mysql.connection.cursor()

        if role == 'faculty':
            cur.execute("SELECT * FROM faculty WHERE email = %s AND password = %s", (email_or_username, password))
            user = cur.fetchone()
            if user:
                session['loggedin'] = True
                session['id'] = user[0]
                session['name'] = user[1]
                session['role'] = 'faculty'
                return redirect('/apply_leave')
            else:
                msg = 'Invalid faculty credentials.'

        elif role == 'admin':
            cur.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (email_or_username, password))
            admin = cur.fetchone()
            if admin:
                session['admin'] = True
                session['name'] = admin[1]
                session['role'] = 'admin'
                return redirect('/admin_dashboard')
            else:
                msg = 'Invalid admin credentials.'

        cur.close()
    return render_template('login.html', msg=msg)

# Apply Leave (Faculty)
@app.route('/apply_leave', methods=['GET', 'POST'])
def apply_leave():
    if 'loggedin' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            leave_type = request.form['leave_type']
            from_date = request.form['from_date']
            to_date = request.form['to_date']
            reason = request.form['reason']
            faculty_id = session['id']

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO leave_requests (faculty_id, leave_type, from_date, to_date, reason, status) VALUES (%s, %s, %s, %s, %s, 'Pending')",
                        (faculty_id, leave_type, from_date, to_date, reason))
            mysql.connection.commit()
            cur.close()
            return redirect('/view_status')

        return render_template('apply_leave.html')
    return redirect('/login')

# View Leave Status (Faculty)
@app.route('/view_status')
def view_status():
    if 'loggedin' in session and session['role'] == 'faculty':
        faculty_id = session['id']
        cur = mysql.connection.cursor()
        cur.execute("SELECT leave_type, from_date, to_date, reason, status FROM leave_requests WHERE faculty_id = %s", (faculty_id,))
        leaves = cur.fetchall()
        cur.close()
        return render_template('view_status.html', leaves=leaves)
    return redirect('/login')

# Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' in session:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT leave_requests.id, faculty.name, leave_requests.leave_type,
                   leave_requests.from_date, leave_requests.to_date,
                   leave_requests.reason, leave_requests.status
            FROM leave_requests
            JOIN faculty ON leave_requests.faculty_id = faculty.id
        """)
        requests = cur.fetchall()
        cur.close()
        return render_template('admin_dashboard.html', requests=requests)
    return redirect('/login')

# Approve Leave
@app.route('/approve/<int:id>')
def approve(id):
    if 'admin' in session:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE leave_requests SET status = 'Approved' WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect('/admin_dashboard')
    return redirect('/login')

# Reject Leave
@app.route('/reject/<int:id>')
def reject(id):
    if 'admin' in session:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE leave_requests SET status = 'Rejected' WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect('/admin_dashboard')
    return redirect('/login')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# Run Server
if __name__ == '__main__':
    app.run(debug=True)
