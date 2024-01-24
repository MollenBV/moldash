# import requests
# import json
# from faker import Faker
# from datetime import datetime, timedelta

# fake = Faker()

# def generate_waiting_area_data():
#     return {
#         'taken_seats': fake.random_int(min=0, max=50),
#         'free_seats': 0,  # Set to 0 initially
#         'total_people': 0,  # Set to 0 initially
#         'timestamp': datetime.utcnow().isoformat(),
#     }

# def generate_customs_area_data():
#     return {
#         'entrance_point': fake.random_int(min=0, max=20),
#         'before_passport_point': fake.random_int(min=0, max=20),
#         'after_passport_point': fake.random_int(min=0, max=20),
#         'exit_point': fake.random_int(min=0, max=20),
#         'current_people_count': 0,  # Set to 0 initially
#         'timestamp': datetime.utcnow().isoformat(),
#     }

# def send_waiting_area_data():
#     url = 'http://localhost:5000/waiting_area'
#     data = generate_waiting_area_data()
#     response = requests.post(url, json=data)
#     print(f"Waiting Area Data Sent: {response.status_code}")

# def send_customs_area_data():
#     url = 'http://localhost:5000/customs_area'
#     data = generate_customs_area_data()
#     response = requests.post(url, json=data)
#     print(f"Customs Area Data Sent: {response.status_code}")

# if __name__ == '__main__':
#     # Sending data to Flask server
#     send_waiting_area_data()
#     send_customs_area_data()

def estimate_people_in_room(taken_seats, total_seats=500, multiplier=1.5):
    # Calculate the percentage of taken seats
    percentage_taken = (taken_seats / total_seats) * 100

    # Assuming each person occupies one seat, estimate the number of people
    estimated_people = int((percentage_taken / 100) * total_seats)

    # Apply the multiplier to account for additional people beyond seated capacity
    estimated_people_with_multiplier = int(estimated_people * multiplier)

    return estimated_people_with_multiplier

# Example usage:
taken_seats = 900  # Replace with the actual number of taken seats
estimated_people = estimate_people_in_room(taken_seats)
print(f"Estimated number of people in the room: {estimated_people}")
