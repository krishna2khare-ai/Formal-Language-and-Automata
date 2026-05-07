from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from models import db, User
from flask_login import LoginManager, login_user, current_user
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config.from_object('config')  # Load configuration from config.py
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login if unauthorized access

class FiniteAutomaton:
    def __init__(self):
        self.states = ['Password Verification', 'OTP Verification', 'Fingerprint Verification', 'Authenticated']
        self.current_state = 'Password Verification'

    def transition_to(self, state):
        self.current_state = state

    def verify_password(self, user, password_input):
        if user.check_password(password_input):
            self.transition_to('OTP Verification')
            user.generate_otp()
            print(f"OTP generated: {user.otp}")
            db.session.commit()
            return True
        return False

    def verify_otp(self, user, otp_input):
        if user.otp == otp_input:
            self.transition_to('Fingerprint Verification')
            return True
        return False

    def verify_fingerprint(self, user, fingerprint_input):
        if user.verify_fingerprint(fingerprint_input):
            self.transition_to('Authenticated')
            return True
        return False

fa = FiniteAutomaton()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and fa.verify_password(user, password):
            session['username'] = user.username
            return redirect(url_for('otp_verification'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/otp', methods=['GET', 'POST'])
def otp_verification():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        otp_input = request.form['otp']
        if fa.verify_otp(user, otp_input):
            return redirect(url_for('fingerprint_verification'))
        else:
            flash('Invalid OTP')

    return render_template('otp.html')

@app.route('/fingerprint', methods=['GET', 'POST'])
def fingerprint_verification():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        fingerprint_input = request.form['fingerprint_hash']
        if fa.verify_fingerprint(user, fingerprint_input):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Fingerprint verification failed')

    return render_template('fingerprint.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return f"Welcome, {current_user.username}. You are authenticated!"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Initialize the database
    app.run(debug=True)
