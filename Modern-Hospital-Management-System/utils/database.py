from models import db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        create_admin_user()

def create_admin_user():
    from models.user import User
    
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(
            name='Admin',
            email='admin@hospital.com',
            password=hashed_pw,
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin@hospital.com / admin123")