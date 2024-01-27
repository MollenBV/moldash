# import keyboard
# import time

# class CustomsArea:
#     def __init__(self):
#         self.points = {
#             'Entrance': 1,
#             'Before passport': 2,
#             'After passport': 3,
#             'Exit': 4
#         }
#         self.point_counts = {point: 0 for point in self.points}

#     def move_to_point(self, point_name):
#         if point_name in self.points:
#             point = self.points[point_name]
#             self.point_counts[point_name] += 1
#             print(f"Moved to point {point_name:>20} ({point})     Count: {self.point_counts[point_name]:<40}")
#         else:
#             print(f"Invalid point {point_name}.")

# def main():
#     customs_area = CustomsArea()

#     while True:
#         try:
#             if keyboard.is_pressed('q'):
#                 customs_area.move_to_point('Entrance')
#                 time.sleep(0.2)
#             elif keyboard.is_pressed('w'):
#                 customs_area.move_to_point('Before passport')
#                 time.sleep(0.2)
#             elif keyboard.is_pressed('e'):
#                 customs_area.move_to_point('After passport')
#                 time.sleep(0.2)
#             elif keyboard.is_pressed('r'):
#                 customs_area.move_to_point('Exit')
#                 time.sleep(0.2)
#         except KeyboardInterrupt:
#             break

# if __name__ == "__main__":
#     main()
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
        'entrance_point': fake.random_int(min=0, max=200),
        'before_passport_point': fake.random_int(min=0, max=200),
        'after_passport_point': fake.random_int(min=0, max=200),
        'exit_point': fake.random_int(min=0, max=200),
        'current_people_count': fake.random_int(min=10, max=400),
        'timestamp': timestamp.isoformat(),
    }

def send_waiting_area_data():
    url = 'http://localhost:5000/waiting_area'
    data = generate_waiting_area_data()
    response = requests.post(url, json=data)
    print(f"Waiting Area Data Sent: {response.status_code}")

def send_customs_area_data():
    url = 'http://localhost:5000/customs_area'
    data = generate_customs_area_data()
    response = requests.post(url, json=data)
    print(f"Customs Area Data Sent: {response.status_code}")

if __name__ == '__main__':
    # Sending data to Flask server
    for x in range(75):
        send_waiting_area_data()
        send_customs_area_data()


