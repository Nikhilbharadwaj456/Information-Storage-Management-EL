from __future__ import annotations

PROPAGATION_MS_PER_KM = 0.005


def replication_comparison(mode: str, local_write_ms: float, network_round_trip_ms: float,
                           bandwidth_mbps: float, write_frequency_iops: float,
                           distance_km: float = 0.0, write_size_kb: float = 8.0) -> dict:
    """Model write response and replication lag for synchronous or asynchronous replication."""
    if mode not in ("Synchronous", "Asynchronous"):
        raise ValueError("Replication mode must be Synchronous or Asynchronous.")
    if local_write_ms < 0 or network_round_trip_ms < 0 or distance_km < 0:
        raise ValueError("Write time, network latency, and distance cannot be negative.")
    if bandwidth_mbps <= 0 or write_frequency_iops < 0 or write_size_kb <= 0:
        raise ValueError("Bandwidth and write size must be positive and write frequency cannot be negative.")

    propagation_rtt_ms = 2 * distance_km * PROPAGATION_MS_PER_KM
    total_rtt_ms = network_round_trip_ms + propagation_rtt_ms
    write_bits = write_size_kb * 1024 * 8
    transmit_ms = write_bits / (bandwidth_mbps * 1_000_000) * 1000
    required_mbps = write_frequency_iops * write_bits / 1_000_000
    link_utilization = required_mbps / bandwidth_mbps
    if link_utilization >= 1:
        raise ValueError(
            f"The replication link is saturated: the workload needs {required_mbps:.1f} Mbps "
            f"but only {bandwidth_mbps:g} Mbps is available. Increase bandwidth or reduce writes."
        )

    if mode == "Synchronous":
        response_ms = local_write_ms + total_rtt_ms
        lag_ms = 0.0
        data_loss = "No acknowledged write is lost (RPO = 0); every write waits for the remote copy"
    else:
        response_ms = local_write_ms
        lag_ms = total_rtt_ms / 2 + transmit_ms / (1 - link_utilization)
        writes_at_risk = write_frequency_iops * lag_ms / 1000
        data_loss = (
            f"Up to {lag_ms:.2f} ms of recent writes (about {writes_at_risk:.1f} writes) "
            f"may be lost on a site failure; RPO is about {lag_ms:.2f} ms"
        )
    return {
        "mode": mode,
        "response_ms": response_ms,
        "lag_ms": lag_ms,
        "rpo_ms": lag_ms,
        "propagation_rtt_ms": propagation_rtt_ms,
        "total_rtt_ms": total_rtt_ms,
        "transmit_ms": transmit_ms,
        "link_utilization_percent": link_utilization * 100,
        "data_loss": data_loss,
    }


def show_replication() -> None:
    import pandas as pd
    import streamlit as st

    st.header("Replication Simulator")
    c1, c2 = st.columns(2)
    mode = c1.selectbox("Replication mode", ["Synchronous", "Asynchronous"])
    bandwidth = c2.number_input("Network bandwidth (Mbps)", min_value=0.1, value=1000.0)

    c3, c4, c5 = st.columns(3)
    latency = c3.number_input("Network round-trip latency (ms)", min_value=0.0, value=2.0)
    local_write = c4.number_input("Local write processing time (ms)", min_value=0.0, value=2.0)
    write_frequency = c5.number_input("Write frequency (IOPS)", min_value=0.0, value=500.0)
    c6, c7 = st.columns(2)
    distance = c6.number_input("Distance between sites (km)", min_value=0.0, value=100.0)
    write_size = c7.number_input("Write size (KB)", min_value=0.5, value=8.0)

    try:
        args = (local_write, latency, bandwidth, write_frequency, distance, write_size)
        result = replication_comparison(mode, *args)
        m1, m2 = st.columns(2)
        m1.metric("Write response time", f"{result['response_ms']:.2f} ms")
        m2.metric("Replication lag", f"{result['lag_ms']:.2f} ms")
        st.warning(result["data_loss"])

        comparison = pd.DataFrame([
            {
                "Mode": row["mode"],
                "Response time (ms)": row["response_ms"],
                "Replication lag (ms)": row["lag_ms"],
                "Data loss window": row["data_loss"],
            }
            for row in (replication_comparison(name, *args) for name in ("Synchronous", "Asynchronous"))
        ])
        st.subheader("Replication comparison")
        st.dataframe(comparison, width="stretch")
        st.caption(
            "This simplified model assumes synchronous writes wait for remote acknowledgement and "
            "asynchronous writes acknowledge locally without waiting."
        )
    except ValueError as exc:
        st.error(str(exc))
