# Insurance Eligibility Verification API

Pre-visit insurance verification backend for independent specialty practices.

Every day the system ingests a practice's appointment schedule, runs each patient through the pVerify eligibility API, flags coverage problems 48-72 hours before the visit, and delivers a prioritized action queue to the billing coordinator — so staff can fix problems before patients walk in the door.

---

## Live Demo

Once deployed, the full interactive API is at:

```
https://<your-railway-url>/docs
```

### Demo walkthrough (3 steps)

**1. Upload today's appointments**

`POST /appointments/upload` — upload `sample_data/appointments.csv`

**2. Run eligibility verification**

`POST /jobs/run-verification` — checks every patient against pVerify, applies the rules engine

**3. View the action queue**

`GET /reports/action-queue` — prioritized list of coverage problems for the billing coordinator

`GET /reports/weekly-roi` — flags raised, resolved, estimated dollars protected

---

## What gets flagged

| Priority | Flag | Example |
|----------|------|---------|
| CRITICAL | Inactive coverage | Patient's Aetna plan terminated |
| CRITICAL | Patient not found | Member ID not in payer system |
| HIGH | Prior auth required | UHC requires auth for MRI |
| HIGH | High deductible remaining | $2,550 left on $3,000 deductible |
| MEDIUM | Out-of-network | Provider not in Cigna network |
| MEDIUM | Medium deductible remaining | $600 left on deductible |

---

## Stack

- **Python 3.11 + FastAPI** — async REST API
- **PostgreSQL** — appointments, verification results, action queue, audit log
- **APScheduler** — 6am daily run + 7am re-check, automated
- **pVerify** — eligibility API (mock mode on, live mode ready)
- **HIPAA-aware** — no PHI in logs, audit trail on every action, patient refs by internal ID only

---

## Deploy to Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Add a **PostgreSQL** plugin to the project
4. Set these environment variables in Railway:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | *(auto-set by Railway PostgreSQL plugin)* |
| `PVERIFY_MOCK_MODE` | `true` |
| `SECRET_KEY` | *(generate a random string)* |
| `API_KEY` | *(generate a random string)* |

5. Deploy — Railway builds the Dockerfile and gives you a public URL.

---

## Run locally

```bash
docker compose up
```

API at `http://localhost:8000/docs`

---

## Switching to live pVerify

Set in Railway environment variables:

```
PVERIFY_MOCK_MODE=false
PVERIFY_CLIENT_ID=your_client_id
PVERIFY_CLIENT_SECRET=your_client_secret
```

No code changes required.
