from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from sqlalchemy import or_, and_, func, DateTime
import traceback, csv, io
from json.decoder import JSONDecodeError
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///passenger_tracking.db'
db = SQLAlchemy(app)

################################################################################
### CONFIG
################################################################################

seat_sensor_dict = {
    'druksensor': "UIT",
    'druksensor_1': "UIT",
    'druksensor_2': "UIT",
    'druksensor_3': "UIT",
    'druksensor_4': "UIT",
    'druksensor_5': "UIT",
    'druksensor_6': "UIT",
    'druksensor_7': "UIT",
    'druksensor_8': "UIT",
    'druksensor_9': "UIT",
    'druksensor_10': "UIT",
}

number_of_seats_in_waiting_area = 10

class WaitingArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_seats = db.Column(db.Integer)
    taken_seats = db.Column(db.Integer)
    free_seats = db.Column(db.Integer)
    total_people = db.Column(db.Integer)
    sensor_id = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(DateTime, default=datetime.utcnow)

class CustomsArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entrance_point = db.Column(db.Integer)
    before_passport_point = db.Column(db.Integer)
    after_passport_point = db.Column(db.Integer)
    exit_point = db.Column(db.Integer)
    current_people_count = db.Column(db.Integer)
    timestamp = db.Column(DateTime, default=datetime.utcnow)



def calculate_free_seats(taken_seats, total_seats=number_of_seats_in_waiting_area):
    """
    Functie die het aantal stoelen berekend die niet bezet zijn.
    """
    calculate_free_seats = total_seats - taken_seats
    return calculate_free_seats

def calculate_total_people_in_waiting_area(taken_seats, total_seats=number_of_seats_in_waiting_area, multiplier=1.3):
    """
    Functie om aantal totale personen in de ruimte te berkenen. er vanuitgaande dat niet elke persoon in de ruimte op een stoel zit (staan, leunen, lopen, zitten op de grond).
    """
    percentage_taken = (taken_seats / total_seats) * 100
    estimated_people = int((percentage_taken / 100) * total_seats)
    estimated_people_with_multiplier = int(estimated_people * multiplier)
    return estimated_people_with_multiplier





with app.app_context():
    db.create_all()

@app.route('/')
def main_page():
    # Set the timezone to CET (Central European Time)
    cet_timezone = timezone(timedelta(hours=1))

    # Get the current time in the Netherlands timezone
    current_time = datetime.now(cet_timezone)

    # Set start_time to midnight of today
    start_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    # Set end_time to the current time
    end_time = current_time

    waiting_area_data = WaitingArea.query.filter(WaitingArea.timestamp.between(start_time, end_time)).all()
    customs_area_data = CustomsArea.query.filter(CustomsArea.timestamp.between(start_time, end_time)).all()
    
    return render_template('dashboard.html', waiting_area=waiting_area_data, customs_area=customs_area_data)



@app.route('/waiting_area', methods=['POST'])
def receive_waiting_area_data():
    try:
        data = request.json
        print(f"Binnengekomen Data op /waiting_area:\n    {data}\n")

        current_time = datetime.now()
        data['timestamp'] = current_time
        sensor_id = data['Sensor']
        status = data.get('Status', '').upper()
        taken_seats = calculate_taken_seats_dict(sensor_id=sensor_id, sensor_status=status, dictionary=seat_sensor_dict)

        # taken_seats = 1 if status == 'AAN' else 0
        new_sensor_data = WaitingArea(
            total_seats=number_of_seats_in_waiting_area,
            taken_seats=taken_seats,
            free_seats=calculate_free_seats(taken_seats),
            total_people=calculate_total_people_in_waiting_area(taken_seats),
            sensor_id=sensor_id,
            status=status,
            timestamp=current_time
        )

        db.session.add(new_sensor_data)
        db.session.commit()
        return jsonify({'message': 'Waiting Area data received successfully'}), 201

    except ValueError as ve:
        db.session.rollback()  # Rollback in case of error
        print(f"ValueError occurred: {ve}")
        return jsonify({'message': 'Error processing the waiting area data'}), 400
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"An error occurred: {e}")
        return jsonify({'message': 'Error processing the waiting area data'}), 500


