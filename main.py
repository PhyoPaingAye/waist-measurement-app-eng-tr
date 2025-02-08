from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_babel import Babel, gettext

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['BABEL_DEFAULT_LOCALE'] = 'en'  # Default language: English

db = SQLAlchemy(app)
babel = Babel(app, default_locale='en')
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

# Supported languages
LANGUAGES = {
    'en': 'English',
    'tr': 'Türkçe'
}

def get_locale():
    if 'language' in session:
        return session['language']
    return request.accept_languages.best_match(LANGUAGES.keys())

babel.init_app(app, locale_selector=get_locale)

# Simulated Waist Data Based on Body Type
WAIST_DATA = {
    "Slim": 60,
    "Normal": 70,
    "Mild Obesity": 80,
    "Obese": 90,
}

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

# Patient model
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_id = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    blood_pressure = db.Column(db.String(20), nullable=False)
    heart_rate = db.Column(db.String(20), nullable=False)  # New Field
    height = db.Column(db.Float, nullable=False)  # New Field
    weight = db.Column(db.Float, nullable=False)  # New Field
    waist = db.Column(db.Float, nullable=False)
    smoking = db.Column(db.String(10), nullable=False)
    drinking = db.Column(db.String(10), nullable=False)
    exercise = db.Column(db.String(10), nullable=False)
    note = db.Column(db.Text, nullable=True)  # Free-text Note Field
    date_added = db.Column(db.DateTime, default=datetime.utcnow)  # Date Added Field

@app.route("/")
def home():
    return render_template_string(HTML_HOME)

@app.route("/set_language/<language>")
def set_language(language=None):
    if language in LANGUAGES:
        session['language'] = language
        babel.locale_selector_func = lambda: session.get('language', 'en')
    return redirect(url_for("dashboard"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))
        if User.query.filter_by(email=email).first():
            flash(gettext("Email already registered."), "danger")
            return redirect(url_for("signup"))
        if User.query.filter_by(username=username).first():
            flash(gettext("Username already taken."), "danger")
            return redirect(url_for("signup"))
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash(gettext("Sign-Up successful! Please log in."), "success")
        return redirect(url_for("login"))
    return render_template_string(HTML_SIGNUP)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash(gettext("Logged in successfully."), "success")
            return redirect(url_for("dashboard"))
        flash(gettext("Invalid email or password."), "danger")
    return render_template_string(HTML_LOGIN)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash(gettext("Logged out successfully."), "success")
    return redirect(url_for("home"))

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    print("Current language:", session.get('language'))
    if "user_id" not in session:
        return redirect(url_for("login"))

    waist_result = session.get('waist_result')
    waist_warning = session.get('waist_warning')
    session.pop('waist_result', None)
    session.pop('waist_warning', None)

    if request.method == "POST":
        try:
            if "add_patient" in request.form:
                # Add Patient Form Submission
                patient_id = request.form.get("patient_id")
                name = request.form.get("name")
                blood_pressure = request.form.get("blood_pressure")
                heart_rate = request.form.get("heart_rate")
                height = float(request.form.get("height"))
                weight = float(request.form.get("weight"))
                waist = float(request.form.get("waist"))
                smoking = request.form.get("smoking")
                drinking = request.form.get("drinking")
                exercise = request.form.get("exercise")
                note = request.form.get("note")  # Free-text Note
                if Patient.query.filter_by(patient_id=patient_id).first():
                    flash(gettext("Patient ID already exists."), "danger")
                    return redirect(url_for("dashboard"))
                patient = Patient(
                    user_id=session["user_id"],
                    patient_id=patient_id,
                    name=name,
                    blood_pressure=blood_pressure,
                    heart_rate=heart_rate,
                    height=height,
                    weight=weight,
                    waist=waist,
                    smoking=smoking,
                    drinking=drinking,
                    exercise=exercise,
                    note=note
                )
                db.session.add(patient)
                db.session.commit()
                flash(gettext("Patient record added successfully."), "success")

            elif "calculate_waist" in request.form:
                # Waist Calculator Form Submission
                age = request.form.get("age")
                gender = request.form.get("gender")
                height = request.form.get("height")
                weight = request.form.get("weight")
                body_type = request.form.get("body_type")
                # Validate inputs
                if not all([age, gender, height, weight, body_type]):
                    flash(gettext("Please fill out all fields."), "danger")
                    return redirect(url_for("dashboard"))
                if body_type not in WAIST_DATA:
                    flash(gettext("Please select a valid body type."), "danger")
                    return redirect(url_for("dashboard"))
                # Calculate waist measurement
                base_waist = WAIST_DATA[body_type]
                height_adjustment = (int(height) - 150) * 0.4  # 0.4 cm per 1 cm above 150
                weight_adjustment = (int(weight) - 45) * 0.5  # 0.5 cm per 1 kg above 45
                total_waist = base_waist + height_adjustment + weight_adjustment
                session['waist_result'] = round(total_waist - 5, 1)  # Adjusted to reduce by 5 cm
                # Determine cardiovascular risk warning
                session['waist_warning'] = None
                if gender == "Male" and session['waist_result'] >= 102:
                    session['waist_warning'] = gettext("Your waist measurement indicates a risk of cardiovascular diseases. Consult a healthcare provider.")
                elif gender == "Female" and session['waist_result'] >= 88:
                    session['waist_warning'] = gettext("Your waist measurement indicates a risk of cardiovascular diseases. Consult a healthcare provider.")

        except Exception as e:
            db.session.rollback()
            flash(gettext(f"An error occurred: {str(e)}"), "danger")
        return redirect(url_for("dashboard"))

    search_query = request.args.get("search", "")
    query = Patient.query.filter_by(user_id=session["user_id"])
    if search_query:
        query = query.filter(Patient.patient_id.like(f"%{search_query}%") | Patient.name.like(f"%{search_query}%"))
    patients = query.all()
    return render_template_string(HTML_DASHBOARD, patients=patients, search_query=search_query, waist_result=waist_result, waist_warning=waist_warning)

