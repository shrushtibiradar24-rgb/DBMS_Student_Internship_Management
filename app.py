from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import date

app = Flask(__name__)
app.secret_key = "internship_secret_key"

# -------------------------
# DATABASE CONNECTION
# -------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="internship_management"
    )

# -------------------------
# LOGIN
# -------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM user WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session['user_id'] = user['user_id']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid Credentials!", "danger")

    return render_template("login.html")

# -------------------------
# REGISTER (Viewer only)
# -------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO user (name, email, password, role)
            VALUES (%s, %s, %s, %s)
        """, (name, email, password, "viewer"))

        db.commit()
        cursor.close()
        db.close()

        flash("Account created successfully!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# -------------------------
# ADMIN DASHBOARD
# -------------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch Students
    cursor.execute("SELECT * FROM student")
    students = cursor.fetchall()

    # Fetch Internships
    cursor.execute("SELECT * FROM internship")
    internships = cursor.fetchall()

    # Fetch Departments
    cursor.execute("SELECT * FROM department")
    departments = cursor.fetchall()

    # Fetch Combined Data
    cursor.execute("""
        SELECT 
            a.application_id,
            i.title AS internship_title,
            i.company_name,
            i.duration,
            i.stipend,
            s.name AS student_name,
            s.email AS student_email,
            s.phone AS student_phone,
            a.status AS application_status,
            a.apply_date
        FROM application a
        JOIN student s ON a.student_id = s.student_id
        JOIN internship i ON a.internship_id = i.internship_id
        ORDER BY a.application_id DESC
    """)
    data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        'admin_dashboard.html',
        students=students,
        internships=internships,
        departments=departments,
        data=data
    )

# -------------------------
# ADD STUDENT
# -------------------------
@app.route('/add_student', methods=['POST'])
def add_student():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO student (name, email, phone, dept_id)
        VALUES (%s, %s, %s, %s)
    """, (
        request.form['name'],
        request.form['email'],
        request.form['phone'],
        request.form['dept_id']
    ))

    db.commit()
    cursor.close()
    db.close()

    flash("Student added successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# ADD INTERNSHIP
# -------------------------
@app.route('/add_internship', methods=['POST'])
def add_internship():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO internship (title, company_name, duration, stipend, dept_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        request.form['title'],
        request.form['company_name'],
        request.form['duration'],
        request.form['stipend'],
        request.form['dept_id']
    ))

    db.commit()
    cursor.close()
    db.close()

    flash("Internship added successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# ADD APPLICATION (COMBINED)
# -------------------------
@app.route('/add_application', methods=['POST'])
def add_application():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor()

    try:
        # Insert Student
        cursor.execute("""
            INSERT INTO student (name, email, phone, dept_id)
            VALUES (%s, %s, %s, %s)
        """, (
            request.form['student_name'],
            request.form['student_email'],
            request.form['student_phone'],
            request.form['student_dept_id']
        ))
        student_id = cursor.lastrowid

        # Insert Internship
        cursor.execute("""
            INSERT INTO internship (title, company_name, duration, stipend, dept_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            request.form['title'],
            request.form['company_name'],
            request.form['duration'],
            request.form['stipend'],
            request.form['internship_dept_id']
        ))
        internship_id = cursor.lastrowid

        # Insert Application
        cursor.execute("""
            INSERT INTO application (student_id, internship_id, status, apply_date)
            VALUES (%s, %s, %s, %s)
        """, (
            student_id,
            internship_id,
            request.form['status'],
            request.form['apply_date'] or str(date.today())
        ))

        db.commit()

    except Exception as e:
        db.rollback()
        print("Error:", e)

    cursor.close()
    db.close()

    flash("Internship assigned successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# DELETE APPLICATION
# -------------------------
@app.route('/delete_application/<int:id>')
def delete_application(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM application WHERE application_id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()

    flash("Application deleted!", "success")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# USER DASHBOARD
# -------------------------
@app.route('/user_dashboard')
def user_dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            i.title AS internship_title,
            i.company_name,
            i.duration,
            i.stipend,
            s.name AS student_name,
            a.status,
            a.apply_date
        FROM application a
        JOIN student s ON a.student_id = s.student_id
        JOIN internship i ON a.internship_id = i.internship_id
    """)

    data = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("user_dashboard.html", data=data)

# -------------------------
# LOGOUT
# -------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -------------------------
# RUN APP
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)