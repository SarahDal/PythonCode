from flask import Flask, request
from mastodon import Mastodon  # Masto
import csv
from datetime import datetime, timedelta

# Store recent detections in memory (bird_name -> timestamp)
recent_detections = {}

app = Flask(__name__)

# Your Mastodon instance URL and access token
mastodon_url = 'https://url'
access_token = 'access token'

# Create a Mastodon instance
mastodon = Mastodon(
    access_token=access_token,
    api_base_url=mastodon_url
)

def get_bird_name(value):
    # Look up the bird name in birds.csv where value is in column A
    with open('birds.csv', mode='r', newline='') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if row[1] == value:  # Column A
                return row[0]  # Column B (Bird name)
    return value

def log_detection(confidence_score, bird_name, value):
    global recent_detections

    # Round timestamp to the nearest minute
    timestamp = datetime.now()
    rounded_timestamp = timestamp.replace(second=0, microsecond=0)

    # Create a unique key for deduplication
    detection_key = bird_name

    # Check if this detection has been logged recently (within the last X minutes)
    ten_minutes_ago = datetime.now() - timedelta(minutes=10)
    recent_detections = {k: v for k, v in recent_detections.items() if v > ten_minutes_ago}

    # Log detection to CSV (this happens regardless of whether it's a duplicate or not)
    date_str = timestamp.strftime("%y/%m/%d")
    time_str = timestamp.strftime("%H:%M")

    with open('detections_log.csv', mode='a', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow([confidence_score, bird_name, value, date_str, time_str])

    print(f"Logged detection: {bird_name} ({confidence_score:.2f}%) at {time_str}")

    # Skip posting to Mastodon if the bird was detected recently (within 5 minutes)
    if detection_key in recent_detections:
        print(f"Skipping Mastodon post: {bird_name} ({confidence_score:.2f}%) - Detected within last 5 minutes.")
        return  # Skip posting to Mastodon

    # Update recent detections dictionary and post to Mastodon
    recent_detections[detection_key] = rounded_timestamp

    try:
        status_update = f"I am {confidence_score:.2f}% certain I heard a {bird_name}"
        mastodon.status_post(status_update)
        print(f"Posted to Mastodon: {status_update}")
    except Exception as e:
        print(f"Mastodon post failed: {e}")

@app.route('/sensor-data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()  # Get JSON data
        # print("Received Data:", data)  # Print full received data

        if data and "detections" in data:
            for detection in data["detections"]:
                for tag in detection.get("tags", []):
                    value = tag["tag"].get("value", "Unknown")
                    confidence_score = tag.get("confidence_score", 0) * 100  # Convert to percentage
                    
                    # Get bird name from CSV
                    bird_name = get_bird_name(value)

                    # Log detection to CSV and handle posting to Mastodon
                    log_detection(confidence_score, bird_name, value)

        return "Received", 200  # Send a success response

    except Exception as e:
        print("Error:", str(e))
        return "Error processing request", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)