

import random
import requests
import json
from faker import Faker
from datetime import datetime, timedelta

import random

def generate_waiting_area_data():
    return {
        'taken_seats': random.randint(0, 500),
        'Sensor': 'Pressuresensor' + str(random.randint(0, 500)),
        'status': random.choice(["Aan", "Uit"])
    }


def generate_customs_area_data():
    return {
        'entrance_point': 1,
        'before_passport_point': 0,
        'after_passport_point': 0,
        'exit_point': 0,
        'current_people_count': 0,
    }

def send_waiting_area_data():
    url = 'http://localhost:80/waiting_area'
    data = generate_waiting_area_data()
    response = requests.post(url, json=data)
    print(f"Waiting Area Data Sent: {response.status_code}")

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
    send_waiting_area_data()






# from datetime import datetime, timedelta, timezone

# amsterdam_timezone = timezone(timedelta(hours=1))
# current_time = datetime.now(amsterdam_timezone)
# print(current_time.strftime('%Y-%m-%d %H:%M:%S'))