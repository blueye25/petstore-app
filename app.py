# שלב 1: שלד בסיסי של אפליקציית Flask
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import random
import sqlite3
import datetime
import os
import csv

app = Flask(__name__)
app.secret_key = 'secret_key_for_sessions'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# יצירת בסיס נתונים פשוט של לקוחות ופידבק
def init_db():
    conn = sqlite3.connect('customers.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT UNIQUE,
        group_type TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        group_type TEXT,
        choice TEXT,
        additional TEXT,
        payment TEXT,
        timestamp DATETIME
    )''')
    conn.commit()
    conn.close()

# פונקציה לייבוא לקוחות מקובץ CSV
def import_customers_from_csv(csv_file_path):
    with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        conn = sqlite3.connect('customers.db')
        c = conn.cursor()
        for row in reader:
            name = row.get("name", "").strip()
            phone = row.get("phone", "").strip()
            group_type = row.get("group_type", "").strip()
            if name and phone:
                try:
                    c.execute("INSERT OR IGNORE INTO customers (name, phone, group_type) VALUES (?, ?, ?)",
                              (name, phone, group_type))
                except Exception as e:
                    print(f"שגיאה בהוספת לקוח {name}: {e}")
        conn.commit()
        conn.close()

# פונקציה לשמירת פידבק
def save_feedback(name, phone, group_type, choice, additional, payment):
    conn = sqlite3.connect('customers.db')
    c = conn.cursor()
    c.execute('''INSERT INTO feedback (name, phone, group_type, choice, additional, payment, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (name, phone, group_type, choice, additional, payment, datetime.datetime.now()))
    conn.commit()
    conn.close()

# HTML עבור לוגו בראש הדף
LOGO_HTML = '<div style="text-align:center;"><img src="/static/logo.jpeg" alt="לוגו" height="80"></div>'

# דף ניהול לצפייה בפידבק
@app.route('/admin/feedback')
def view_feedback():
    conn = sqlite3.connect('customers.db')
    c = conn.cursor()
    c.execute('''SELECT name, phone, group_type, choice, additional, payment, timestamp FROM feedback ORDER BY timestamp DESC''')
    rows = c.fetchall()
    conn.close()

    html = f'''
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            table {{ width: 100%; border-collapse: collapse; font-family: Arial; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: right; }}
            th {{ background-color: #f2f2f2; }}
            h2 {{ font-family: Arial; }}
        </style>
    </head>
    <body>
        {LOGO_HTML}
        <h2>רשימת פניות לקוחות</h2>
        <table>
            <tr>
                <th>שם</th>
                <th>טלפון</th>
                <th>קבוצה</th>
                <th>בחירה</th>
                <th>פרטים נוספים</th>
                <th>תשלום</th>
                <th>תאריך</th>
            </tr>
    '''
    for row in rows:
        html += f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>"

    html += '''
        </table>
    </body>
    </html>
    '''
    return html

# דף הבית - הזנת מספר טלפון
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        phone = request.form['phone']
        otp = random.randint(1000, 9999)
        session['phone'] = phone
        session['otp'] = str(otp)

        conn = sqlite3.connect('customers.db')
        c = conn.cursor()
        c.execute("SELECT name, group_type FROM customers WHERE phone = ?", (phone,))
        result = c.fetchone()
        conn.close()

        if result:
            session['name'] = result[0]
            session['group_type'] = result[1]
        else:
            session['name'] = "אורח"
            session['group_type'] = "רגיל"

        print(f"OTP שנשלח ללקוח: {otp}")
        return redirect(url_for('verify'))
    return f'''
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            input {{ padding: 10px; width: 100%; margin-bottom: 10px; }}
            button {{ padding: 10px; width: 100%; background-color: #28a745; color: white; border: none; }}
        </style>
    </head>
    <body>
        {LOGO_HTML}
        <h2>ברוך הבא לחנות "משפחה על 4"</h2>
        <form method="POST">
            <label>מספר טלפון:</label>
            <input type="text" name="phone" placeholder="הקלד מספר טלפון" required>
            <button type="submit">שלח קוד אימות</button>
        </form>
    </body>
    </html>
    '''
