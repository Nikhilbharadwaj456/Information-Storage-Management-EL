# StorageLab Project Report

## 1. Title Page

**StorageLab: RAID Simulator and Storage Performance Analyzer with Backup/Replication Strategy Planner**  
Subject: Information Storage Management (CS374TFD)

## 2. Abstract

StorageLab is a web application (React frontend, FastAPI backend, Python calculation modules) that demonstrates RAID behavior, disk performance equations, backup strategies, replication, and storage risk. Its RAID module includes a block-level simulator that stripes a real file across disk files with XOR and Reed-Solomon parity, survives disk failures, rebuilds onto a hot spare, and proves recovery with SHA-256. It uses no physical disks or storage hardware and is intended as an educational software simulation. A Streamlit version of the same modules is also included.

## 3. Introduction

Enterprise storage systems require availability, reliability, performance, and data protection. StorageLab provides interactive calculations and visualizations that make these concepts measurable.

## 4. Problem Statement

Storage failures, recovery behavior, queueing, retention, and RPO/RTO trade-offs are difficult to study without enterprise infrastructure. This project provides a hardware-independent environment for experimentation.

## 5. Objectives

- Compare RAID capacity, efficiency, fault tolerance, write penalty, and layout.
- Demonstrate disk failure, XOR recovery, and hot-spare rebuild on real data, verified with SHA-256.
- Apply disk service-time and queueing formulas.
- Compare full, incremental, and differential backups.
- Evaluate RPO and RTO.
- Demonstrate replication and storage risk concepts.

## 6. Existing System and Limitations

Traditional teaching depends on diagrams or physical infrastructure. StorageLab replaces infrastructure with mathematical models, but cannot reproduce controller, firmware, workload, or device behavior.

## 7. Proposed System

All calculations live in Python modules under `modules/`. A FastAPI backend exposes them as REST endpoints, and a React frontend provides the interactive pages, tables, and charts. Saved experiments are stored in SQLite. The live RAID array stores each simulated disk as a file under `workspace/`, so failures and rebuilds act on real bytes. The original Streamlit interface (`app.py`) reuses the same modules.

## 8. System Architecture

Browser (React pages) → REST API (FastAPI routers in `backend/app/routers/`) → calculation modules (`modules/raid.py`, `raid_engine.py`, `disk_performance.py`, `backup.py`, `replication.py`, `risk_assessment.py`) → results with explanations. Scenarios are persisted through SQLAlchemy to SQLite. The live RAID engine reads and writes disk files in `workspace/<array id>/`, one file per disk plus hot-spare files and a metadata file. Rebuild progress is streamed to the browser as newline-delimited JSON.

## 9. Technologies Used

Python, FastAPI, Pydantic, SQLAlchemy (SQLite), NumPy, Pandas, hashlib (SHA-256), Pytest; React, TypeScript, Vite, Recharts, Vitest; Streamlit and Plotly for the alternative interface; Docker Compose (optional).

## 10. Module-wise Implementation

### RAID Simulator

The capacity calculator computes raw and usable capacity, efficiency, fault tolerance, write penalty, layout, disk failure state (Healthy, Degraded, Rebuilding, Failed), whether data is still accessible, remaining fault tolerance, rebuild time, and hot-spare behavior, with a comparison table and chart across all levels. An interactive XOR demonstration lets the user mark any block as missing and verifies the reconstructed value.

The live array (`modules/raid_engine.py`) splits an uploaded file into stripe units and writes them to one file per disk. RAID 0 stripes, RAID 1 mirrors two disks, RAID 10 stripes across mirrored pairs, RAID 5 stores XOR parity that rotates across disks, and RAID 6 adds a Reed-Solomon Q parity over GF(2^8). Failing a disk deletes its file. Reads reconstruct missing blocks on the fly, a hot spare can be rebuilt row by row with a live progress bar, and SHA-256 of the reassembled file is compared with the original. Failing more disks than the level tolerates is detected and reported as data loss.

### Disk Performance Analyzer

