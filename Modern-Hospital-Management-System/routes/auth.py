from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from utils.database import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif current_user.role == 'patient':
            return redirect(url_for('patient.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            if not user.is_active:
                flash('Your account is inactive. Please contact admin.', 'error')
                return redirect(url_for('auth.login'))
            
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('auth.index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'patient')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('auth.register'))
        
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(name=name, email=email, password=hashed_pw, role=role)
        db.session.add(user)
        db.session.flush()
        
        if role == 'patient':
            patient = Patient(
                user_id=user.id,
                age=request.form.get('age'),
                gender=request.form.get('gender'),
                phone=request.form.get('phone'),
                address=request.form.get('address')
            )
            db.session.add(patient)
        elif role == 'doctor':
            doctor = Doctor(
                user_id=user.id,
                specialization=request.form.get('specialization'),
                experience=request.form.get('experience', 0),
                phone=request.form.get('phone'),
                is_approved=False
            )
            db.session.add(doctor)
        
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('auth.login'))