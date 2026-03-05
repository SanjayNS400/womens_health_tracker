from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'  # Change this to a secure key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///womens_health.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    records = db.relationship('HealthRecord', backref='user', lazy=True)

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sleep_hours = db.Column(db.Float, nullable=False)
    stress_level = db.Column(db.Integer, nullable=False)
    exercise_minutes = db.Column(db.Integer, nullable=False)
    water_intake = db.Column(db.Integer, nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)
    meditation_minutes = db.Column(db.Integer, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    records = HealthRecord.query.filter_by(user_id=current_user.id).all()
    
    # Convert records to dictionary format
    formatted_records = sorted([{
        'date': record.date.strftime('%Y-%m-%d'),
        'sleep_hours': record.sleep_hours,
        'stress_level': record.stress_level,
        'exercise_minutes': record.exercise_minutes,
        'water_intake': record.water_intake,
        'mood_score': record.mood_score,
        'meditation_minutes': record.meditation_minutes,
        'energy_level': record.mood_score  # Using mood_score as a substitute for energy_level
    } for record in records], key=lambda x: x['date'], reverse=True) if records else []
    
    # Generate predictions and recommendations if records exist
    predictions = None
    recommendations = []
    
    if formatted_records and len(formatted_records) >= 2:
        # Simple prediction based on last few records
        recent_records = formatted_records[:min(5, len(formatted_records))]
        
        # Calculate averages for predictions
        avg_sleep = sum(float(r['sleep_hours']) for r in recent_records) / len(recent_records)
        avg_stress = sum(float(r['stress_level']) for r in recent_records) / len(recent_records)
        avg_exercise = sum(float(r['exercise_minutes']) for r in recent_records) / len(recent_records)
        avg_mood = sum(float(r['mood_score']) for r in recent_records) / len(recent_records)
        avg_water = sum(float(r['water_intake']) for r in recent_records) / len(recent_records)
        avg_meditation = sum(float(r['meditation_minutes']) for r in recent_records) / len(recent_records)
        
        # Prepare chart data
        dates = [r['date'] for r in formatted_records]
        sleep_data = [float(r['sleep_hours']) for r in formatted_records]
        stress_data = [float(r['stress_level']) for r in formatted_records]
        mood_data = [float(r['mood_score']) for r in formatted_records]
        exercise_data = [float(r['exercise_minutes']) for r in formatted_records]
        energy_data = [float(r['energy_level']) for r in formatted_records]
        water_data = [float(r['water_intake']) for r in formatted_records]
        meditation_data = [float(r['meditation_minutes']) for r in formatted_records]
        
        # Calculate trends (positive value means improvement)
        sleep_trend = 1.0 if len(sleep_data) > 1 and float(sleep_data[0]) > float(sleep_data[-1]) else -1.0 if len(sleep_data) > 1 and float(sleep_data[0]) < float(sleep_data[-1]) else 0
        stress_trend = -1.0 if len(stress_data) > 1 and float(stress_data[0]) < float(stress_data[-1]) else 1.0 if len(stress_data) > 1 and float(stress_data[0]) > float(stress_data[-1]) else 0
        mood_trend = 1.0 if len(mood_data) > 1 and float(mood_data[0]) > float(mood_data[-1]) else -1.0 if len(mood_data) > 1 and float(mood_data[0]) < float(mood_data[-1]) else 0
        exercise_trend = 1.0 if len(exercise_data) > 1 and float(exercise_data[0]) > float(exercise_data[-1]) else -1.0 if len(exercise_data) > 1 and float(exercise_data[0]) < float(exercise_data[-1]) else 0
        
        predictions = {
            'predicted_energy': min(10, max(1, int(avg_mood + (avg_sleep / 8) * 2 - (avg_stress / 10) * 2 + (avg_exercise / 60) * 2))),
            'sleep_quality': min(10, max(1, int((avg_sleep / 8) * 10))),
            'overall_health': min(10, max(1, int((avg_mood + avg_sleep / 8 + (10 - avg_stress) / 10 + avg_exercise / 60) / 4 * 10))),
            'importance': {
                'Sleep': min(1.0, max(0.1, avg_sleep / 10)),
                'Exercise': min(1.0, max(0.1, avg_exercise / 60)),
                'Stress Management': min(1.0, max(0.1, (10 - avg_stress) / 10)),
                'Mood': min(1.0, max(0.1, avg_mood / 10))
            },
            'trends': {
                'Sleep': sleep_trend,
                'Stress': stress_trend,
                'Mood': mood_trend,
                'Exercise': exercise_trend
            },
            'chart_data': {
                'dates': dates,
                'sleep': sleep_data,
                'stress': stress_data,
                'mood': mood_data,
                'exercise': exercise_data,
                'energy': energy_data,
                'water': water_data,
                'meditation': meditation_data
            },
            'recommendations': []  # Initialize empty recommendations list
        }
        
        # Generate recommendations based on data
        if avg_sleep < 7:
            predictions['recommendations'].append(
                'Improve Sleep Quality: Try to get 7-8 hours of sleep. Establish a regular sleep schedule and create a restful environment.'
            )
        
        if avg_stress > 5:
            predictions['recommendations'].append(
                'Stress Management: Practice meditation, deep breathing, or yoga to reduce stress levels.'
            )
        
        if avg_exercise < 30:
            predictions['recommendations'].append(
                'Increase Physical Activity: Aim for at least 30 minutes of moderate exercise daily to improve overall health.'
            )
            
        if not predictions['recommendations']:
            predictions['recommendations'].append(
                'Maintain Healthy Habits: You\'re doing well! Continue your current health practices for optimal wellbeing.'
            )
    
    return render_template('dashboard.html',
                         name=current_user.name,
                         records=formatted_records,
                         predictions=predictions)

@app.route('/add_record', methods=['GET', 'POST'])
@login_required
def add_record():
    if request.method == 'POST':
        record = HealthRecord(
            user_id=current_user.id,
            sleep_hours=float(request.form.get('sleep_hours')),
            stress_level=int(request.form.get('stress_level')),
            exercise_minutes=int(request.form.get('exercise_minutes')),
            water_intake=int(request.form.get('water_intake')),
            mood_score=int(request.form.get('mood_score')),
            meditation_minutes=int(request.form.get('meditation_minutes'))
        )
        db.session.add(record)
        db.session.commit()
        flash('Record added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_record.html')

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=8080, debug=True)
