from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from sqlalchemy import or_, and_, func, DateTime
import traceback, csv, io
from json.decoder import JSONDecodeError
import random

################################################################################
### CONFIG
################################################################################

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///passenger_tracking.db'
db = SQLAlchemy(app)

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

CHART_TIME_FRAME = timedelta(minutes=1)

################################################################################
### DATABASE
################################################################################

class WaitingArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_seats = db.Column(db.Integer)
    taken_seats = db.Column(db.Integer)
    free_seats = db.Column(db.Integer)
    total_people = db.Column(db.Integer)
    sensor_id = db.Column(db.String(50), nullable=False)
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


################################################################################
### FUNCTIONS CALCULATIONS
################################################################################


def calculate_free_seats(taken_seats, total_seats=number_of_seats_in_waiting_area):
    """
    Function that calculates the number of unoccupied seats.

    Parameters:
    - taken_seats: The number of seats that are currently occupied.
    - total_seats: The total number of seats available in the waiting area (default value obtained from a predefined constant).

    Returns:
    - calculate_free_seats: The number of unoccupied seats.
    """
    calculate_free_seats = total_seats - taken_seats
    return calculate_free_seats

def calculate_total_people_in_waiting_area(taken_seats, total_seats=number_of_seats_in_waiting_area, multiplier=1.3):
    """
    Function to calculate the total number of people in the space, assuming not every person in the space is seated (standing, leaning, walking, sitting on the floor).

    Parameters:
    - taken_seats: The number of seats that are currently occupied.
    - total_seats: The total number of seats available in the waiting area (default value obtained from a predefined constant).
    - multiplier: A factor to estimate the total number of people based on the number of taken seats (default value is 1.3, which is an empirical multiplier).

    Returns:
    - estimated_people_with_multiplier: The estimated total number of people in the waiting area, considering the multiplier.
    """
    percentage_taken = (taken_seats / total_seats) * 100
    estimated_people = int((percentage_taken / 100) * total_seats)
    estimated_people_with_multiplier = int(estimated_people * multiplier)
    return estimated_people_with_multiplier



with app.app_context():
    db.create_all()

@app.route('/')
def main_page():
    """
    Function that provides a route to the "main_page". This page contains the graphs, and this function ensures that the correct data is displayed in the appropriate graphs. 
    It retrieves the necessary data from the corresponding database.
    """

    # Set the timezone to CET (Central European Time)
    cet_timezone = timezone(timedelta(hours=1))

    # Get the current time in the Netherlands timezone
    current_time = datetime.now(cet_timezone)

    # Set start_time to midnight of today
    start_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    # Set end_time to the current time
    end_time = current_time

    # Query the WaitingArea table in the database for data within the time frame from start_time to end_time
    waiting_area_data = WaitingArea.query.filter(WaitingArea.timestamp.between(start_time, end_time)).all()

    # Query the CustomsArea table in the database for data within the time frame from start_time to end_time
    customs_area_data = CustomsArea.query.filter(CustomsArea.timestamp.between(start_time, end_time)).all()
    
    # Render the dashboard.html template, passing the waiting_area_data and customs_area_data to be used in the template
    return render_template('dashboard.html', waiting_area=waiting_area_data, customs_area=customs_area_data)



@app.route('/waiting_area', methods=['POST'])
def receive_waiting_area_data():
    """
    Function for receiving data on route: "/waiting_area". This function receives the data, calls other functions to perform necessary calculations, 
    and inserts the correct data into the Waiting area database.
    """
    try:
        # Receive JSON data from the request
        data = request.json
        print(f"Binnengekomen Data op /waiting_area:\n    {data}\n")

        # Get the current time
        current_time = datetime.now()

        # Add timestamp to the received data
        data['timestamp'] = current_time

        # Extract sensor ID and status from the received data
        sensor_id = data['Sensor']
        status = data.get('Status', '').upper()

        # Calculate taken seats based on sensor data
        taken_seats = calculate_taken_seats_dict(sensor_id=sensor_id, sensor_status=status, dictionary=seat_sensor_dict)

        # Create a new WaitingArea object with calculated data
        new_sensor_data = WaitingArea(
            total_seats=number_of_seats_in_waiting_area,
            taken_seats=taken_seats,
            free_seats=calculate_free_seats(taken_seats),
            total_people=calculate_total_people_in_waiting_area(taken_seats),
            sensor_id=sensor_id,
            status=status,
            timestamp=current_time
        )

        # Add new data to the database
        db.session.add(new_sensor_data)
        db.session.commit()

        # Clean up old data
        earliest_time_to_keep = current_time - CHART_TIME_FRAME
        WaitingArea.query.filter(WaitingArea.timestamp < earliest_time_to_keep).delete()
        db.session.commit()

        # Return success message
        return jsonify({'message': 'Waiting Area data received successfully'}), 201

    except ValueError as ve:
        db.session.rollback()  # Rollback in case of error
        print(f"ValueError occurred: {ve}")
        return jsonify({'message': 'Error processing the Waiting Area data'}), 400
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"An error occurred: {e}")
        return jsonify({'message': 'Error processing the Waiting Area data'}), 500



