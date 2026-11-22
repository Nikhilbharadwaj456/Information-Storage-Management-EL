from __future__ import annotations


MIN_DISKS = {"RAID 0": 2, "RAID 1": 2, "RAID 5": 3, "RAID 6": 4, "RAID 10": 4}


def calculate_raid(raid_level: str, disk_count: int, disk_size_tb: float) -> dict:
    if raid_level not in MIN_DISKS:
        raise ValueError("Unsupported RAID level.")
    if disk_count < MIN_DISKS[raid_level]:
        raise ValueError(f"{raid_level} requires at least {MIN_DISKS[raid_level]} disks.")
    if raid_level in ("RAID 1", "RAID 10") and disk_count % 2:
        raise ValueError(f"{raid_level} requires an even number of disks.")
    if disk_size_tb <= 0:
        raise ValueError("Disk capacity must be greater than zero.")

    raw = disk_count * disk_size_tb
    if raid_level == "RAID 0":
        usable, fault = raw, 0
        read_level, write_level = "Very high; parallel reads across disks", "Very high; parallel writes across disks"
        characteristic = "Performance"
    elif raid_level == "RAID 1":
        usable, fault = disk_count / 2 * disk_size_tb, "Mirror-dependent"
        read_level, write_level = "High; mirror copies can share reads", "Moderate; every mirror copy is updated"
        characteristic = "Redundancy"
    elif raid_level == "RAID 5":
        usable, fault = (disk_count - 1) * disk_size_tb, 1
        read_level, write_level = "High; distributed data access", "Moderate; one parity update per write"
        characteristic = "Balanced"
    elif raid_level == "RAID 6":
        usable, fault = (disk_count - 2) * disk_size_tb, 2
        read_level, write_level = "High; distributed data access", "Lower; two parity updates per write"
        characteristic = "Higher redundancy"
    else:
        usable, fault = disk_count / 2 * disk_size_tb, "Mirror-dependent"
        read_level, write_level = "High; parallel striped reads", "High; mirrored pair writes"
        characteristic = "Performance + redundancy"

    return {
        "level": raid_level,
        "disk_count": disk_count,
        "disk_size_tb": disk_size_tb,
        "raw_capacity_tb": raw,
        "usable_capacity_tb": usable,
        "efficiency_percent": usable / raw * 100,
        "fault_tolerance": fault,
        "read_performance": read_level,
        "write_performance": write_level,
        "characteristic": characteristic,
    }


def xor_recover(a: int, b: int, c: int) -> tuple[int, int, int]:
    parity = a ^ b ^ c
    return parity, c, parity ^ a ^ b


def rebuild_time(data_tb: float, rebuild_throughput_mb_s: float) -> float:
    if rebuild_throughput_mb_s <= 0:
        raise ValueError("Rebuild throughput must be greater than zero.")
    data_mb = data_tb * 1024 * 1024
    return data_mb / rebuild_throughput_mb_s / 3600


def array_state(raid_level: str, disk_count: int, failed_disks: set[int]) -> str:
    if not failed_disks:
        return "Healthy"
    if raid_level == "RAID 0":
        return "Failed"
    if raid_level in ("RAID 5", "RAID 6"):
        tolerance = 1 if raid_level == "RAID 5" else 2
        return "Failed" if len(failed_disks) > tolerance else "Degraded"
    if raid_level == "RAID 1":
        for disk in range(0, disk_count, 2):
            if disk in failed_disks and disk + 1 in failed_disks:
                return "Failed"
        return "Degraded"
    for pair in range(0, disk_count, 2):
        if pair in failed_disks and pair + 1 in failed_disks:
            return "Failed"
    return "Degraded"


def build_layout(raid_level: str, disk_count: int, failed_disks: set[int] | None = None) -> pd.DataFrame:
    import pandas as pd

    failed = failed_disks or set()
    rows = []
    stripes = 3
    if raid_level == "RAID 5":
        for stripe in range(stripes):
            row = {"Stripe": stripe + 1}
            parity_disk = stripe % disk_count
            data_index = 1
            for disk in range(disk_count):
                if disk == parity_disk:
                    row[f"Disk {disk + 1}"] = f"P{stripe + 1}"
                else:
                    row[f"Disk {disk + 1}"] = f"D{stripe + 1}.{data_index}"
                    data_index += 1
                if disk in failed:
                    row[f"Disk {disk + 1}"] = "FAILED"
            rows.append(row)
    elif raid_level == "RAID 6":
        for stripe in range(stripes):
            row = {"Stripe": stripe + 1}
            parity_a = stripe % disk_count
            parity_b = (stripe + 1) % disk_count
            data_index = 1
            for disk in range(disk_count):
                if disk == parity_a:
                    row[f"Disk {disk + 1}"] = f"P{stripe + 1}"
                elif disk == parity_b:
                    row[f"Disk {disk + 1}"] = f"Q{stripe + 1}"
                else:
                    row[f"Disk {disk + 1}"] = f"D{stripe + 1}.{data_index}"
                    data_index += 1
                if disk in failed:
                    row[f"Disk {disk + 1}"] = "FAILED"
            rows.append(row)
    else:
        for stripe in range(stripes):
            row = {"Stripe": stripe + 1}
            for disk in range(disk_count):
                if raid_level == "RAID 1" or raid_level == "RAID 10":
                    row[f"Disk {disk + 1}"] = f"M{disk // 2 + 1}.{stripe + 1}"
                elif raid_level == "RAID 0":
                    row[f"Disk {disk + 1}"] = f"A{stripe + 1}.{disk + 1}"
                if disk in failed:
                    row[f"Disk {disk + 1}"] = "FAILED"
            rows.append(row)
    return pd.DataFrame(rows)


