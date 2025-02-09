from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import logging  # הוספת הייבוא החסר
from utils import (
    setup_logger, 
    handle_registration, 
    handle_login, 
    handle_logout,
    check_user_session,
    admin_required,
    handle_admin_user_management,
    get_all_users,
    is_admin,
    validate_full_name,
    validate_phone,
    check_password_hash,
    generate_password_hash
)
from validators import validate_password  # הוספת הייבוא החסר
from models import Game

# הגדרת הלוגר
setup_logger()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

@app.route('/')
def home():
    print("\n=== DEBUG INFO ===")
    print(f"Current Session: {dict(session)}")
    user = check_user_session(User)
    if not user:
        print("❌ User not logged in - redirecting to login")
        return redirect(url_for('login'))
    print(f"✅ Logged in user: {user.full_name}")
    print("================\n")
    return render_template('home.html', full_name=user.full_name, email=user.email, is_admin=is_admin)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return handle_registration(request.form, db, User)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("\n=== LOGIN ATTEMPT ===")
        result = handle_login(request.form, User)
        print(f"Login result: {result}")
        print(f"Session after login: {dict(session)}")
        print("===================\n")
        if isinstance(result, str):
            return redirect(result)
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    return handle_logout()

@app.route('/admin')
@admin_required
def admin_dashboard():
    users = get_all_users(User)
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/user/<action>', methods=['POST'])
@admin_required
def admin_user_action(action):
    return handle_admin_user_management(request.form, db, User, action)

@app.route('/settings')
def settings():
    user = check_user_session(User)
    if not user:
        return redirect(url_for('login'))
    
    # מעביר את אובייקט המשתמש המלא לתבנית
    user_data = {
        'full_name': user.full_name,
        'email': user.email,
        'phone': user.phone,
        'is_admin': user.is_admin
    }
    return render_template('settings.html', user=user_data)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    user = check_user_session(User)
    if not user:
        return redirect(url_for('login'))
    
    try:
        # קבלת הנתונים מהטופס
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        # בדיקת תקינות השם
        name_valid, name_error = validate_full_name(full_name)
        if not name_valid:
            flash(name_error)
            return redirect(url_for('settings'))

        # בדיקת תקינות הטלפון
        if not validate_phone(phone):
            flash('מספר הטלפון אינו תקין')
            return redirect(url_for('settings'))

        # עדכון פרטים
        user.full_name = full_name
        user.phone = phone
        
        # עדכון סיסמה אם הוזנה
        if current_password and new_password:
            if not check_password_hash(user.password, current_password):
                flash('הסיסמה הנוכחית שגויה')
                return redirect(url_for('settings'))
            
            password_valid, password_error = validate_password(new_password)
            if not password_valid:
                flash(password_error)
                return redirect(url_for('settings'))
                
            user.password = generate_password_hash(new_password)

        db.session.commit()
        flash('הפרטים עודכנו בהצלחה!')
        
    except Exception as e:
        db.session.rollback()
        flash('אירעה שגיאה בעדכון הפרטים')
        logging.error(f"Error updating settings: {str(e)}")
    
    return redirect(url_for('settings'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/api/games', methods=['GET'])
@admin_required
def get_games():
    games = Game.query.all()
    return jsonify([{
        'id': game.id,
        'title': game.title,
        'genre': game.genre,
        'price': game.price,
        'quantity': game.quantity,
        'is_loaned': game.is_loaned
    } for game in games])

@app.route('/api/games', methods=['POST'])
@admin_required
def add_game():
    data = request.json
    new_game = Game(
        title=data['title'],
        genre=data['genre'],
        price=float(data['price']),
        quantity=int(data['quantity'])
    )
    db.session.add(new_game)
    db.session.commit()
    return jsonify({'message': 'Game added successfully'}), 201

@app.route('/api/games/<int:game_id>', methods=['DELETE'])
@admin_required
def delete_game(game_id):
    game = Game.query.get_or_404(game_id)
    db.session.delete(game)
    db.session.commit()
    return jsonify({'message': 'Game deleted successfully'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False)
