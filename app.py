from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import date

app = Flask(__name__)
app.secret_key = "internship_secret_key"

# -------------------------
# DATABASE CONNECTION FUNCTION
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
# USER DASHBOARD (VIEW ONLY)
# -------------------------
@app.route('/user_dashboard')
def user_dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch only data related to student applications
    cursor.execute("""
        SELECT 
            i.title AS internship_title,
            i.company_name,
            i.duration,
            i.stipend,
            d1.dept_name AS internship_dept,
            s.name AS student_name,
            s.email AS student_email,
            s.phone AS student_phone,
            d2.dept_name AS student_dept,
            a.status AS application_status,
            a.apply_date
        FROM internship i
        JOIN department d1 ON i.dept_id = d1.dept_id
        JOIN application a ON i.internship_id = a.internship_id
        JOIN student s ON a.student_id = s.student_id
        JOIN department d2 ON s.dept_id = d2.dept_id
        ORDER BY i.title;
    """)

    data = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("user_dashboard.html", data=data)

# -------------------------
# ADMIN DASHBOARD
# -------------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch combined application data
    cursor.execute("""
        SELECT 
            a.application_id,
            i.internship_id,
            i.title AS internship_title,
            i.company_name,
            i.duration,
            i.stipend,
            d1.dept_name AS internship_dept,
            s.student_id,
            s.name AS student_name,
            s.email AS student_email,
            s.phone AS student_phone,
            d2.dept_name AS student_dept,
            a.status AS application_status,
            a.apply_date
        FROM internship i
        JOIN department d1 ON i.dept_id = d1.dept_id
        JOIN application a ON i.internship_id = a.internship_id
        JOIN student s ON a.student_id = s.student_id
        JOIN department d2 ON s.dept_id = d2.dept_id
        ORDER BY i.title, s.name;
    """)
    data = cursor.fetchall()

    # Fetch students, internships, departments for dropdowns
    cursor.execute("SELECT * FROM student")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM internship")
    internships = cursor.fetchall()

    cursor.execute("SELECT * FROM department")
    departments = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("admin_dashboard.html", data=data, students=students,
                           internships=internships, departments=departments)

# -------------------------
# ADD STUDENT
# -------------------------
@app.route('/add_student', methods=['POST'])
def add_student():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    dept_id = request.form['dept_id']

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO student (name, email, phone, dept_id)
        VALUES (%s, %s, %s, %s)
    """, (name, email, phone, dept_id))
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
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    title = request.form['title']
    company_name = request.form['company_name']
    duration = request.form['duration']
    stipend = request.form['stipend']
    dept_id = request.form['dept_id']

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO internship (title, company_name, duration, stipend, dept_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (title, company_name, duration, stipend, dept_id))
    db.commit()
    cursor.close()
    db.close()

    flash("Internship added successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# ADD APPLICATION (Assign student to internship)
# -------------------------
@app.route('/add_application', methods=['POST'])
def add_application():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    student_id = request.form['student_id']
    internship_id = request.form['internship_id']
    status = request.form['status']
    apply_date = request.form['apply_date'] or str(date.today())

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO application (student_id, internship_id, status, apply_date)
        VALUES (%s, %s, %s, %s)
    """, (student_id, internship_id, status, apply_date))
    db.commit()
    cursor.close()
    db.close()

    flash("Application added successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# EDIT STUDENT
# -------------------------
@app.route('/edit_student/<int:id>', methods=['POST'])
def edit_student(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    dept_id = request.form['dept_id']

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE student 
        SET name=%s, email=%s, phone=%s, dept_id=%s
        WHERE student_id=%s
    """, (name, email, phone, dept_id, id))
    db.commit()
    cursor.close()
    db.close()

    flash("Student updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# EDIT INTERNSHIP
# -------------------------
@app.route('/edit_internship/<int:id>', methods=['POST'])
def edit_internship(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    title = request.form['title']
    company_name = request.form['company_name']
    duration = request.form['duration']
    stipend = request.form['stipend']
    dept_id = request.form['dept_id']

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE internship 
        SET title=%s, company_name=%s, duration=%s, stipend=%s, dept_id=%s
        WHERE internship_id=%s
    """, (title, company_name, duration, stipend, dept_id, id))
    db.commit()
    cursor.close()
    db.close()

    flash("Internship updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# DELETE STUDENT
# -------------------------
@app.route('/delete_student/<int:id>')
def delete_student(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM student WHERE student_id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()

    flash("Student deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# DELETE INTERNSHIP
# -------------------------
@app.route('/delete_internship/<int:id>')
def delete_internship(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM internship WHERE internship_id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()

    flash("Internship deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# DELETE APPLICATION
# -------------------------
@app.route('/delete_application/<int:id>')
def delete_application(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM application WHERE application_id=%s", (id,))
    db.commit()
    cursor.close()
    db.close()

    flash("Application deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

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