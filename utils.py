from flask import flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
import logging
from logging.handlers import RotatingFileHandler
import os
from validators import validate_email, validate_phone, validate_password, validate_full_name
from functools import wraps

# הגדרת לוגר
def setup_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        handlers=[RotatingFileHandler('logs/app.log', maxBytes=100000, backupCount=5)],
        level=logging.ERROR,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

# פונקציות עזר לניהול משתמשים
def handle_registration(form, db, User):
    try:
        # קבלת נתונים מהטופס עם בדיקת קיום
        full_name = form.get('full_name', '').strip()
        email = form.get('email', '').strip()
        phone = form.get('phone', '').strip()
        password = form.get('password', '')

        # בדיקה שכל השדות מלאים
        if not all([full_name, email, phone, password]):
            flash('כל השדות הם חובה')
            return redirect(url_for('register'))

        # בדיקות תקינות
        name_valid, name_error = validate_full_name(full_name)
        if not name_valid:
            flash(name_error)
            return redirect(url_for('register'))
        
        if not validate_email(email):
            flash('כתובת המייל אינה תקינה')
            return redirect(url_for('register'))
        
        if not validate_phone(phone):
            flash('מספר הטלפון אינו תקין')
            return redirect(url_for('register'))
        
        password_valid, password_error = validate_password(password)
        if not password_valid:
            flash(password_error)
            return redirect(url_for('register'))

        # בדיקת קיום משתמש
        if User.query.filter_by(email=email).first():
            flash('אימייל כבר רשום במערכת')
            return redirect(url_for('register'))
        
        if User.query.filter_by(phone=phone).first():
            flash('מספר טלפון כבר רשום במערכת')
            return redirect(url_for('register'))

        # יצירת משתמש חדש
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        # הוספה לסשן
        session['email'] = new_user.email
        session['full_name'] = new_user.full_name
        
        flash('נרשמת בהצלחה!')
        return redirect(url_for('home'))

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error in registration: {str(e)}")
        flash('אירעה שגיאה בתהליך ההרשמה')
        return redirect(url_for('register'))
    except Exception as e:
        logging.error(f"Error in registration: {str(e)}")
        flash('אירעה שגיאה. אנא נסה שוב מאוחר יותר')
        return redirect(url_for('register'))

def handle_login(form, User):
    try:
        email = form.get('email', '').strip()
        password = form.get('password', '')

        if not email or not password:
            flash('יש להזין אימייל וסיסמה')
            return url_for('login')

        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['email'] = user.email
            session['full_name'] = user.full_name
            session['is_admin'] = user.is_admin
            print(f"Setting session for user: {user.full_name}")  # הדפסה לבדיקה
            return url_for('home')
        else:
            flash('אימייל או סיסמה לא נכונים')
            return url_for('login')

    except Exception as e:
        logging.error(f"Error in login: {str(e)}")
        flash('אירעה שגיאה. אנא נסה שוב מאוחר יותר')
        return url_for('login')

def handle_logout():
    try:
        session.clear()
        return redirect(url_for('login'))
    except Exception as e:
        logging.error(f"Error in logout: {str(e)}")
        return redirect(url_for('login'))

def check_user_session(User):
    try:
        if 'email' not in session:
            return None
        
        user = User.query.filter_by(email=session['email']).first()
        if not user:
            session.clear()
            return None
            
        return user
    except Exception as e:
        logging.error(f"Error checking user session: {str(e)}")
        return None

def is_admin():
    """בדיקה האם המשתמש הנוכחי הוא אדמין"""
    try:
        from app import User  # Import User model
        if 'email' not in session:
            return False
        user = User.query.filter_by(email=session['email']).first()
        return user and user.is_admin
    except Exception as e:
        logging.error(f"Error checking admin status: {str(e)}")
        return False

def admin_required(f):
    """דקורטור לבדיקת הרשאות אדמין"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('אין לך הרשאות לגשת לעמוד זה')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def handle_admin_user_management(form, db, User, action):
    """טיפול בפעולות ניהול משתמשים"""
    try:
        if not is_admin():
            flash('אין לך הרשאות לבצע פעולה זו')
            return redirect(url_for('home'))

        user_id = form.get('user_id')
        user = User.query.get(user_id)

        if not user:
            flash('משתמש לא נמצא')
            return redirect(url_for('admin_dashboard'))

        if action == 'delete':
            db.session.delete(user)
        elif action == 'toggle_admin':
            user.is_admin = not user.is_admin
        elif action == 'update':
            user.full_name = form.get('full_name', user.full_name)
            user.email = form.get('email', user.email)
            user.phone = form.get('phone', user.phone)

        db.session.commit()
        flash('הפעולה בוצעה בהצלחה')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in admin action: {str(e)}")
        flash('אירעה שגיאה בביצוע הפעולה')
    
    return redirect(url_for('admin_dashboard'))

def get_all_users(User):
    """קבלת רשימת כל המשתמשים"""
    try:
        return User.query.all()
    except Exception as e:
        logging.error(f"Error fetching users: {str(e)}")
        return [] 