@app.route('/customs_area', methods=['POST'])
def receive_customs_area_data():
    """
    Function for receiving data on route: "/customs_area". This function receives the data, calls other functions to perform necessary calculations, 
    and inserts the correct data into the Customs Area database.
    """
    try:
        # Receive JSON data from the request
        data = request.json
        print(f"Binnengekomen Data op /customs_area:\n    {data}\n")

        # Get the current time
        current_time = datetime.now()
        
        # Add timestamp to the received data
        data['timestamp'] = current_time

        # Calculate the total number of people currently in the customs area
        current_people_count = data['entrance_point'] + data['before_passport_point'] + data['after_passport_point']

        # Create a new CustomsArea object and commit it to the database
        customs_area_data = CustomsArea(
            entrance_point=data['entrance_point'],
            before_passport_point=data['before_passport_point'],
            after_passport_point=data['after_passport_point'],
            exit_point=data['exit_point'],
            current_people_count=current_people_count,
            timestamp=current_time 
        )

        db.session.add(customs_area_data)
        db.session.commit()

        # Clean up old data
        earliest_time_to_keep = current_time - CHART_TIME_FRAME
        CustomsArea.query.filter(CustomsArea.timestamp < earliest_time_to_keep).delete()
        db.session.commit()

        # Return success message
        return jsonify({'message': 'Customs Area data received successfully'}), 201

    except JSONDecodeError:
        # Return error message for invalid JSON format
        return jsonify({'message': 'Invalid JSON format'}), 400

    except Exception as e:
        # Handle other exceptions and return error message
        print(f"An error has occurred: {e}")
        return jsonify({'message': 'Error'}), 500


