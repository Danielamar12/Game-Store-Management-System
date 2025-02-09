import re

def validate_email(email):
    """
    בדיקת תקינות כתובת אימייל
    מחזיר: True אם תקין, False אם לא
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """
    בדיקת תקינות מספר טלפון ישראלי
    מחזיר: True אם תקין, False אם לא
    """
    pattern = r'^(05[0-9]|07[0-9])[0-9]{7}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    """
    בדיקת חוזק סיסמה
    מחזיר: (תקינות, הודעת שגיאה)
    """
    if len(password) < 8:
        return False, "הסיסמה חייבת להכיל לפחות 8 תווים"
    if not re.search(r"[A-Z]", password):
        return False, "הסיסמה חייבת להכיל לפחות אות גדולה אחת"
    if not re.search(r"[a-z]", password):
        return False, "הסיסמה חייבת להכיל לפחות אות קטנה אחת"
    if not re.search(r"\d", password):
        return False, "הסיסמה חייבת להכיל לפחות ספרה אחת"
    return True, ""

def validate_full_name(full_name):
    """
    בדיקת תקינות שם מלא
    מחזיר: (תקינות, הודעת שגיאה)
    """
    if len(full_name.strip()) < 2:
        return False, "השם חייב להכיל לפחות 2 תווים"
    if not re.match(r'^[\u0590-\u05FF\w\s]{2,}$', full_name):
        return False, "השם יכול להכיל רק אותיות בעברית, אנגלית ורווחים"
    return True, "" 