The disk module calculates rotational latency, transfer time, service time, IOPS, utilization, Little's Law, average queue length, and M/M/1 response time. Results update as inputs change, and the current workload is marked on the response-time curve.

### Backup Strategy Planner

The backup module compares retained storage, backup duration, restoration time, data restored, recovery steps, RPO compliance, and RTO compliance, and recommends a strategy that meets both objectives.

### Optional Replication and Risk Modules

Replication compares synchronous and asynchronous modes using distance, network latency, bandwidth, write size, and write rate, reporting write response time, replication lag, link utilization, and RPO. Risk assessment applies a 1-5 likelihood-impact model to an asset, threat, and vulnerability.

## 11. Mathematical Models and Algorithms

- Efficiency = usable capacity / raw capacity x 100
- Write penalty (back-end I/Os per write): RAID 0 = 1, RAID 1 and 10 = 2, RAID 5 = 4, RAID 6 = 6
- Rebuild time = data to rebuild / rebuild throughput
- RAID 5 parity = A XOR B XOR C; a lost block = P XOR the surviving blocks
- RAID 6: P = XOR of the data blocks, Q = sum of g^i x D_i over GF(2^8) with g = 2 and polynomial x^8 + x^4 + x^3 + x^2 + 1. Two lost data blocks x and y are solved from Dx = (Qxy + g^y x Pxy) / (g^x + g^y) and Dy = Pxy + Dx
- Recovery is verified with SHA-256 of the reassembled file
- Rotation = 30000 / RPM ms
- Transfer = block MB / transfer rate, converted to ms
- Service time = seek + rotation + transfer
- Utilization = arrival rate x service time in seconds
- Response time = service time / (1 - utilization)
- Little's Law: L = lambda x W
- Average queue length = U^2 / (1 - U)
- Backup storage uses one initial full backup and fixed daily change data
- Backup or restore duration = data transferred / throughput
- Replication round trip = network latency + 2 x distance x 5 microseconds per km
- Synchronous response = local write + round trip; asynchronous response = local write
- Asynchronous lag (and RPO) = round trip / 2 + transmit time / (1 - link utilization), where transmit time = write size / bandwidth
- Risk score = likelihood x impact on 1-5 scales

## 12. Results and Screenshots

Screenshots of every page are in `screenshots/`: home, RAID calculator, RAID live array (light and dark theme), disk performance, backup, replication, risk, saved experiments, methodology, and a phone-width RAID page. The demonstration scenario is described in the README.

## 13. Testing and Validation

Pytest covers RAID capacity, invalid configurations, failure states, write penalty, XOR recovery, rebuild time, disk formulas, queue length, queue stability, backup storage, RPO/RTO fields, replication distance and lag units, link saturation, risk scores, and the API. The live RAID engine tests write and read back a file at every level, fail every tolerated combination of disks (for RAID 6, every pair), rebuild onto hot spares, and require a matching SHA-256; they also check that failures beyond tolerance are reported as data loss and that each RAID 5 parity block equals the XOR of its data blocks. Vitest covers the React pages. All 62 Python tests and 11 frontend tests pass.

## 14. Limitations

The models are intentionally simplified and do not claim actual hardware measurements. The capacity calculator's layout grid is illustrative; the live array stores real bytes in ordinary files rather than on block devices, limits files to 5 MB and arrays to 8 disks, and slows rebuild progress so it is visible. Queueing behavior assumes a single-server M/M/1 model. Replication assumes one transfer per write and a constant propagation speed.

## 15. Conclusion

StorageLab demonstrates the mandatory ISM concepts in an interactive, validated, and hardware-independent application.

## 16. Explainable AI Integration

StorageLab now provides transparent, rule-based explainability for every major
module. Each result identifies the plain-language reason for the output, the
calculation or formula used, the contributing factors, and the assumptions or
limitations that apply. This is explainable decision support rather than a
black-box machine-learning model: the system exposes the same deterministic rules
and equations used to produce the result.

## 17. References

- Course reference specification for CS374TFD
- Python, Streamlit, Pandas, NumPy, Plotly, and Pytest documentation
