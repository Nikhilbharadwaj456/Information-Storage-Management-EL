# StorageLab Project Report

## 1. Title Page

**StorageLab: RAID Simulator and Storage Performance Analyzer with Backup/Replication Strategy Planner**  
Subject: Information Storage Management (CS374TFD)

## 2. Abstract

StorageLab is a Streamlit application that demonstrates RAID behavior, disk performance equations, backup strategies, replication, and storage risk. It performs no physical disk operations and is intended as an educational software simulation.

## 3. Introduction

Enterprise storage systems require availability, reliability, performance, and data protection. StorageLab provides interactive calculations and visualizations that make these concepts measurable.

## 4. Problem Statement

Storage failures, recovery behavior, queueing, retention, and RPO/RTO trade-offs are difficult to study without enterprise infrastructure. This project provides a hardware-independent environment for experimentation.

## 5. Objectives

- Compare RAID capacity, efficiency, fault tolerance, and layout.
- Demonstrate disk failure and XOR recovery.
- Apply disk service-time and queueing formulas.
- Compare full, incremental, and differential backups.
- Evaluate RPO and RTO.
- Demonstrate replication and storage risk concepts.

## 6. Existing System and Limitations

Traditional teaching depends on diagrams or physical infrastructure. StorageLab replaces infrastructure with mathematical models, but cannot reproduce controller, firmware, workload, or device behavior.

## 7. Proposed System

The application separates calculation logic from Streamlit interfaces. It uses session state for temporary RAID failure state and provides pandas tables and Plotly charts.

## 8. System Architecture

The main app routes requests to independent RAID, disk performance, backup, replication, and risk modules. Shared utilities provide unit conversion.

## 9. Technologies Used

Python, Streamlit, Pandas, NumPy, Plotly, and Pytest.

## 10. Module-wise Implementation

### RAID Simulator

The RAID module calculates raw and usable capacity, efficiency, fault tolerance, layout, disk failure state, XOR parity, rebuild time, and hot-spare behavior.

### Disk Performance Analyzer

The disk module calculates rotational latency, transfer time, service time, IOPS, utilization, Little's Law, and M/M/1 response time.

### Backup Strategy Planner

The backup module compares retained storage, backup duration, restoration work, recovery steps, RPO compliance, and RTO compliance.

### Optional Replication and Risk Modules

Replication compares acknowledgement and lag assumptions. Risk assessment applies a 1-5 likelihood-impact model.

## 11. Mathematical Models and Algorithms

- Efficiency = usable capacity / raw capacity
- RAID 5 parity = A XOR B XOR C
- Rotation = 30000 / RPM ms
- Transfer = block MB / transfer rate, converted to ms
- Service time = seek + rotation + transfer
- Utilization = arrival rate x service time in seconds
- Response time = service time / (1 - utilization)
- Little's Law: L = lambda x W
- Backup storage uses one initial full backup and fixed daily change data

## 12. Results and Screenshots

Place application screenshots in `screenshots/` after running the demonstration.

## 13. Testing and Validation

Pytest covers RAID capacity, invalid configurations, failure states, XOR recovery, rebuild time, disk formulas, queue stability, backup storage, RPO/RTO fields, replication, and risk scores.

## 14. Limitations

The models are intentionally simplified and do not claim actual hardware measurements. RAID layouts are illustrative. Queueing behavior assumes a single-server M/M/1 model.

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
