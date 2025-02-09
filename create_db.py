from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # יצירת בסיס נתונים חדש
    db.create_all()
    
    # יצירת משתמש אדמין
    admin = User(
        full_name='דניאל אמר',
        email='danielknight536@gmail.com',
        phone='0526286599',  # שנה למספר הטלפון שלך
        password=generate_password_hash('Skempy12', method='pbkdf2:sha256'),
        is_admin=True
    )
    
    db.session.add(admin)
    db.session.commit()
    print("נוצר משתמש אדמין חדש!")