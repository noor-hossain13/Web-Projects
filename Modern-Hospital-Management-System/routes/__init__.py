def register_blueprints(app):
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.doctor import doctor_bp
    from routes.patient import patient_bp
    from routes.ai import ai_bp
    from routes.chat import chat_bp
    from routes.video_call import video_bp  # Add this line
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(video_bp)  # Add this line