def get_waiting_area_data():
    """
    Function that retrieves data from the database for the "Waiting Area" and displays it in a graph on the web application.
    """
    # Set the timezone to CET (Central European Time)
    cet_timezone = timezone(timedelta(hours=1))

    # Get the current time in the CET timezone
    current_time = datetime.now(cet_timezone)

    # Set the end time to the current time
    end_time = current_time

    # Set the start time to 5 minutes before the current time
    start_time = end_time - timedelta(minutes=5)

    # Query the WaitingArea table in the database for data within the time frame from start_time to end_time
    waiting_area_data = WaitingArea.query.filter(WaitingArea.timestamp.between(start_time, end_time)).all()

    # Sort the waiting area data based on timestamp
    waiting_area_data = sorted(waiting_area_data, key=lambda entry: entry.timestamp)

    # Prepare data for the graph
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
    Function that retrieves data from the database for the "Customs Area" and displays it in a graph on the web application.
    """
    # Set the timezone to CET (Central European Time) and get the current time zone
    cet_timezone = timezone(timedelta(hours=1))
    current_time = datetime.now(cet_timezone)

    # Set the end time to the current time
    end_time = current_time

    # Set the start time to 24 hours before the current time
    start_time = end_time - timedelta(hours=24)

    # Query the CustomsArea table in the database for data within the time frame from start_time to end_time
    customs_area_data = CustomsArea.query.filter(CustomsArea.timestamp.between(start_time, end_time)).all()

    # Sort the customs area data based on timestamp
    customs_area_data = sorted(customs_area_data, key=lambda entry: entry.timestamp)

    # Prepare data for the graph
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
    """
    Function that retrieves the appropriate data for the selected dates. These dates are selected on the web page and can range from a single day to multiple days/weeks/months/years, etc.
    """
    try:
        # Get start_date and end_date from the query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Convert start_date and end_date to datetime objects
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Add one day to include the end_date

        print(f"Start Date: {start_datetime}")
        print(f"End Date: {end_datetime}")

        # Query the CustomsArea table in the database for data within the specified range
        customs_area_data = CustomsArea.query.filter(
            CustomsArea.timestamp.between(start_datetime, end_datetime)
        ).all()

        # Sort the customs area data based on timestamp
        customs_area_data = sorted(customs_area_data, key=lambda entry: entry.timestamp)

        # Query the WaitingArea table in the database for data within the specified range
        waiting_area_data = WaitingArea.query.filter(
            WaitingArea.timestamp.between(start_datetime, end_datetime)
        ).all()

        # Sort the waiting area data based on timestamp
        waiting_area_data = sorted(waiting_area_data, key=lambda entry: entry.timestamp)

        # Prepare data for the Customs Area chart
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

        # Prepare data for the Waiting Area chart
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
        
        # Return the data for both charts as JSON
        return jsonify({'waiting_area': data_waiting_filter_date, 'customs_area': data_customs_filter_date})

    except Exception as e:
        # Handle any exceptions and return an error message
        print(f"An error occurred in /get_date_range: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500




def calculate_average_occupancy(data_points):
    """
    Calculate the average occupancy over multiple data points.
    """
    # Check if data_points is None, empty, or an empty string
    if data_points is None or data_points == "":
        return ""
    
    # Sum up taken seats and total seats from data points
    total_taken_seats = sum(entry.taken_seats for entry in data_points)
    total_total_seats = sum(entry.total_seats for entry in data_points)

    # Check if the total total seats is zero to avoid division by zero
    if total_total_seats == 0:
        return 0

    # Calculate the average occupancy
    average_occupancy = (total_taken_seats / total_total_seats) * 100
    return round(average_occupancy, 1)


def calculate_peak_occupancy(data_points):
    """
    Function to calculate the peak occupancy over multiple data points.
    """
    # Check if data_points is None, empty, or an empty list
    if data_points is None or data_points == "" or data_points == []:
        return ""
    
    # Calculate occupancies from data points
    occupancies = [(entry.taken_seats / entry.total_seats) * 100 for entry in data_points if entry.total_seats != 0]

    # Check if occupancies list is empty
    if not occupancies:
        return "" 

    # Find the maximum occupancy
    max_occupancy = max(occupancies)
    return round(max_occupancy, 1)


def get_average_occupancy_custom(data_points):
    """
    Function to calculate the occupancy rate in the Customs Area
    """
    # Check if data_points is None, empty, or an empty list
    if data_points is None or data_points == "" or data_points == []:
        return ""
    
    # Calculate the total occupancy using SQLAlchemy aggregate function
    total_occupancy = db.session.query(func.avg(CustomsArea.current_people_count)).scalar()
    return total_occupancy


def get_peak_occupancy_custom(data_points):
    """
    Function to calculate the peak occupancy rate in the Customs Area
    """
    # Check if data_points is None, empty, or an empty list
    if data_points is None or data_points == "" or data_points == []:
        return ""
    
    # Calculate the peak occupancy using SQLAlchemy aggregate function
    peak_occupancy = db.session.query(func.max(CustomsArea.current_people_count)).scalar()
    return peak_occupancy


def calculate_taken_seats_dict(sensor_id, sensor_status, dictionary=seat_sensor_dict):
    """
    Function to calculate how many seats are taken inside the Waiting Area
    """
    # Print sensor_id and sensor_status for debugging purposes
    print(f"Sensor ID: {sensor_id}")
    print(f"Sensor Status: {sensor_status}")

    # Update the dictionary with sensor_id and sensor_status
    dictionary[sensor_id] = sensor_status  

    # Count the number of seats that are "AAN" (occupied) in the dictionary
    taken_seats = sum(1 for value in dictionary.values() if value == "AAN")

    # Print the updated dictionary and the number of taken seats for debugging purposes
    print(f"Updated seat_sensor_dict: {dictionary}")
    print(f"Taken Seats: {taken_seats}")
    return taken_seats


@app.route('/get_statistics', methods=['GET'])
def get_statistics():
    """
    Function to send the statistics to the webpage. This function is called by our Javascript file
    """
    try:
        # Get start_date and end_date from the query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Convert start_date and end_date to datetime objects
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Add one day to include the end_date

        print(f"Start Date: {start_datetime}")
        print(f"End Date: {end_datetime}")

        # Query the CustomsArea table in the database for data within the specified range
        customs_area_data = CustomsArea.query.filter(
            or_(
                and_(CustomsArea.timestamp >= start_datetime, CustomsArea.timestamp < end_datetime),
                and_(CustomsArea.timestamp >= start_datetime, CustomsArea.timestamp < end_datetime)
            )
        ).all()

        # Sort the customs area data based on timestamp
        customs_area_data = sorted(customs_area_data, key=lambda entry: entry.timestamp)

        # Query the WaitingArea table in the database for data within the specified range
        waiting_area_data = WaitingArea.query.filter(
            or_(
                and_(WaitingArea.timestamp >= start_datetime, WaitingArea.timestamp < end_datetime),
                and_(WaitingArea.timestamp >= start_datetime, WaitingArea.timestamp < end_datetime)
            )
        ).all()

        # Sort the waiting area data based on timestamp
        waiting_area_data = sorted(waiting_area_data, key=lambda entry: entry.timestamp)

        # Initialize variables to store statistics
        avg_occupancy_waiting = peak_occupancy_waiting = avg_wait_time_waiting = ""
        avg_occupancy_custom = peak_occupancy_custom = avg_passenger_turnaround_time_custom = avg_wait_time_custom = ""

        # Calculate statistics for waiting area if data is available
        if waiting_area_data:
            avg_occupancy_waiting = calculate_average_occupancy(waiting_area_data)
            peak_occupancy_waiting = calculate_peak_occupancy(waiting_area_data)

        # Calculate statistics for customs area if data is available
        if customs_area_data:
            avg_occupancy_custom = get_average_occupancy_custom(customs_area_data)
            peak_occupancy_custom = get_peak_occupancy_custom(customs_area_data)

        # Return the statistics as JSON response
        return jsonify({
            'avg_occupancy_waiting': avg_occupancy_waiting,
            'peak_occupancy_waiting': peak_occupancy_waiting,
            'avg_occupancy_custom': avg_occupancy_custom,
            'peak_occupancy_custom': peak_occupancy_custom,
            'avg_passenger_turnaround_time': avg_passenger_turnaround_time_custom,
            'avg_wait_time_custom': avg_wait_time_custom,
        })

    except Exception as e:
        # Handle any exceptions and return an error message
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/export_data_to_csv')
def export_data_to_csv():
    """
    Function to export the data to CSV format for further calculations
    """
    try:
        # Get start_date, end_date, and area from the query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        area = request.args.get('area')

        # Convert start_date and end_date to datetime objects
        start_datetime = datetime.strptime(start_date, '%m/%d/%Y')
        end_datetime = datetime.strptime(end_date, '%m/%d/%Y') + timedelta(days=1)

        # Filter data based on the area
        if area == 'waiting_area':
            # Query WaitingArea table for data within the specified range
            data = WaitingArea.query.filter(WaitingArea.timestamp.between(start_datetime, end_datetime)).all()
            # Define column names for CSV file
            column_names = ['ID', 'Total Seats', 'Taken Seats', 'Free Seats', 'Total People', 'Timestamp']
            # Create CSV data
            csv_data = [[getattr(d, column) for column in ['id', 'total_seats', 'taken_seats', 'free_seats', 'total_people', 'timestamp']] for d in data]
        elif area == 'customs_area':
            # Query CustomsArea table for data within the specified range
            data = CustomsArea.query.filter(CustomsArea.timestamp.between(start_datetime, end_datetime)).all()
            # Define column names for CSV file
            column_names = ['ID', 'Entrance Point', 'Before Passport Point', 'After Passport Point', 'Exit Point', 'Current People Count', 'Timestamp']
            # Create CSV data
            csv_data = [[getattr(d, column) for column in ['id', 'entrance_point', 'before_passport_point', 'after_passport_point', 'exit_point', 'current_people_count', 'timestamp']] for d in data]
        else:
            return jsonify({'error': 'Invalid area specified'}), 400

        # Create a string buffer to write CSV data
        buffer = io.StringIO()
        csv_writer = csv.writer(buffer)
        csv_writer.writerow(column_names)  # Write column names to CSV
        csv_writer.writerows(csv_data)     # Write data rows to CSV
        buffer.seek(0)

        # Send the CSV file as a download
        return send_file(
            io.BytesIO(buffer.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{area}_{start_date}_to_{end_date}.csv"
        )
    
    except Exception as e:
        # Handle any exceptions and return an error message
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/waiting_area_data')
def waiting_area_data():
    """
    Route for javascript to get Waiting Area data.
    """
    # Call function to get data for the Waiting Area
    data = get_waiting_area_data()
    return jsonify(data)

@app.route('/customs_area_data')
def customs_area_data():
    """
    Route for javascript to get Customs Area data.
    """
    # Call function to get data for the Customs Area
    data = get_customs_area_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=80, host="0.0.0.0")
