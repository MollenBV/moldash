


import requests
import json
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

def generate_waiting_area_data():
    # Generate a timestamp within the last 5 days
    timestamp = datetime.utcnow() - timedelta(days=fake.random_int(min=0, max=10))
    
    return {
        'taken_seats': fake.random_int(min=0, max=500),
        'timestamp': timestamp.isoformat(),
    }

def generate_customs_area_data():
    # Generate a timestamp within the last 5 days
    timestamp = datetime.utcnow() - timedelta(days=fake.random_int(min=0, max=10))

    return {
        'entrance_point': 1,
        'before_passport_point': 0,
        'after_passport_point': 0,
        'exit_point': 0,
        'current_people_count': 0,
    }

# def send_waiting_area_data():
#     url = 'http://localhost:5000/waiting_area'
#     data = generate_waiting_area_data()
#     response = requests.post(url, json=data)
#     print(f"Waiting Area Data Sent: {response.status_code}")

def send_customs_area_data():
    url = 'http://localhost:80/customs_area'
    data = generate_customs_area_data()
    response = requests.post(url, json=data)
    print(f"Customs Area Data Sent: {response.status_code}")

# if __name__ == '__main__':
#     # Sending data to Flask server
#     for x in range(75):
#         send_waiting_area_data()
#         send_customs_area_data()


for x in range(10):
    send_customs_area_data()