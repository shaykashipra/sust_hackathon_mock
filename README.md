# Customer Support Triage API

FastAPI service for classifying digital financial service customer complaints.

## What This Does

This API receives one customer complaint and returns a structured JSON triage result. It identifies the complaint type, severity, responsible department, short agent summary, review flag, and confidence score.

## What Is Used

- Python
- FastAPI
- Pydantic
- Uvicorn
- Pytest
- Rules-based keyword classification

No LLM, GPU, database, or secret key is required.

## How It Works

The `/sort-ticket` endpoint checks the customer message for keywords related to:

- Wrong transfers
- Failed payments
- Refund requests
- Phishing, scams, OTP, PIN, or password requests
- Other support issues

Then it maps the result to severity and department using the task rules. Critical phishing or fraud-risk messages are automatically marked for human review.

## Endpoints

- `GET /health`
- `POST /sort-ticket`

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Run the API:

```powershell
python run.py
```

Open:

- Health: `http://127.0.0.1:8000/health`
- Docs: `http://127.0.0.1:8000/docs`

## How To Check Response

1. Start the server with `python run.py`.
2. Open `http://127.0.0.1:8000/docs`.
3. Expand `POST /sort-ticket`.
4. Click `Try it out`.
5. Replace the request body with a sample ticket.
6. Click `Execute`.
7. Check the JSON under `Server response`.

## Environment Process

The service has no secrets. Runtime settings can be kept in `.env` and passed to deployment platforms as environment variables.

| Variable | Example | Purpose |
| --- | --- | --- |
| `APP_HOST` | `0.0.0.0` | Host binding for local or container runs |
| `APP_PORT` | `8000` | Port for the API |
| `APP_RELOAD` | `true` | Enable reload during local development |

## Sample Request

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/sort-ticket `
  -ContentType "application/json" `
  -Body '{"ticket_id":"T-001","channel":"app","locale":"en","message":"I sent 3000 to wrong number"}'
```

Expected response:

```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports: I sent 3000 to wrong number",
  "human_review_required": false,
  "confidence": 0.9
}
```

## Sample Responses

Wrong transfer:

```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports: I sent 3000 to wrong number",
  "human_review_required": false,
  "confidence": 0.9
}
```

Payment failed:

```json
{
  "ticket_id": "T-002",
  "case_type": "payment_failed",
  "severity": "high",
  "department": "payments_ops",
  "agent_summary": "Customer reports: Payment failed but balance deducted",
  "human_review_required": false,
  "confidence": 0.88
}
```

Phishing or scam:

```json
{
  "ticket_id": "T-003",
  "case_type": "phishing_or_social_engineering",
  "severity": "critical",
  "department": "fraud_risk",
  "agent_summary": "Customer reports suspicious contact involving credential-related fraud risk.",
  "human_review_required": true,
  "confidence": 0.95
}
```

## Deployment

Use this start command on Render, Railway, Fly, EC2, or similar platforms:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

A `Procfile` is included for platforms that detect it automatically.

## Docker Deployment

Build the Docker image:

```powershell
docker build -t customer-triage-api .
```

Run the container:

```powershell
docker run --env-file .env -p 8000:8000 customer-triage-api
```

Or run with Docker Compose:

```powershell
docker compose up --build
```

After the container starts, check:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## Free Submission Deployment

Recommended free option: Render Web Service. Docker is not required on your computer.

1. Push this project to a public GitHub repository.
2. Go to `https://dashboard.render.com`.
3. Click `New` then `Web Service`.
4. Connect your GitHub repository.
5. Select `Python` as the runtime or language.
6. Choose the `Free` instance type.
7. Use `pip install -r requirements.txt` as the build command.
8. Use `uvicorn app.main:app --host 0.0.0.0 --port $PORT` as the start command.
9. Deploy the service.
10. After deploy finishes, copy the public HTTPS URL.

This repository also includes `render.yaml`, so Render can detect the same free Python deployment settings automatically.

If Render tries Python `3.14` and fails while installing `pydantic-core`, keep `.python-version` in the repository. It pins the deploy runtime to Python `3.13.5`.

If Render runs `gunicorn your_application.wsgi`, the service start command is still using Render's default Python command. Change the Render service start command to:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

For the submission form:

- GitHub repository URL: your public GitHub repo link
- Live API base URL: your Render service URL, for example `https://your-service-name.onrender.com`
- Deployment platform: `Render`
- LLM used: `No`

Before submitting, test:

- `https://your-service-name.onrender.com/health`
- `https://your-service-name.onrender.com/docs`

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests
```

LLM used by service: No. This is a deterministic rules-based implementation.