def _raid_comparison(disk_count: int, disk_size_tb: float) -> pd.DataFrame:
    import pandas as pd

    records = []
    for level in ("RAID 0", "RAID 1", "RAID 5", "RAID 6", "RAID 10"):
        try:
            result = calculate_raid(level, disk_count, disk_size_tb)
            records.append({
                "RAID": level,
                "Capacity (TB)": result["usable_capacity_tb"],
                "Efficiency (%)": result["efficiency_percent"],
                "Fault Tolerance": str(result["fault_tolerance"]),
                "Characteristic": result["characteristic"],
            })
        except ValueError:
            continue
    return pd.DataFrame(records)


def show_raid() -> None:
    import pandas as pd
    import plotly.express as px
    import streamlit as st

    st.header("RAID Simulator")

    col1, col2, col3 = st.columns(3)
    raid_level = col1.selectbox("RAID level", ["RAID 0", "RAID 1", "RAID 5", "RAID 6", "RAID 10"])
    disk_count = col2.number_input("Number of disks", min_value=2, max_value=32, value=4, step=1)
    disk_size = col3.number_input("Capacity per disk (TB)", min_value=0.1, value=1.0, step=0.1)

    read_speed = st.number_input("Optional disk read/write speed (MB/s)", min_value=1.0, value=200.0)
    hot_spare = st.checkbox("Enable one hot spare")

    try:
        result = calculate_raid(raid_level, int(disk_count), float(disk_size))
        state_key = f"raid_failed_{raid_level}_{disk_count}"
        if state_key not in st.session_state:
            st.session_state[state_key] = set()
        failed = st.session_state[state_key]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Raw capacity", f"{result['raw_capacity_tb']:.2f} TB")
        m2.metric("Usable capacity", f"{result['usable_capacity_tb']:.2f} TB")
        m3.metric("Efficiency", f"{result['efficiency_percent']:.1f}%")
        m4.metric("Fault tolerance", str(result["fault_tolerance"]))

        st.info(f"Read: {result['read_performance']}.  |  Write: {result['write_performance']}. "
                "These are relative estimates, not hardware benchmarks.")

        st.subheader("Disk layout")
        layout = build_layout(raid_level, int(disk_count), failed)
        st.dataframe(layout, use_container_width=True)

        failure_col, action_col = st.columns([2, 1])
        selectable = [disk for disk in range(int(disk_count)) if disk not in failed]
        disk_to_fail = failure_col.selectbox(
            "Disk to fail",
            selectable,
            format_func=lambda i: f"Disk {i + 1}",
            key=f"failed_choice_{state_key}",
        ) if selectable else None
        if action_col.button("Fail Disk", disabled=disk_to_fail is None):
            failed.add(disk_to_fail)
            st.session_state[state_key] = failed
            st.rerun()

        state = array_state(raid_level, int(disk_count), failed)
        if hot_spare and failed and state in ("Degraded", "Failed"):
            state = "Rebuilding"
        st.subheader("Failure and rebuild status")
        st.metric("System state", state)
        st.write(f"Failed disks: {len(failed)}")

        if hot_spare and failed:
            rebuild_hours = rebuild_time(float(disk_size), read_speed)
            st.success(f"Hot spare activated. Reconstruction estimated at {rebuild_hours:.2f} hours.")
        else:
            rebuild_hours = rebuild_time(float(disk_size), read_speed)
            st.caption(f"Rebuild estimate with no spare: {rebuild_hours:.2f} hours.")

        st.subheader("RAID comparison")
        comparison = _raid_comparison(int(disk_count), float(disk_size))
        st.dataframe(comparison, use_container_width=True)
        fig = px.bar(comparison, x="RAID", y="Efficiency (%)", color="Characteristic",
                     title="Storage Efficiency Comparison")
        st.plotly_chart(fig, use_container_width=True)

        if raid_level == "RAID 5":
            st.subheader("RAID 5 XOR parity recovery")
            a = st.text_input("Block A (binary)", "1010")
            b = st.text_input("Block B (binary)", "1100")
            c = st.text_input("Block C (binary)", "0110")
            try:
                a_value, b_value, c_value = int(a, 2), int(b, 2), int(c, 2)
                parity, _, reconstructed = xor_recover(a_value, b_value, c_value)
                st.write(f"Original blocks: A={a_value:04b}, B={b_value:04b}, C={c_value:04b}")
                st.write(f"Parity P = A XOR B XOR C = {parity:04b}")
                st.write(f"Recovered C = P XOR A XOR B = {reconstructed:04b}")
                st.success("Recovery verified." if reconstructed == c_value else "Recovery mismatch.")
            except ValueError:
                st.error("Enter valid binary values for A, B, and C.")

        if st.button("Reset simulation"):
            st.session_state[state_key] = set()
            st.rerun()
    except ValueError as exc:
        st.error(str(exc))
