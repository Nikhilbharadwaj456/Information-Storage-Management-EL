from __future__ import annotations

def calculate_disk(rpm: float, seek_ms: float, transfer_rate_mb_s: float,
                   block_kb: float, arrival_iops: float) -> dict:
    if rpm <= 0:
        raise ValueError("RPM must be greater than zero.")
    if seek_ms < 0 or transfer_rate_mb_s <= 0 or block_kb <= 0:
        raise ValueError("Seek, transfer rate, and block size must be valid.")
    if arrival_iops < 0:
        raise ValueError("Request arrival rate cannot be negative.")

    rotational_latency_ms = 30000.0 / rpm
    transfer_time_ms = (block_kb / 1024.0) / transfer_rate_mb_s * 1000.0
    service_time_ms = seek_ms + rotational_latency_ms + transfer_time_ms
    estimated_iops = 1000.0 / service_time_ms
    utilization = arrival_iops * (service_time_ms / 1000.0)
    if utilization >= 1.0:
        raise ValueError(
            f"Unstable utilization: {utilization * 100:.1f}%. Arrival rate must be below "
            f"{estimated_iops:.1f} IOPS."
        )

    response_time_ms = service_time_ms / (1.0 - utilization)
    requests_in_system = arrival_iops * (response_time_ms / 1000.0)
    return {
        "rotational_latency_ms": rotational_latency_ms,
        "transfer_time_ms": transfer_time_ms,
        "service_time_ms": service_time_ms,
        "estimated_iops": estimated_iops,
        "utilization": utilization,
        "response_time_ms": response_time_ms,
        "requests_in_system": requests_in_system,
    }


def response_time_curve(service_time_ms: float) -> pd.DataFrame:
    import numpy as np
    import pandas as pd

    utilizations = np.linspace(0.05, 0.95, 91)
    response_ms = service_time_ms / (1.0 - utilizations)
    return pd.DataFrame({
        "Utilization (%)": utilizations * 100,
        "Average response time (ms)": response_ms,
    })


def show_disk() -> None:
    import pandas as pd
    import plotly.graph_objects as go
    import streamlit as st

    st.header("Disk Performance Analyzer")
    c1, c2, c3 = st.columns(3)
    rpm = c1.number_input("Disk RPM", min_value=1, max_value=30000, value=7200, step=100)
    seek_ms = c2.number_input("Average seek time (ms)", min_value=0.0, value=4.0, step=0.1)
    transfer_rate = c3.number_input("Transfer rate (MB/s)", min_value=0.1, value=150.0, step=10.0)

    c4, c5 = st.columns(2)
    block_kb = c4.number_input("Block size (KB)", min_value=0.1, value=4.0, step=1.0)
    arrival_iops = c5.number_input("Request arrival rate (IOPS)", min_value=0.0, value=100.0, step=10.0)

    try:
        result = calculate_disk(rpm, seek_ms, transfer_rate, block_kb, arrival_iops)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Rotational latency", f"{result['rotational_latency_ms']:.3f} ms")
        m2.metric("Transfer time", f"{result['transfer_time_ms']:.3f} ms")
        m3.metric("Service time", f"{result['service_time_ms']:.3f} ms")
        m4.metric("Estimated capacity", f"{result['estimated_iops']:.1f} IOPS")

        m5, m6, m7 = st.columns(3)
        m5.metric("Utilization", f"{result['utilization'] * 100:.1f}%")
        m6.metric("Average response time", f"{result['response_time_ms']:.3f} ms")
        m7.metric("Requests in system", f"{result['requests_in_system']:.3f}")

        st.caption("Little's Law: L = lambda x W")
        curve = response_time_curve(result["service_time_ms"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=curve["Utilization (%)"],
            y=curve["Average response time (ms)"],
            mode="lines",
            name="M/M/1 response time",
        ))
        fig.add_vline(
            x=result["utilization"] * 100,
            line_dash="dash",
            annotation_text="Current utilization",
        )
        fig.update_layout(
            xaxis_title="Utilization (%)",
            yaxis_title="Average response time (ms)",
            title="Response Time vs Utilization",
            yaxis={"rangemode": "tozero"},
        )
        st.plotly_chart(fig, use_container_width=True)

        if result["utilization"] >= 0.8:
            st.warning("The disk is operating at high utilization; queueing delay will increase sharply.")
        else:
            st.success("The disk is operating within the stable single-server queueing model.")
    except ValueError as exc:
        st.error(str(exc))