@app.route('/customs_area', methods=['POST'])
def receive_customs_area_data():
    try:
        data = request.json
        print(f"Binnengekomen Data op /customs_area:\n    {data}\n")

        current_time = datetime.now() 
        data['timestamp'] = current_time
        current_time = datetime.now() 
        data['timestamp'] = current_time

        # Maak een nieuw CustomsArea-object en commit naar de database
        customs_area_data = CustomsArea(
            entrance_point=data['entrance_point'],
            before_passport_point=data['before_passport_point'],
            after_passport_point=data['after_passport_point'],
            exit_point=data['exit_point'],
            current_people_count=data['current_people_count'],
            timestamp=current_time
        )

        db.session.add(customs_area_data)
        db.session.commit()

        return jsonify({'message': 'Customs Area data received successfully'}), 201
    except JSONDecodeError:
        return jsonify({'message': 'Invalid JSON format'}), 400
    except Exception as e:
        print(f"An error has occurred: {e}")
        return jsonify({'message': 'Error'}), 500

def get_waiting_area_data():
    """
    Functie die de data uit de database haalt voor de "Waiting Area" en weergeeft in een grafiek op de webapplicatie
    """
    cet_timezone = timezone(timedelta(hours=1))
    current_time = datetime.now(cet_timezone)
    end_time = current_time
    start_time = end_time - timedelta(hours=24)

    waiting_area_data = WaitingArea.query.filter(WaitingArea.timestamp.between(start_time, end_time)).all()
    waiting_area_data = sorted(waiting_area_data, key=lambda entry: entry.timestamp)
    data = {
        'labels': [entry.timestamp.strftime('%Y-%m-%d %H:%M:%S') for entry in waiting_area_data],
        'datasets': [
            {
                'label': 'Taken Seats (Waiting Area)',
                'data': [entry.taken_seats for entry in waiting_area_data],
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1,
                'backgroundColor': 'rgba(75, 192, 192, 0.9)',  
                'fill': False
            },
            {
                'label': 'Free Seats (Waiting Area)',
                'data': [entry.free_seats for entry in waiting_area_data],
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1,
                'backgroundColor': 'rgba(255, 99, 132, 0.9)',  
                'fill': False
            },
            {
                'label': 'Total Seats (Waiting Area)',
                'data': [entry.total_seats for entry in waiting_area_data],
                'borderColor': 'rgba(255, 0, 178, 1)',
                'borderWidth': 1,
                'backgroundColor': 'rgba(255, 0, 178, 0.9)', 
                'fill': False
            },
            {
                'label': 'Total People (Waiting Area)',
                'data': [entry.total_people for entry in waiting_area_data],
                'borderColor': 'rgba(51, 255, 51, 1)',
                'borderWidth': 1,
                'backgroundColor': 'rgba(51, 255, 51, 0.9)', 
                'fill': False
            },
        ]
    }


    return data

def get_customs_area_data():
    """
    Functie die de data uit de database haalt voor de Customs Area" en weergeeft in een grafiek op de webapplicatie
    """
    cet_timezone = timezone(timedelta(hours=1))
    current_time = datetime.now(cet_timezone)
    end_time = current_time
    start_time = end_time - timedelta(hours=24)

    customs_area_data = CustomsArea.query.filter(CustomsArea.timestamp.between(start_time, end_time)).all()
    customs_area_data = sorted(customs_area_data, key=lambda entry: entry.timestamp)
    print(customs_area_data)
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
                },
        ]
    }
    return data


