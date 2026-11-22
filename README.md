# StorageLab

StorageLab is an Information Storage Management application for exploring RAID, disk performance, backup, replication, and storage risk using transparent mathematical models.

It includes a backward-compatible Streamlit prototype and a complete full-stack React + FastAPI implementation. Outputs are simplified simulations, not real hardware measurements.

## Features

- RAID 0, 1, 5, 6, and 10 capacity and efficiency
- Disk failure, hot-spare, rebuild, and RAID 5 XOR recovery
- Disk latency, IOPS, utilization, Little's Law, and M/M/1 response time
- Full, incremental, and differential backup comparisons
- RPO and RTO compliance evaluation
- Synchronous/asynchronous replication comparison
- Likelihood-impact storage risk assessment
- Saved SQLite scenarios, cloning, deletion, comparison data, and CSV export
- Explainable-AI panels that describe each result in plain language, including the
  factors, formulas, and assumptions behind it

## Local Development

Requirements:

- Python 3.10 or newer
- Node.js 22 or newer
- npm

### 1. Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

### 2. Start the FastAPI backend

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

API documentation:

- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health: http://127.0.0.1:8000/api/health

### 3. Start the React frontend

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open http://127.0.0.1:5173.

## How to use StorageLab

1. Open http://127.0.0.1:5173.
2. On the overview page, choose a module.
3. Open the expandable **How to use this module** section if you need guidance.
4. Enter parameters and select the module's calculate/analyze/compare button.
5. Read the numbers, charts, recommendation, and Explainable AI panel.
6. Select **Save scenario** to preserve a completed result.
7. Open **Saved Experiments** to refresh, clone, delete, compare, or export scenarios.

### Beginner-friendly workflow

- **RAID:** choose a RAID level, disk count, and disk capacity. Then optionally mark failed disks and enable a hot spare.
- **Disk:** enter disk timing and workload IOPS. Keep utilization below 100%; high utilization causes unstable queueing behavior.
- **Backup:** enter data size, daily change, retention, throughput, RPO, and RTO.
- **Replication:** compare synchronous remote acknowledgement with asynchronous local acknowledgement.
- **Risk:** select asset, threat, and vulnerability, then assign likelihood and impact scores from 1 to 5.
- **Saved Experiments:** select at least two scenarios before using Compare.

Use the question-mark button in the top bar to open the methodology and limitations page.

### 4. Optional Streamlit prototype

```powershell
python -m streamlit run app.py
```

The Streamlit application remains available for backward compatibility.

## Tests

```powershell
python -m pytest -q
cd frontend
npm test -- --run
npm run build
```

The Python tests verify API calculations, validation, scenario storage, comparison,
CSV export, and the explanation payload. The frontend tests verify React rendering
and key user interactions. A successful run should report all backend and frontend
tests as passing and finish with a production build.

## Docker

Docker is optional for local development. Install Docker Desktop first, then run:

```powershell
docker compose up --build
```

URLs:

- Application: http://localhost:5173
- API: http://localhost:8000
- API documentation: http://localhost:8000/docs

Stop the deployment:

```powershell
docker compose down
```

The SQLite database is stored in the `storagelab_data` Docker volume.

## Environment

Copy `.env.example` as a template.

- `STORAGELAB_DATABASE_URL`: SQLAlchemy database URL
- `VITE_API_BASE_URL`: React API base URL

SQLite is used locally and in Docker. SQLAlchemy models can also be configured for PostgreSQL through `STORAGELAB_DATABASE_URL`.

## Project Structure

```text
app.py                 Streamlit prototype
modules/               Existing calculation and UI modules
utils/                 Shared calculations and service adapter
backend/app/           FastAPI API, database, and schemas
backend/tests/         API and scenario tests
frontend/src/          React application
frontend/src/pages/    StorageLab pages
tests/                 Calculation unit tests
docker-compose.yml     Full-stack Docker deployment
Dockerfile             FastAPI container
report/                Project report area
screenshots/           Demonstration screenshots
```

## Assumptions

RAID layouts and reconstruction are logical demonstrations, not physical controller implementations. Disk performance uses a simplified M/M/1 queueing model. Backup storage assumes fixed daily change data and one initial full backup. Replication assumes simplified acknowledgement behavior. The application must not be used as a real hardware benchmark or production storage compliance guarantee.
