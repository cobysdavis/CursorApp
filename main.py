from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import GOOGLE_MAPS_API_KEY

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///locations.db'
db = SQLAlchemy(app)

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

