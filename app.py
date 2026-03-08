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
# REGISTER
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
        INSERT INTO user (name,email,password,role)
        VALUES (%s,%s,%s,%s)
        """,(name,email,password,"viewer"))

        db.commit()

        cursor.close()
        db.close()

        flash("Account created successfully!")
        return redirect(url_for('login'))

    return render_template("register.html")

# -------------------------
# ADMIN DASHBOARD
# -------------------------
@app.route('/admin_dashboard')
def admin_dashboard():

    if 'role' not in session or session['role']!='admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM internship")
    internships = cursor.fetchall()

    cursor.execute("SELECT * FROM department")
    departments = cursor.fetchall()

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
    JOIN student s ON a.student_id=s.student_id
    JOIN internship i ON a.internship_id=i.internship_id
    ORDER BY a.application_id DESC
    """)

    data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "admin_dashboard.html",
        students=students,
        internships=internships,
        departments=departments,
        data=data,
        total_students=len(students),
        total_internships=len(internships),
        total_departments=len(departments),
        total_applications=len(data)
    )

# -------------------------
# OPEN ADD STUDENT PAGE
# -------------------------
@app.route('/add_student_page')
def add_student_page():

    if session.get('role')!='admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM department")
    departments = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("add_student.html", departments=departments)

# -------------------------
# ADD STUDENT TO DATABASE
# -------------------------
@app.route('/add_student', methods=['POST'])
def add_student():

    if session.get('role') != 'admin':
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

    return redirect(url_for('admin_dashboard'))

# -------------------------
# ADD INTERNSHIP
# -------------------------
@app.route('/add_internship', methods=['POST'])
def add_internship():

    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    title = request.form['title']
    company_name = request.form['company_name']
    duration = request.form['duration']
    stipend = request.form['stipend']
    dept_id = request.form['dept_id']

    user_id = session['user_id']   # logged-in admin

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO internship
        (title, company_name, duration, stipend, dept_id, user_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """,(title, company_name, duration, stipend, dept_id, user_id))

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for('admin_dashboard'))


# -------------------------
# OPEN ASSIGN INTERNSHIP PAGE
# -------------------------
@app.route('/assign_internship_page')
def assign_internship_page():

    if session.get('role')!='admin':
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM internship")
    internships = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "assign_internship.html",
        students=students,
        internships=internships
    )

# -------------------------
# ADD APPLICATION
# -------------------------
@app.route('/add_application',methods=['POST'])
def add_application():

    if session.get('role')!='admin':
        return redirect(url_for('login'))

    db=get_db_connection()
    cursor=db.cursor()

    cursor.execute("""
    INSERT INTO application(student_id,internship_id,status,apply_date)
    VALUES(%s,%s,%s,%s)
    """,(
        request.form['student_id'],
        request.form['internship_id'],
        request.form['status'],
        request.form['apply_date'] or str(date.today())
    ))

    db.commit()

    cursor.close()
    db.close()

    flash("Application added successfully")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# EDIT APPLICATION
# -------------------------
@app.route('/edit_application/<int:id>')
def edit_application(id):

    if session.get('role')!='admin':
        return redirect(url_for('login'))

    db=get_db_connection()
    cursor=db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM application WHERE application_id=%s",(id,))
    application=cursor.fetchone()

    cursor.close()
    db.close()

    return render_template("edit_application.html",application=application)

# -------------------------
# UPDATE APPLICATION
# -------------------------
@app.route('/update_application/<int:id>',methods=['POST'])
def update_application(id):

    if session.get('role')!='admin':
        return redirect(url_for('login'))

    status=request.form['status']

    db=get_db_connection()
    cursor=db.cursor()

    cursor.execute("""
    UPDATE application
    SET status=%s
    WHERE application_id=%s
    """,(status,id))

    db.commit()

    cursor.close()
    db.close()

    flash("Application updated successfully")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# DELETE APPLICATION
# -------------------------
@app.route('/delete_application/<int:id>')
def delete_application(id):

    if session.get('role')!='admin':
        return redirect(url_for('login'))

    db=get_db_connection()
    cursor=db.cursor()

    cursor.execute("DELETE FROM application WHERE application_id=%s",(id,))
    db.commit()

    cursor.close()
    db.close()

    flash("Application deleted successfully")
    return redirect(url_for('admin_dashboard'))

# -------------------------
# USER DASHBOARD
# -------------------------
@app.route('/user_dashboard')
def user_dashboard():

    if 'role' not in session:
        return redirect(url_for('login'))

    db=get_db_connection()
    cursor=db.cursor(dictionary=True)

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
    JOIN student s ON a.student_id=s.student_id
    JOIN internship i ON a.internship_id=i.internship_id
    """)

    data=cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("user_dashboard.html",data=data)

# -------------------------
# LOGOUT
# -------------------------
@app.route('/logout')
def logout():

    session.clear()
    return redirect(url_for('login'))

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)