# StorageLab

Information Storage Management (CS374TFD) experiential-learning project, 7th semester CSE, RVCE. A web app that simulates RAID, disk performance, backup, replication, and storage risk with no storage hardware. Every feature must map to a syllabus unit so it can be defended in the viva.

| Module | Unit | Priority | Owner |
|---|---|---|---|
| RAID simulator (calculator + live array) | II | Mandatory | Person A |
| Disk performance analyzer | I | Mandatory | Person B |
| Backup strategy planner | IV | Mandatory | Person C (also integration, report) |
| Replication simulator | IV | Optional | |
| Storage risk assessment | V | Optional | |

Tell the module's owner before changing another person's module.

## Architecture

Request path: React page (`frontend/src/pages/`) → FastAPI router (`backend/app/routers/`) → calculation module (`modules/`).

- `modules/` holds every calculation. Each module also has a `show_*()` function for the Streamlit app (`app.py`) that imports Streamlit inside the function, so the calculation functions stay importable and testable without it.
- Routers are thin: validate with Pydantic (`backend/app/schemas.py`), call `modules/`, attach units, assumptions, and an `explanation` dict.
- Pages render results; they hold no formulas.
- `modules/raid_engine.py` is the live RAID array: it writes real disk files under `workspace/<array id>/` (gitignored), one file per disk plus `spare_N.bin` and `meta.json`. A failed disk is a deleted file. Rebuild progress streams as NDJSON.
- Saved experiments go to SQLite through SQLAlchemy (`backend/app/database.py`).

The Streamlit app must keep working: the course spec defines completion as "the application runs successfully using Streamlit". When a calculation's signature changes, update its `show_*()` caller too.

## Commands

Python lives in `.venv/` (system Python has no packages).

```bash
.venv/bin/python -m pytest -q                                   # all Python tests
.venv/bin/python -m uvicorn backend.app.main:app --port 8000    # API, no auto-reload: restart after backend edits
.venv/bin/python -m streamlit run app.py                         # Streamlit version
cd frontend && npm run dev -- --port 5173                        # React app
cd frontend && npm test && npm run build                         # Vitest, then tsc + production build
```

A change is done when pytest, `npm test`, and `npm run build` all pass and every Streamlit page still loads.

## Models (the source of truth for formulas)

Keep these exact; the viva checks them against the textbook. Sizes and times convert to consistent units before dividing.

RAID
- Usable capacity: RAID 0 = N×S, RAID 1 and 10 = N/2×S, RAID 5 = (N−1)×S, RAID 6 = (N−2)×S. Efficiency = usable / raw × 100.
- Minimum disks: RAID 5 ≥ 3, RAID 6 ≥ 4, RAID 1 and 10 even (RAID 10 ≥ 4). The live array limits RAID 1 to exactly two disks.
- Write penalty: 1, 2, 4, 6, 2 for RAID 0, 1, 5, 6, 10.
- States: Healthy, Degraded, Rebuilding, Failed. Rebuilding applies only to a Degraded array with a hot spare; a Failed array has lost data and cannot rebuild.
- Rebuild time = data to rebuild / rebuild throughput.
- RAID 5 parity P = XOR of the data blocks, rotating across disks. RAID 6 adds Q = Σ gⁱ·Dᵢ over GF(2⁸), g = 2, polynomial 0x11D.

Disk (single-server M/M/1)
- Rotational latency = 30000 / RPM ms; transfer time = block size / transfer rate; service time Ts = seek + rotation + transfer.
- IOPS = 1000 / Ts(ms); U = λ × Ts(s), valid only below 1; R = Ts / (1 − U); queue length = U² / (1 − U); Little's Law N = λ × R. The response curve knee is about 70% utilization.

Backup (one initial full backup, fixed daily change C, R retained points, data size D)
- Storage: full = R×D; incremental = D + (R−1)×C; differential = D + C×(1 + 2 + … + (R−1)), each differential capped at D.
- Duration = data transferred / throughput. RPO passes when backup interval ≤ RPO; RTO passes when restore time ≤ RTO.
- Recommend only among strategies that meet both RPO and RTO, and say explicitly when none does.

Replication
- Round trip = network latency + 2 × distance × 0.005 ms/km.
- Synchronous response = local write + round trip (RPO 0). Asynchronous response = local write; lag and RPO = round trip / 2 + transmit time / (1 − link utilization).
- Link utilization ≥ 1 is an error (the link is saturated).

Risk: score = likelihood × impact on 1–5 scales; 1–5 Low, 6–10 Medium, 11–15 High, 16–25 Critical.

## Presenting results

- Every number shows its unit.
- Results are educational estimates: label them as model outputs, never as hardware benchmarks.
- The explanation panels are rule-based text generated from the same formulas, not machine learning; describe them that way in the report and viva.

## Tests

Python tests sit beside their subject: `tests/` for `modules/`, `backend/tests/` for the API. For RAID, every change keeps these green:

- Write then read back returns identical bytes for every level.
- Failing up to the level's tolerance (every combination; every pair for RAID 6) and rebuilding gives a matching SHA-256.
- Failing beyond tolerance reports data loss and refuses rebuild.
- Each RAID 5 parity block equals the XOR of its row's data blocks.

Formula changes get a test against a hand-calculated value.

## Frontend gotchas

- `.results-column` uses `grid-template-columns: minmax(0, 1fr)`. Without it, wide tables and charts push the page sideways on phones.
- Recharts axis text is styled through `.recharts-cartesian-axis-tick-value`.
- Design tokens live at the top of `frontend/src/index.css`; the "Modern visual layer" block at the end overrides older rules and carries the dark-theme colours.
- Run the dev servers in the background and stop them when finished.

## Submission artifacts

`README.md` (setup and the demonstration scenario), `report/project_report.md` (16-section report), `STAGE10_VERIFICATION.md` (latest verification results), and `screenshots/`. After a change that alters the UI or a test count, update the affected artifact in the same change.
