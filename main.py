import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)

# Add this line after app creation
app.secret_key = os.environ.get('SECRET_KEY', 'dev')  # 'dev' is fallback for development

# Get Google Maps API key from environment variable
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
# Database configuration
database_url = os.environ.get('DATABASE_URL')
print(database_url, "DATABASE_URL")
if database_url and database_url.startswith('postgres://'):
    print(database_url, "DATABASE_URL")
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    print(database_url, "DATABASE_URL")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///locations.db'
print(app.config['SQLALCHEMY_DATABASE_URI'], "app.config['SQLALCHEMY_DATABASE_URI']")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    locations = db.relationship('Location', backref='user', lazy=True)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    locations = Location.query.filter_by(user_id=current_user.id).all()
    locations_json = [{
        'id': loc.id,
        'name': loc.name,
        'lat': loc.latitude,
        'lng': loc.longitude,
        'address': loc.address
    } for loc in locations]
    
    return render_template('index.html', 
                         locations=locations,
                         locations_json=locations_json,
                         google_maps_api_key=GOOGLE_MAPS_API_KEY)

@app.route('/add_location', methods=['POST'])
@login_required
def add_location():
    data = request.json
    
    # Check if location already exists for this user
    existing_location = Location.query.filter_by(
        latitude=data['latitude'],
        longitude=data['longitude'],
        user_id=current_user.id
    ).first()
    
    if existing_location:
        return jsonify({
            'success': False,
            'message': 'This location is already saved!'
        })

    new_location = Location(
        name=data['name'],
        latitude=data['latitude'],
        longitude=data['longitude'],
        address=data['address'],
        user_id=current_user.id
    )
    db.session.add(new_location)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/delete_location/<int:id>', methods=['POST'])
def delete_location(id):
    location = Location.query.get_or_404(id)
    db.session.delete(location)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        
        error = 'Invalid username or password'
    
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return 'Username already exists'
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

