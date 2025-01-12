import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Get Google Maps API key from environment variable
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///locations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200))

@app.route('/')
def index():
    locations = Location.query.all()
    locations_json = [{
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
def add_location():
    data = request.json
    
    # Check if location already exists
    existing_location = Location.query.filter_by(
        latitude=data['latitude'],
        longitude=data['longitude']
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
        address=data['address']
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