@app.route("/delete_patient/<int:patient_id>")
def delete_patient(patient_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    patient = Patient.query.get_or_404(patient_id)
    if patient.user_id != session["user_id"]:
        flash(gettext("You are not authorized to delete this patient."), "danger")
        return redirect(url_for("dashboard"))
    db.session.delete(patient)
    db.session.commit()
    flash(gettext("Patient record deleted successfully."), "success")
    return redirect(url_for("dashboard"))

# HTML Templates
HTML_HOME = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ _('Waist Measurement App') }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .header { background: linear-gradient(135deg, #007bff, #28a745); color: white; text-align: center; padding: 20px; }
        h1 { margin: 0; font-size: 2rem; }
        p { margin: 10px 0; font-size: 1rem; }
        .btn { padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; transition: background 0.3s; }
        .btn:hover { background-color: #0056b3; }
        .container { max-width: 800px; margin: 20px auto; padding: 20px; background: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border-radius: 10px; }
        footer { text-align: center; margin-top: 20px; font-size: 0.9rem; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ _('Waist Measurement App') }}</h1>
        <p>{{ _('Welcome to Waist Measurement App') }}</p>
        <p>{{ _('The smart way to manage and measure patient waist sizes.') }}</p>
        <a href="{{ url_for('signup') }}" class="btn">{{ _('Sign Up') }}</a>
        <a href="{{ url_for('login') }}" class="btn">{{ _('Login') }}</a>
    </div>
    <div class="container">
        <footer>
            {{ _('Developed by Dr. Phyo Paing Aye') }}
        </footer>
    </div>
</body>
</html>
'''

HTML_SIGNUP = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ _('Sign-Up') }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .header { background: linear-gradient(135deg, #007bff, #28a745); color: white; text-align: center; padding: 20px; }
        h1 { margin: 0; font-size: 2rem; }
        .container { max-width: 500px; margin: 20px auto; padding: 20px; background: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border-radius: 10px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input { width: 100%; padding: 8px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 5px; }
        .btn { padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; transition: background 0.3s; }
        .btn:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ _('Sign-Up') }}</h1>
    </div>
    <div class="container">
        <form action="{{ url_for('signup') }}" method="POST">
            <div class="form-group">
                <label>{{ _('Username') }}:</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>{{ _('Email') }}:</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>{{ _('Password') }}:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn">{{ _('Sign-Up') }}</button>
        </form>
    </div>
</body>
</html>
'''

HTML_LOGIN = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ _('Login') }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .header { background: linear-gradient(135deg, #007bff, #28a745); color: white; text-align: center; padding: 20px; }
        h1 { margin: 0; font-size: 2rem; }
        .container { max-width: 500px; margin: 20px auto; padding: 20px; background: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border-radius: 10px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input { width: 100%; padding: 8px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 5px; }
        .btn { padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; transition: background 0.3s; }
        .btn:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ _('Login') }}</h1>
    </div>
    <div class="container">
        <form action="{{ url_for('login') }}" method="POST">
            <div class="form-group">
                <label>{{ _('Email') }}:</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>{{ _('Password') }}:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn">{{ _('Login') }}</button>
        </form>
    </div>
</body>
</html>
'''

HTML_DASHBOARD = '''
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ _('Patient Dashboard') }}</title>
    <style>
        .flag-icon {
            font-size: 24px;
            margin: 0 5px;
            text-decoration: none;
            cursor: pointer;
        }
        :root {
            --bg-color: #ffffff;
            --text-color: #000000;
            --table-bg: #ffffff;
            --table-border: #ddd;
            --form-bg: #f9f9f9;
        }

        [data-theme="dark"] {
            --bg-color: #1a1a1a;
            --text-color: #ffffff;
            --table-bg: #2d2d2d;
            --table-border: #444;
            --form-bg: #2d2d2d;
        }

        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-color);
        }
        .header { 
            background: linear-gradient(135deg, #007bff, #28a745); 
            color: white; 
            text-align: center; 
            padding: 20px;
            position: relative;
        }

        .theme-switch {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            align-items: center;
        }

        .theme-switch-label {
            margin-right: 10px;
            color: white;
        }

        .switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background-color: #2196F3;
        }

        input:checked + .slider:before {
            transform: translateX(26px);
        }

        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px;
            background-color: var(--table-bg);
        }

        th, td { 
            border: 1px solid var(--table-border); 
            padding: 8px; 
            text-align: left;
        }
        .btn { padding: 8px 16px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; transition: background 0.3s; }
        .btn-danger { background-color: #dc3545; }
        .btn-danger:hover { background-color: #a71d2a; }
        .btn-secondary { background-color: #6c757d; }
        .btn-secondary:hover { background-color: #5a6268; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 5px; }
        footer { text-align: center; margin-top: 20px; font-size: 0.9rem; color: #666; }
        .side-by-side { display: flex; gap: 20px; margin-top: 20px; }
        .side-by-side > div { flex: 1; padding: 20px; background: var(--form-bg); border: 1px solid var(--table-border); border-radius: 10px; }
        @media (max-width: 768px) {
            .side-by-side { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ _('Patient Dashboard') }}</h1>
        <div style="position: absolute; top: 10px; right: 20px;">
            <a href="{{ url_for('set_language', language='en') }}" class="flag-icon">🇬🇧</a>
            <a href="{{ url_for('set_language', language='tr') }}" class="flag-icon">🇹🇷</a>
            <div class="theme-switch" style="margin-top: 15px;">
                <label class="theme-switch-label" for="theme-toggle">{{ _('Dark Mode') }}</label>
                <label class="switch">
                    <input type="checkbox" id="theme-toggle">
                    <span class="slider"></span>
                </label>
            </div>

        </div>
    </div>
    <div class="container">
        <div style="text-align: right; margin: 20px 0;">
            <a href="{{ url_for('logout') }}" class="btn btn-secondary">{{ _('Logout') }}</a>
        </div>
        <form action="{{ url_for('dashboard') }}" method="GET">
            <input type="text" name="search" placeholder="{{ _('Search by Patient ID or Name') }}" value="{{ search_query }}">
            <button type="submit" class="btn">{{ _('Search') }}</button>
        </form>
        <div class="side-by-side">
            <div>
                <h2>{{ _('Add Patient') }}</h2>
                <form action="{{ url_for('dashboard') }}" method="POST">
                    <input type="hidden" name="add_patient" value="true">
                    <div class="form-group">
                        <label>{{ _('Patient ID') }}:</label>
                        <input type="text" name="patient_id" required>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Name') }}:</label>
                        <input type="text" name="name" required>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Blood Pressure') }}:</label>
                        <input type="text" name="blood_pressure" required>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Heart Rate') }}:</label>
                        <input type="text" name="heart_rate" required>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Height (cm)') }}:</label>
                        <input type="number" step="0.01" name="height" required>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Weight (kg)') }}:</label>
                        <input type="number" step="0.01" name="weight" required>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Waist Measurement (cm)') }}:</label>
                        <input type="number" step="0.01" name="waist" required>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Smoking') }}:</label>
                        <select name="smoking" required>
                            <option value="Yes">{{ _('Yes') }}</option>
                            <option value="No">{{ _('No') }}</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Drinking') }}:</label>
                        <select name="drinking" required>
                            <option value="Yes">{{ _('Yes') }}</option>
                            <option value="No">{{ _('No') }}</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Exercise') }}:</label>
                        <select name="exercise" required>
                            <option value="Yes">{{ _('Yes') }}</option>
                            <option value="No">{{ _('No') }}</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Note') }}:</label>
                        <textarea name="note"></textarea>
                    </div>
                    <button type="submit" class="btn">{{ _('Add Patient') }}</button>
                </form>
            </div>
            <div>
                <h2>{{ _('Waist Measurement Calculator') }}</h2>
                <form id="waistCalculatorForm" onsubmit="calculateWaist(event)">
                    <div class="form-group">
                        <label>{{ _('Age (18-70)') }}:</label>
                        <input type="number" name="age" min="18" max="70" required>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Gender') }}:</label>
                        <select name="gender" required>
                            <option value="Male">{{ _('Male') }}</option>
                            <option value="Female">{{ _('Female') }}</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Height (cm)') }}:</label>
                        <input type="number" name="height" required>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Weight (kg)') }}:</label>
                        <input type="number" name="weight" required>
                    </div>
                    <div class="form-group">
                        <label>{{ _('Body Type') }}:</label>
                        <select name="body_type" required>
                            <option value="Slim">{{ _('Slim') }}</option>
                            <option value="Normal">{{ _('Normal') }}</option>
                            <option value="Mild Obesity">{{ _('Mild Obesity') }}</option>
                            <option value="Obese">{{ _('Obese') }}</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">{{ _('Calculate Waist') }}</button>
                </form>
                <div id="waistResult" style="margin-top: 20px; display: none;">
                    <strong>{{ _('Estimated Waist Measurement') }}:</strong> <span id="waistMeasurement"></span> cm
                    <p id="waistWarning" style="color: red; display: none;"></p>
                </div>
                <script>
                function calculateWaist(event) {
                    event.preventDefault();
                    const form = event.target;
                    const formData = new FormData(form);

                    const height = parseInt(formData.get('height'));
                    const weight = parseInt(formData.get('weight'));
                    const bodyType = formData.get('body_type');
                    const gender = formData.get('gender');

                    const waistData = {
                        "Slim": 60,
                        "Normal": 70,
                        "Mild Obesity": 80,
                        "Obese": 90
                    };

                    const baseWaist = waistData[bodyType];
                    const heightAdjustment = (height - 150) * 0.4;
                    const weightAdjustment = (weight - 45) * 0.5;
                    const totalWaist = baseWaist + heightAdjustment + weightAdjustment;
                    const waistResult = Math.round((totalWaist - 5) * 10) / 10;

                    document.getElementById('waistMeasurement').textContent = waistResult;
                    const warningElement = document.getElementById('waistWarning');

                    if ((gender === 'Male' && waistResult >= 102) || 
                        (gender === 'Female' && waistResult >= 88)) {
                        warningElement.textContent = "{{ _('Your waist measurement indicates a risk of cardiovascular diseases. Consult a healthcare provider.') }}";
                        warningElement.style.display = 'block';
                    } else {
                        warningElement.style.display = 'none';
                    }

                    document.getElementById('waistResult').style.display = 'block';
                }
                </script>
            </div>
        </div>

        <h2>{{ _('Patient History') }}</h2>
        <table>
            <thead>
                <tr>
                    <th>{{ _('Date Added') }}</th>
                    <th>{{ _('Patient ID') }}</th>
                    <th>{{ _('Name') }}</th>
                    <th>{{ _('Blood Pressure') }}</th>
                    <th>{{ _('Heart Rate') }}</th>
                    <th>{{ _('Height (cm)') }}</th>
                    <th>{{ _('Weight (kg)') }}</th>
                    <th>{{ _('Waist (cm)') }}</th>
                    <th>{{ _('Smoking') }}</th>
                    <th>{{ _('Drinking') }}</th>
                    <th>{{ _('Exercise') }}</th>
                    <th>{{ _('Note') }}</th>
                    <th>{{ _('Actions') }}</th>
                </tr>
            </thead>
            <tbody>
                {% for patient in patients %}
                <tr>
                    <td>{{ patient.date_added.strftime('%d.%m.%Y') }}</td>
                    <td>{{ patient.patient_id }}</td>
                    <td>{{ patient.name }}</td>
                    <td>{{ patient.blood_pressure }}</td>
                    <td>{{ patient.heart_rate }}</td>
                    <td>{{ patient.height }}</td>
                    <td>{{ patient.weight }}</td>
                    <td>{{ patient.waist }}</td>
                    <td>{{ patient.smoking }}</td>
                    <td>{{ patient.drinking }}</td>
                    <td>{{ patient.exercise }}</td>
                    <td>{{ patient.note }}</td>
                    <td><a href="{{ url_for('delete_patient', patient_id=patient.id) }}" class="btn btn-danger">{{ _('Delete') }}</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <footer>
            {{ _('Developed by Dr. Phyo Paing Aye') }}
        </footer>
    </div>
    <script>
        const themeToggle = document.getElementById('theme-toggle');
        const html = document.documentElement;

        themeToggle.addEventListener('change', () => {
            html.dataset.theme = themeToggle.checked ? 'dark' : 'light';
        });
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080, debug=True)