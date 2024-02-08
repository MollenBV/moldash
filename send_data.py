import random
import requests
import json
from faker import Faker
from datetime import datetime, timedelta

import random


def generate_waiting_area_data():
    return {
        'Sensor': 'Pressuresensor' + str(random.randint(0, 10)),
        'Status': random.choice(["AAN", "UIT"])
    }


def generate_customs_area_data():
    return {
        'entrance_point': 1,
        'before_passport_point': 0,
        'after_passport_point': 0,
        'exit_point': 0,
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


if __name__ == '__main__':

    for x in range(75):
        send_waiting_area_data()
        send_customs_area_data()
