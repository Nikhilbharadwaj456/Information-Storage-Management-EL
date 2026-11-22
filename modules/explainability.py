from __future__ import annotations


def raid_explanation(base: dict, array_state: str, rebuild_hours: float,
                     failed_count: int, hot_spare_active: bool) -> dict:
    fault = base["fault_tolerance"]
    summary = (
        f"{base['level']} provides {base['usable_capacity_tb']:.2f} TB of usable capacity "
        f"from {base['raw_capacity_tb']:.2f} TB raw capacity."
    )
    reasons = [
        f"Usable capacity and efficiency come from the selected RAID layout.",
        f"The array is currently {array_state.lower()} with {failed_count} failed disk(s).",
    ]
    if rebuilding := hot_spare_active:
        reasons.append(f"A hot spare is active and the rebuild estimate is {rebuild_hours:.2f} hours.")
    elif rebuild_hours > 0:
        reasons.append(f"A rebuild of the failed disk(s) is estimated at {rebuild_hours:.2f} hours.")
    return {
        "summary": summary,
        "formula": "Usable capacity = raw capacity minus capacity used for redundancy; efficiency = usable capacity / raw capacity.",
        "contributing_factors": reasons,
        "assumptions": [
            "The result is a logical RAID simulation, not a controller or hardware benchmark.",
            f"The configuration's advertised fault tolerance is {fault}.",
        ],
    }


def disk_explanation(result: dict, arrival_iops: float) -> dict:
    utilization = result["utilization"] * 100
    level = "high utilization" if utilization >= 80 else "stable utilization"
    return {
        "summary": (
            f"The disk is operating at {utilization:.1f}% utilization, so this workload has "
            f"{level}. The estimated average response time is {result['response_time_ms']:.3f} ms."
        ),
        "formula": "Service time = seek + rotational latency + transfer time; utilization = arrival IOPS x service time (seconds); response time = service time / (1 - utilization).",
        "contributing_factors": [
            f"The service time is {result['service_time_ms']:.3f} ms.",
            f"The workload arrival rate is {arrival_iops:.1f} IOPS.",
            f"The disk can theoretically serve about {result['estimated_iops']:.1f} IOPS.",
            f"Little's Law estimates {result['requests_in_system']:.3f} requests in the system.",
        ],
        "assumptions": [
            "This uses a simplified single-server M/M/1 queue model.",
            "The response time becomes unstable as utilization approaches 100%.",
        ],
    }


def backup_explanation(strategies: list[dict], recommendation: str, rpo_hours: float,
                       rto_hours: float, interval_hours: float) -> dict:
    compliant = [
        row["Strategy"] for row in strategies
        if row["RPO compliant"] == "Yes" and row["RTO compliant"] == "Yes"
    ]
    return {
        "summary": recommendation,
        "formula": "Backup duration = data size / throughput; RPO is checked against backup interval; RTO is checked against estimated restore duration.",
        "contributing_factors": [
            f"The selected backup interval is {interval_hours:g} hours against a required RPO of {rpo_hours:g} hours.",
            f"Restore estimates are compared with a required RTO of {rto_hours:g} hours.",
            (
                f"{', '.join(compliant)} meet both objectives."
                if len(compliant) > 1
                else f"{compliant[0]} meets both objectives."
                if compliant
                else "No strategy meets both objectives."
            ),
        ],
        "assumptions": [
            "Storage uses fixed daily changed data and one initial full backup.",
            "Throughput is constant and restoration steps are simplified.",
        ],
    }


def replication_explanation(selected: dict, mode: str) -> dict:
    if mode == "Synchronous":
        summary = "Synchronous replication waits for remote acknowledgement, improving confirmation of copy completion while adding network delay."
    else:
        summary = "Asynchronous replication acknowledges locally first, giving faster write response but allowing a replication lag."
    return {
        "summary": summary,
        "formula": "Synchronous response = local write + network RTT; asynchronous response = local write; asynchronous lag = RTT + transfer-window estimate.",
        "contributing_factors": [
            f"Selected write response: {selected['response_ms']:.2f} ms.",
            f"Selected replication lag: {selected['lag_ms']:.2f} ms.",
            selected["data_loss"],
        ],
        "assumptions": [
            "Synchronous writes wait for remote acknowledgement.",
            "Asynchronous writes acknowledge locally without waiting.",
            "Network and storage processing behavior is intentionally simplified.",
        ],
    }


def risk_explanation(asset: str, threat: str, vulnerability: str, likelihood: int,
                     impact: int, score: int, category: str, mitigation: str) -> dict:
    return {
        "summary": (
            f"{asset} has a {category.lower()} risk score of {score}/25 for {threat} because "
            f"likelihood is {likelihood}/5 and impact is {impact}/5."
        ),
        "formula": "Risk score = likelihood (1-5) x impact (1-5); 1-5 Low, 6-10 Medium, 11-15 High, 16-25 Critical.",
        "contributing_factors": [
            f"The selected threat is {threat}.",
            f"The identified vulnerability is {vulnerability}.",
            f"Impact contributes {impact} points per unit of likelihood, producing {score} in total.",
        ],
        "assumptions": [
            "The qualitative scores come from expert/user judgement rather than measured incident frequency.",
            f"The suggested mitigation is: {mitigation}",
        ],
    }
