from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///passenger_tracking.db'
db = SQLAlchemy(app)



################################################################################
### CONFIG
################################################################################

number_of_seats_in_waiting_area = 500


class WaitingArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_seats = db.Column(db.Integer)
    taken_seats = db.Column(db.Integer)
    free_seats = db.Column(db.Integer)
    total_people = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

class CustomsArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entrance_point = db.Column(db.Integer)
    before_passport_point = db.Column(db.Integer)
    after_passport_point = db.Column(db.Integer)
    exit_point = db.Column(db.Integer)
    current_people_count = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)



def calculate_free_seats(taken_seats, total_seats=number_of_seats_in_waiting_area):
    calculate_free_seats = total_seats - taken_seats
    return calculate_free_seats

def calculate_total_people_in_waiting_area(taken_seats, total_seats=number_of_seats_in_waiting_area, multiplier=1.5):
    # Calculate the percentage of taken seats
    percentage_taken = (taken_seats / total_seats) * 100

    # Assuming each person occupies one seat, estimate the number of people
    estimated_people = int((percentage_taken / 100) * total_seats)

    # Apply the multiplier to account for additional people that are not seated 
    estimated_people_with_multiplier = int(estimated_people * multiplier)

    return estimated_people_with_multiplier




with app.app_context():
    db.create_all()

@app.route('/')
def main_page():
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)

    waiting_area_data = WaitingArea.query.filter(WaitingArea.timestamp.between(start_time, end_time)).all()
    customs_area_data = CustomsArea.query.filter(CustomsArea.timestamp.between(start_time, end_time)).all()

    return render_template('dashboard.html', waiting_area=waiting_area_data, customs_area=customs_area_data)



@app.route('/waiting_area', methods=['POST'])
def receive_waiting_area_data():
    data = request.json
    data['timestamp'] = datetime.fromisoformat(data['timestamp'])
    data['total_seats'] = number_of_seats_in_waiting_area
    data['free_seats'] = calculate_free_seats(data['taken_seats'])
    waiting_area_entry = WaitingArea(**data)
    db.session.add(waiting_area_entry)
    db.session.commit()
    return jsonify({'message': 'Waiting Area data received successfully'}), 201

@app.route('/customs_area', methods=['POST'])
def receive_customs_area_data():
    data = request.json
    data['timestamp'] = datetime.fromisoformat(data['timestamp'])
    customs_area_entry = CustomsArea(**data)
    db.session.add(customs_area_entry)
    db.session.commit()
    return jsonify({'message': 'Customs Area data received successfully'}), 201


def get_waiting_area_data():
    waiting_area_data = WaitingArea.query.all()
    data = {
        'labels': [entry.timestamp.strftime('%Y-%m-%d %H:%M:%S') for entry in waiting_area_data],
        'datasets': [
            {
                'label': 'Taken Seats (Waiting Area)',
                'data': [entry.taken_seats for entry in waiting_area_data],
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1,
                'fill': False
            },
            {
                'label': 'Free Seats (Waiting Area)',
                'data': [entry.free_seats for entry in waiting_area_data],
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1,
                'fill': False
            },
            {
                'label': 'Total Seats (Waiting Area)',
                'data': [entry.total_seats for entry in waiting_area_data],
                'borderColor': 'rgba(255, 0, 178, 0.8)',
                'borderWidth': 1,
                'fill': False
            },
        ]
    }
    return data

def get_customs_area_data():
    customs_area_data = CustomsArea.query.all()
    data = {
        'labels': [entry.timestamp.strftime('%Y-%m-%d %H:%M:%S') for entry in customs_area_data],
        'datasets': [
            {
                'label': 'Exit Point (Customs Area)',
                'data': [entry.exit_point for entry in customs_area_data],
                'borderColor': 'rgba(255, 205, 86, 1)',
                'borderWidth': 1,
                'fill': False
            },
            {
                'label': 'Current People Count (Customs Area)',
                'data': [entry.current_people_count for entry in customs_area_data],
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1,
                'fill': False
            },
            {
                'label': 'Entrance Point Count (Customs Area)',
                'data': [entry.entrance_point for entry in customs_area_data],
                'borderColor': 'rgba(255, 99, 71, 1)',
                'borderWidth': 1,
                'fill': False
            }
        ]
    }
    return data


@app.route('/')
def index():
    return render_template('index_chartjs.html')

@app.route('/waiting_area_data')
def waiting_area_data():
    data = get_waiting_area_data()
    return jsonify(data)

@app.route('/customs_area_data')
def customs_area_data():
    data = get_customs_area_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)