from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'

# Database path
DATABASE = 'database/hospital.db'

# Initialize database
def init_db():
    # Create database directory if it doesn't exist
    os.makedirs('database', exist_ok=True)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'doctor', 'patient')),
            full_name TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            specialization TEXT,
            qualification TEXT,
            experience INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            age INTEGER,
            gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
            blood_group TEXT,
            address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Appointments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            appointment_date DATE,
            appointment_time TIME,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'confirmed', 'completed', 'cancelled')),
            symptoms TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# Database helper function
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    return render_template('base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            flash('Login successful!', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        full_name = request.form['full_name']
        phone = request.form['phone']
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password, role, full_name, phone) VALUES (?, ?, ?, ?, ?, ?)",
                (username, email, password, role, full_name, phone)
            )
            user_id = cursor.lastrowid
            
            # Create role-specific entry
            if role == 'doctor':
                specialization = request.form.get('specialization', '')
                qualification = request.form.get('qualification', '')
                experience = request.form.get('experience', 0)
                cursor.execute(
                    "INSERT INTO doctors (user_id, specialization, qualification, experience) VALUES (?, ?, ?, ?)",
                    (user_id, specialization, qualification, experience)
                )
            elif role == 'patient':
                age = request.form.get('age', 0)
                gender = request.form.get('gender', 'Other')
                blood_group = request.form.get('blood_group', '')
                address = request.form.get('address', '')
                cursor.execute(
                    "INSERT INTO patients (user_id, age, gender, blood_group, address) VALUES (?, ?, ?, ?, ?)",
                    (user_id, age, gender, blood_group, address)
                )
            
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
        finally:
            conn.close()
    
    return render_template('signup.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='doctor'")
    doctor_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='patient'")
    patient_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM appointments")
    appointment_count = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         doctor_count=doctor_count,
                         patient_count=patient_count,
                         appointment_count=appointment_count)

@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'user_id' not in session or session['role'] != 'doctor':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM doctors WHERE user_id = ?", (session['user_id'],))
    doctor = cursor.fetchone()
    
    if doctor:
        cursor.execute('''
            SELECT a.id, u.full_name, a.appointment_date, a.appointment_time, a.symptoms, a.status
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE a.doctor_id = ?
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        ''', (doctor['id'],))
        appointments = cursor.fetchall()
    else:
        appointments = []
    
    conn.close()
    
    return render_template('doctor_dashboard.html', appointments=appointments)

@app.route('/patient_dashboard')
def patient_dashboard():
    if 'user_id' not in session or session['role'] != 'patient':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM patients WHERE user_id = ?", (session['user_id'],))
    patient = cursor.fetchone()
    
    if patient:
        cursor.execute('''
            SELECT a.id, u.full_name, d.specialization, a.appointment_date, a.appointment_time, a.status
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            JOIN users u ON d.user_id = u.id
            WHERE a.patient_id = ?
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        ''', (patient['id'],))
        appointments = cursor.fetchall()
    else:
        appointments = []
    
    conn.close()
    
    return render_template('patient_dashboard.html', appointments=appointments)

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if 'user_id' not in session or session['role'] != 'patient':
        flash('Please login as patient to book appointment!', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        symptoms = request.form['symptoms']
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM patients WHERE user_id = ?", (session['user_id'],))
        patient = cursor.fetchone()
        
        if patient:
            cursor.execute(
                "INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, symptoms) VALUES (?, ?, ?, ?, ?)",
                (patient['id'], doctor_id, appointment_date, appointment_time, symptoms)
            )
            conn.commit()
            flash('Appointment booked successfully!', 'success')
            conn.close()
            return redirect(url_for('patient_dashboard'))
        
        conn.close()
    
    # Get all doctors
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.id, u.full_name, d.specialization, d.qualification
        FROM doctors d
        JOIN users u ON d.user_id = u.id
    ''')
    doctors = cursor.fetchall()
    conn.close()
    
    return render_template('appointment.html', doctors=doctors)

@app.route('/view_patients')
def view_patients():
    if 'user_id' not in session or session['role'] not in ['admin', 'doctor']:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.full_name, u.email, u.phone, p.age, p.gender, p.blood_group, p.address
        FROM patients p
        JOIN users u ON p.user_id = u.id
    ''')
    patients = cursor.fetchall()
    conn.close()
    
    return render_template('view_patients.html', patients=patients)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)