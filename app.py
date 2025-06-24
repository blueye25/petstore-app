# שלב 1: שלד בסיסי של אפליקציית Flask
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import random
import sqlite3
import datetime
import os
import csv
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'secret_key_for_sessions'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# פרטי Twilio מתוך .env
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")

# שליחת OTP ב-SMS
def send_sms(to_number, message):
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=to_number
        )
        print(f"✅ נשלח SMS ל {to_number}")
    except Exception as e:
        print(f"❌ שגיאה בשליחת SMS: {e}")

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

# ... שאר הקוד לא השתנה

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
        send_sms(phone, f"קוד האימות שלך למשפחה על 4 הוא: {otp}")

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