@app.route('/get_date_range', methods=['GET'])
def get_date_range():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Convert start_date and end_date to datetime objects
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Add one day to include the end_date

        print(f"Start Date: {start_datetime}")
        print(f"End Date: {end_datetime}")

        # Use OR condition to filter entries within the specified range
        customs_area_data = CustomsArea.query.filter(
            or_(
                and_(CustomsArea.timestamp >= start_datetime, CustomsArea.timestamp < end_datetime),
                and_(CustomsArea.timestamp >= start_datetime, CustomsArea.timestamp < end_datetime)
            )
        ).all()

        customs_area_data = sorted(customs_area_data, key=lambda entry: entry.timestamp)

        waiting_area_data = WaitingArea.query.filter(
            or_(
                and_(WaitingArea.timestamp >= start_datetime, WaitingArea.timestamp < end_datetime),
                and_(WaitingArea.timestamp >= start_datetime, WaitingArea.timestamp < end_datetime)
            )
        ).all()

        waiting_area_data = sorted(waiting_area_data, key=lambda entry: entry.timestamp)

        data_customs_filter_date = {
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
                },
            ]
        }

        data_waiting_filter_date = {
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
                {
                    'label': 'Total People (Waiting Area)',
                    'data': [entry.total_people for entry in waiting_area_data],
                    'borderColor': 'rgba(51, 255, 51, 1)',
                    'borderWidth': 1,
                    'fill': False
            },
            ]
        }
        
        return jsonify({'waiting_area': data_waiting_filter_date, 'customs_area': data_customs_filter_date})

    except Exception as e:
        print(f"An error occurred in /get_date_range: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500



def calculate_average_occupancy(data_points):
    """
    Calculate the average occupancy over multiple data points.
    """
    if data_points == None or data_points == "":
        return ""
    
    total_taken_seats = sum(entry.taken_seats for entry in data_points)
    total_total_seats = sum(entry.total_seats for entry in data_points)

    if total_total_seats == 0:
        return 0

    average_occupancy = (total_taken_seats / total_total_seats) * 100
    return round(average_occupancy, 1)


def calculate_peak_occupancy(data_points):
    """
    Calculate the peak occupancy over multiple data points.
    """
    if data_points == None or data_points == "" or data_points == []:
        return ""
    
    occupancies = [(entry.taken_seats / entry.total_seats) * 100 for entry in data_points if entry.total_seats != 0]
    if not occupancies:
        return "" 

    max_occupancy = max(occupancies)
    return round(max_occupancy, 1)


def calculate_occupancy_rate(taken_seats, total_seats=number_of_seats_in_waiting_area):
    """
    Calculate the occupancy rate.
    """
    return ""  


def calculate_seat_turnover_rate(free_seats, total_seats=number_of_seats_in_waiting_area):
    """
    Calculate the seat turnover rate.
    """
    return ""  


def calculate_average_wait_time(total_people, seat_turnover_rate):
    """
    Calculate the average wait time.
    """
    return ""  


def get_average_occupancy_custom(data_points):
    if data_points == None or data_points == "" or data_points == []:
        return ""
    total_occupancy = db.session.query(func.avg(CustomsArea.current_people_count)).scalar()
    return total_occupancy

def get_peak_occupancy_custom(data_points):
    if data_points == None or data_points == "" or data_points == []:
        return ""
    peak_occupancy = db.session.query(func.max(CustomsArea.current_people_count)).scalar()
    return peak_occupancy

def get_flow_rate_custom(data_points):
    if data_points == None or data_points == "" or data_points == []:
        return ""
    return "" 

def get_passenger_turnaround_time_custom(data_points):
    if data_points == None or data_points == "" or data_points == []:
        return ""
    return ""

def get_average_wait_time_custom(data_points):
    if data_points == None or data_points == "" or data_points == []:
        return ""
    return ""

def calculate_taken_seats_dict(sensor_id, sensor_status, dictionary=seat_sensor_dict):
    taken_seats = 0
    print(f"Sensor ID: {sensor_id}")
    print(f"Sensor Status: {sensor_status}")

    for value in dictionary.values():
        if value == "AAN":
            taken_seats += 1

    return taken_seats

@app.route('/get_statistics', methods=['GET'])
def get_statistics():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        print(f"Start Date: {start_datetime}")
        print(f"End Date: {end_datetime}")

        customs_area_data = CustomsArea.query.filter(
            or_(
                and_(CustomsArea.timestamp >= start_datetime, CustomsArea.timestamp < end_datetime),
                and_(CustomsArea.timestamp >= start_datetime, CustomsArea.timestamp < end_datetime)
            )
        ).all()

        customs_area_data = sorted(customs_area_data, key=lambda entry: entry.timestamp)

        waiting_area_data = WaitingArea.query.filter(
            or_(
                and_(WaitingArea.timestamp >= start_datetime, WaitingArea.timestamp < end_datetime),
                and_(WaitingArea.timestamp >= start_datetime, WaitingArea.timestamp < end_datetime)
            )
        ).all()

        waiting_area_data = sorted(waiting_area_data, key=lambda entry: entry.timestamp)

        if waiting_area_data:
            avg_occupancy_waiting = calculate_average_occupancy(waiting_area_data)
            peak_occupancy_waiting = calculate_peak_occupancy(waiting_area_data)
            
            if waiting_area_data[-1].total_seats != 0:
                occupancy_rate_waiting = calculate_occupancy_rate(waiting_area_data[-1].taken_seats, waiting_area_data[-1].total_seats)
                seat_turnover_rate_waiting = calculate_seat_turnover_rate(waiting_area_data[-1].total_seats, waiting_area_data[-1].free_seats)
                avg_wait_time_waiting = calculate_average_wait_time(waiting_area_data[-1].total_people, seat_turnover_rate_waiting)
            else:
                occupancy_rate_waiting = seat_turnover_rate_waiting = avg_wait_time_waiting = ""
        else:
            avg_occupancy_waiting = peak_occupancy_waiting = occupancy_rate_waiting = seat_turnover_rate_waiting = avg_wait_time_waiting = ""



        print("avg occupancy" + str(avg_occupancy_waiting))
        print("Peak occupancy" + str(peak_occupancy_waiting))
        print("rate occupancy" + str(occupancy_rate_waiting))

        # Calculate statistics for customs area
        if customs_area_data:
            avg_occupancy_custom = get_average_occupancy_custom(customs_area_data)
            peak_occupancy_custom = get_peak_occupancy_custom(customs_area_data)
            avg_flow_rate_custom = get_flow_rate_custom(customs_area_data)
            avg_passenger_turnaround_time_custom = get_passenger_turnaround_time_custom(customs_area_data)
            avg_wait_time_custom = get_average_wait_time_custom(customs_area_data)

        else:
            avg_occupancy_custom = peak_occupancy_custom = avg_flow_rate_custom = avg_passenger_turnaround_time_custom = avg_wait_time_custom = ""

        return jsonify({
            'avg_occupancy_waiting': avg_occupancy_waiting,
            'peak_occupancy_waiting': peak_occupancy_waiting,
            'occupancy_rate_waiting': occupancy_rate_waiting,
            'seat_turnover_rate_waiting': seat_turnover_rate_waiting,
            'avg_wait_time_waiting': avg_wait_time_waiting,
            'avg_occupancy_custom': avg_occupancy_custom,
            'peak_occupancy_custom': peak_occupancy_custom,
            'avg_flow_rate_custom': avg_flow_rate_custom,
            'avg_passenger_turnaround_time': avg_passenger_turnaround_time_custom,
            'avg_wait_time_custom': avg_wait_time_custom,
        })

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/export_data_to_csv')
def export_data_to_csv():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        area = request.args.get('area')

        # Convert start_date and end_date to datetime objects
        start_datetime = datetime.strptime(start_date, '%m/%d/%Y')
        end_datetime = datetime.strptime(end_date, '%m/%d/%Y') + timedelta(days=1)

        # Filter data based on the area
        if area == 'waiting_area':
            data = WaitingArea.query.filter(WaitingArea.timestamp.between(start_datetime, end_datetime)).all()
            # Define the column names for the CSV file
            column_names = ['ID', 'Total Seats', 'Taken Seats', 'Free Seats', 'Total People', 'Timestamp']
            # Create CSV data
            csv_data = [[getattr(d, column) for column in ['id', 'total_seats', 'taken_seats', 'free_seats', 'total_people', 'timestamp']] for d in data]
        elif area == 'customs_area':
            data = CustomsArea.query.filter(CustomsArea.timestamp.between(start_datetime, end_datetime)).all()
            column_names = ['ID', 'Entrance Point', 'Before Passport Point', 'After Passport Point', 'Exit Point', 'Current People Count', 'Timestamp']
            csv_data = [[getattr(d, column) for column in ['id', 'entrance_point', 'before_passport_point', 'after_passport_point', 'exit_point', 'current_people_count', 'timestamp']] for d in data]
        else:
            return jsonify({'error': 'Invalid area specified'}), 400

        # Create a string buffer
        buffer = io.StringIO()
        csv_writer = csv.writer(buffer)
        csv_writer.writerow(column_names)
        csv_writer.writerows(csv_data)
        buffer.seek(0)

        # Send the CSV file as a download
        return send_file(
            io.BytesIO(buffer.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{area}_{start_date}_to_{end_date}.csv"
        )
    
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/waiting_area_data')
def waiting_area_data():
    data = get_waiting_area_data()
    return jsonify(data)

@app.route('/customs_area_data')
def customs_area_data():
    data = get_customs_area_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=80, host="0.0.0.0")