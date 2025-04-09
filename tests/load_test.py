import requests
import time
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor

# URL of the API you want to test
LOG_EVENT_API_URL = "https://measure-229201178350.europe-north1.run.app/log-event"  # Update with your API URL
USAGE_API_URL = "https://measure-229201178350.europe-north1.run.app/usage"  # Update with your API URL

# Duration of the load test (in seconds)
TEST_DURATION = 10 * 60  # 10 minutes

# Number of requests per second
REQUESTS_PER_SECOND = 20

def generate_log_event_payload(number):
    """
    Generates a log event payload with an incremented account_id, endpoint, and timestamp.
    The account_id and endpoint are dynamically generated based on the provided number.
    """
    # Increment the number for the account_id and endpoint
    account_id = f"test_acct_{number}"  # Create account_id using the incremented number
    endpoint = f"/api/v1/feature{number}"  # Create endpoint using the incremented number
    timestamp = datetime.now(pytz.UTC).isoformat()  # Current timestamp in UTC format

    return {
        "account_id": account_id,
        "endpoint": endpoint,
        "timestamp": timestamp
    }

# Generate payload for usage query
def generate_usage_payload():
    return {
        "account_id": "test_acct",
        "start": (datetime.now(pytz.UTC) - timedelta(days=1)).isoformat(),
        "end": datetime.now(pytz.UTC).isoformat()
    }

# Function to send a POST request to the log-event API
def send_log_event_request(number):
    payload = generate_log_event_payload(number)
    response = requests.post(LOG_EVENT_API_URL, json=payload)
    if response.status_code != 201:
        print(f"Log Event Request Failed: {response.status_code}")

# Function to send a GET request to the usage API
def send_usage_request():
    payload = generate_usage_payload()
    response = requests.get(USAGE_API_URL, params=payload)
    if response.status_code != 200:
        print(f"Usage Request Failed: {response.status_code}")

# Function to handle sending requests to both APIs concurrently
def send_requests():
    counter = 1  # Start from 1
    with ThreadPoolExecutor(max_workers=REQUESTS_PER_SECOND * 2) as executor:
        while time.time() < start_time + TEST_DURATION:
            # Send 20 requests to /log-event and 20 to /usage every second
            for _ in range(REQUESTS_PER_SECOND):
                executor.submit(send_log_event_request, counter)  # Submit log event request with counter
                executor.submit(send_usage_request)  # Submit usage request
                counter += 1  # Increment counter for the next log event
            time.sleep(1)

if __name__ == "__main__":
    start_time = time.time()
    print(f"Starting load test for {TEST_DURATION / 60} minutes...")
    send_requests()
    print("Load test completed.")
