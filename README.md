# StorageLab

StorageLab is an Information Storage Management application for exploring RAID, disk performance, backup, replication, and storage risk using transparent mathematical models.

It includes a backward-compatible Streamlit prototype and a complete full-stack React + FastAPI implementation. Outputs are simplified simulations, not real hardware measurements.

## Features

- RAID 0, 1, 5, 6, and 10 capacity, efficiency, fault tolerance, write penalty, and a comparison table and chart
- Disk failure, hot-spare rebuild estimate, and an interactive RAID 5 XOR recovery demonstration
- Live RAID array: a real file is striped into blocks across disk files with XOR (RAID 5) or XOR + Reed-Solomon (RAID 6) parity; disks can be failed, read in degraded mode, rebuilt onto a hot spare, and verified with SHA-256
- Disk latency, IOPS, utilization, Little's Law, queue length, and M/M/1 response time with a live response-time curve
- Full, incremental, and differential backup comparisons
- RPO and RTO compliance evaluation
- Synchronous/asynchronous replication comparison with distance-based delay, link utilization, and RPO
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

- **RAID (Capacity calculator tab):** choose a RAID level, disk count, and disk capacity. Then optionally mark failed disks and enable a hot spare.
- **RAID (Live array tab):** upload a file or use the sample file, select Fail on a disk column, then Rebuild. The banner shows SHA-256 MATCH, MISMATCH, or DATA LOSS after every step.
- **Disk:** enter disk timing and workload IOPS. Results update as you type. Keep utilization below 100%; high utilization causes unstable queueing behavior.
- **Backup:** enter data size, daily change, retention, throughput, RPO, and RTO.
- **Replication:** enter the distance between sites, network latency, bandwidth, write size, and write rate, then compare synchronous and asynchronous replication.
- **Risk:** select asset, threat, and vulnerability, then assign likelihood and impact scores from 1 to 5.
- **Saved Experiments:** select at least two scenarios before using Compare.

Use the question-mark button in the top bar to open the methodology and limitations page.

### 4. Optional Streamlit prototype

```powershell
python -m streamlit run app.py
```

The Streamlit application remains available for backward compatibility.

## Demonstration scenario

1. RAID Simulator, Live array tab: choose RAID 5, 4 disks, 4 KB stripe unit, 1 hot spare, then select Use sample file (or upload a file).
2. Show the block and parity layout: parity (P) moves to a different disk in each stripe row.
3. Select Fail on Disk 2. The array is Degraded and the banner still shows SHA-256 MATCH, because the missing blocks are rebuilt from parity on every read.
4. Select Rebuild on Disk 2. The progress bar fills, the hot spare becomes Disk 2, the array returns to Healthy, and the SHA-256 still matches.
5. Fail two disks on RAID 5: the banner shows DATA LOSS and rebuild is refused. Discard the array, repeat with RAID 6 and 5 disks: two failures still give SHA-256 MATCH.
6. Capacity calculator tab: show the RAID comparison table and efficiency chart, then the XOR demonstration with a block marked as missing.
7. Disk Performance: raise the arrival rate and watch the operating point move up the response-time curve past the 70% knee.
8. Backup Planner: set RPO to 1 hour with daily backups to show an RPO failure, then switch to hourly backups and show the recommendation.

## Tests

```powershell
python -m pytest -q
cd frontend
npm test -- --run
npm run build
```

The Python tests verify the calculations, validation, the live RAID engine (write and
read back for every level, rebuild after every tolerated failure combination with a
matching SHA-256, detection of data loss beyond tolerance, and XOR parity correctness),
scenario storage, comparison, CSV export, and the explanation payload. The frontend tests verify React rendering
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
modules/               Calculation modules (raid_engine.py is the live block-level RAID engine)
backend/app/           FastAPI API, database, and schemas
backend/tests/         API and scenario tests
frontend/src/          React application
frontend/src/pages/    StorageLab pages
tests/                 Calculation unit tests
docker-compose.yml     Full-stack Docker deployment
Dockerfile             FastAPI container
report/                Project report
screenshots/           Demonstration screenshots
workspace/             Disk files of live RAID arrays (created at runtime, not committed)
```

## Assumptions

The RAID capacity calculator and its layout grid are logical demonstrations. The live RAID array stores and reconstructs real bytes in ordinary files, but it is not a physical controller implementation; its rebuild progress is deliberately slowed so it is visible. Disk performance uses a simplified M/M/1 queueing model. Backup storage assumes fixed daily change data and one initial full backup. Replication assumes simplified acknowledgement behavior. The application must not be used as a real hardware benchmark or production storage compliance guarantee.
