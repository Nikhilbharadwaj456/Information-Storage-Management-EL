from __future__ import annotations

def replication_comparison(mode: str, local_write_ms: float, network_round_trip_ms: float,
                           bandwidth_mbps: float, write_frequency_iops: float) -> dict:
    if mode not in ("Synchronous", "Asynchronous"):
        raise ValueError("Replication mode must be Synchronous or Asynchronous.")
    if local_write_ms < 0 or network_round_trip_ms < 0:
        raise ValueError("Write time and network latency cannot be negative.")
    if bandwidth_mbps <= 0 or write_frequency_iops < 0:
        raise ValueError("Bandwidth must be positive and write frequency cannot be negative.")

    transfer_window_seconds = write_frequency_iops / bandwidth_mbps
    if mode == "Synchronous":
        response_ms = local_write_ms + network_round_trip_ms
        lag_ms = 0.0
        data_loss = "Near zero for acknowledged writes; network or site loss can affect availability"
    else:
        response_ms = local_write_ms
        lag_ms = network_round_trip_ms + transfer_window_seconds * 1000.0
        data_loss = f"Potentially up to {lag_ms:.2f} ms of replication lag"
    return {
        "mode": mode,
        "response_ms": response_ms,
        "lag_ms": lag_ms,
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
    latency = c3.number_input("Network round-trip latency (ms)", min_value=0.0, value=20.0)
    local_write = c4.number_input("Local write processing time (ms)", min_value=0.0, value=2.0)
    write_frequency = c5.number_input("Write frequency (IOPS)", min_value=0.0, value=500.0)

    try:
        result = replication_comparison(mode, local_write, latency, bandwidth, write_frequency)
        m1, m2 = st.columns(2)
        m1.metric("Write response time", f"{result['response_ms']:.2f} ms")
        m2.metric("Replication lag", f"{result['lag_ms']:.2f} ms")
        st.warning(result["data_loss"])

        comparison = pd.DataFrame([
            {
                "Mode": "Synchronous",
                "Response time (ms)": local_write + latency,
                "Replication lag (ms)": 0.0,
                "Data loss window": "Near zero after acknowledgement",
            },
            {
                "Mode": "Asynchronous",
                "Response time (ms)": local_write,
                "Replication lag (ms)": latency + (write_frequency / bandwidth * 1000.0),
                "Data loss window": "Changes not yet copied remotely",
            },
        ])
        st.subheader("Replication comparison")
        st.dataframe(comparison, use_container_width=True)
        st.caption(
            "This simplified model assumes synchronous writes wait for remote acknowledgement and "
            "asynchronous writes acknowledge locally without waiting."
        )
    except ValueError as exc:
        st.error(str(exc))
