📊 Metering API
This is a lightweight metering API that logs and queries API usage per account. It supports individual usage event recording, time range querying, and rate limiting.

🚀 Hosted Version (Google Cloud Run)
A live version is available at:

🔗 https://measure-229201178350.europe-north1.run.app

🧑‍💻 Running Locally
✅ Requirements
Python 3.8+

PostgreSQL (or use SQLite for local testing)

pip or venv for managing Python dependencies

📦 Install Dependencies
bash
Copy
Edit
```pip install -r requirements.txt```
⚙️ Set Environment Variables
Before running locally, export the following:

bash
Copy
Edit
export FLASK_APP=main.py
You may also want to export the database connection string (optional, if not hardcoded):

bash
Copy
Edit the config.py
```
export DATABASE_URL=postgresql://youruser:yourpassword@localhost:5432/measure

```
▶️ Start the App by running


```flask run```

By default, it will be served at http://127.0.0.1:5000

📡 API Endpoints
POST /log-event
Record a usage event.

Curl command with Request Body (JSON):


```
curl -X POST http://127.0.0.1:5000/log-event \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "acct_123",
    "endpoint": "/api/v1/some-feature",
    "timestamp": "2025-04-09T16:00:00Z"
  }'

{"message":"Event logged"}
```
Rate Limit: 10 requests per second per account_id

GET /usage
Query usage data.

Query Params:

account_id (optional)

endpoint (optional)

start (required) – ISO 8601 format

end (required) – ISO 8601 format

Example:


```GET /usage?account_id=acct_123&start=2025-04-01T00:00:00Z&end=2025-04-09T23:59:59Z```

Rate Limit: 10 requests per second per account_id

Let me know if you’d like a section for testing (pytest), Dockerization, or deployment instructions.


Following are the major TODO to complete this project.

1. Move the secrets to a secret store and read from there.
2. Add monitoring and alerting to the api
3. If required add authentication to call the API.