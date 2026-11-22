from __future__ import annotations

def backup_comparison(data_size_gb: float, change_percent: float, retention_days: int,
                     throughput_mb_s: float, rpo_hours: float, rto_hours: float,
                     backup_interval_hours: float) -> pd.DataFrame:
    import pandas as pd

    if data_size_gb <= 0 or throughput_mb_s <= 0:
        raise ValueError("Data size and backup throughput must be greater than zero.")
    if change_percent < 0 or change_percent > 100:
        raise ValueError("Daily data change percentage must be between 0 and 100.")
    if retention_days < 1:
        raise ValueError("Retention period must include at least one recovery point.")
    if rpo_hours <= 0 or rto_hours <= 0 or backup_interval_hours <= 0:
        raise ValueError("RPO, RTO, and backup interval must be greater than zero.")

    changed_gb = data_size_gb * change_percent / 100.0
    full_storage = retention_days * data_size_gb
    incremental_storage = data_size_gb + (retention_days - 1) * changed_gb

    differential_daily = [
        min(changed_gb * day, data_size_gb)
        for day in range(1, retention_days)
    ]
    differential_storage = data_size_gb + sum(differential_daily)

    full_backup_gb = data_size_gb
    incremental_backup_gb = changed_gb
    differential_backup_gb = min(changed_gb * (retention_days - 1), data_size_gb)

    def duration_hours(data_gb: float) -> float:
        return data_gb * 1024.0 / throughput_mb_s / 3600.0

    full_restore_gb = data_size_gb
    incremental_restore_gb = data_size_gb + changed_gb * max(retention_days - 1, 0)
    differential_restore_gb = data_size_gb + differential_backup_gb

    full_steps = 1
    incremental_steps = 1 + max(retention_days - 1, 0)
    differential_steps = 2

    records = []
    for name, storage, backup_gb, restore_gb, steps in (
        ("Full", full_storage, full_backup_gb, full_restore_gb, full_steps),
        ("Incremental", incremental_storage, incremental_backup_gb, incremental_restore_gb, incremental_steps),
        ("Differential", differential_storage, differential_backup_gb, differential_restore_gb, differential_steps),
    ):
        backup_hours = duration_hours(backup_gb)
        restore_hours = duration_hours(restore_gb)
        rpo_ok = backup_interval_hours <= rpo_hours
        rto_ok = restore_hours <= rto_hours
        records.append({
            "Strategy": name,
            "Storage (GB)": storage,
            "Backup duration (hours)": backup_hours,
            "Restore duration (hours)": restore_hours,
            "Recovery steps": steps,
            "Restore data (GB)": restore_gb,
            "RPO compliant": "Yes" if rpo_ok else "No",
            "RTO compliant": "Yes" if rto_ok else "No",
            "Backup window (hours)": backup_hours,
        })
    return pd.DataFrame(records)


def recommend_strategy(comparison: pd.DataFrame, rpo_hours: float, rto_hours: float) -> str:
    compliant = comparison[
        (comparison["RPO compliant"] == "Yes") &
        (comparison["RTO compliant"] == "Yes")
    ]
    if compliant.empty:
        return "No strategy meets both objectives. Increase backup frequency or throughput, or revise RPO/RTO."
    lowest_storage = compliant.loc[compliant["Storage (GB)"].idxmin()]
    if lowest_storage["Strategy"] == "Incremental":
        return ("Incremental backup is the most storage-efficient option that meets RPO and RTO. "
                "Use periodic full backups and ordered incremental recovery.")
    if lowest_storage["Strategy"] == "Differential":
        return "Differential backup meets RPO and RTO while balancing storage and recovery complexity."
    return "Full backup meets RPO and RTO and offers the simplest independent recovery, if capacity is sufficient."


def show_backup() -> None:
    import plotly.express as px
    import streamlit as st

    st.header("Backup Strategy Planner")
    c1, c2, c3 = st.columns(3)
    data_size = c1.number_input("Original data size (GB)", min_value=1.0, value=1000.0, step=100.0)
    change_percent = c2.number_input("Daily data change (%)", min_value=0.0, max_value=100.0, value=5.0, step=1.0)
    retention = c3.number_input("Retention period (days)", min_value=1, max_value=365, value=7, step=1)

    c4, c5, c6, c7 = st.columns(4)
    throughput = c4.number_input("Backup throughput (MB/s)", min_value=0.1, value=100.0, step=10.0)
    backup_frequency = c5.selectbox("Backup frequency", ["Hourly", "Daily", "Weekly"], index=1)
    rpo = c6.number_input("Required RPO (hours)", min_value=0.1, value=24.0, step=1.0)
    rto = c7.number_input("Required RTO (hours)", min_value=0.1, value=4.0, step=0.5)
    interval = {"Hourly": 1.0, "Daily": 24.0, "Weekly": 168.0}[backup_frequency]
    st.caption("Simplified assumptions: fixed daily change, one initial full backup, and unchanged change data per interval.")

    try:
        comparison = backup_comparison(
            float(data_size), float(change_percent), int(retention),
            float(throughput), float(rpo), float(rto), interval,
        )
        st.subheader("Backup method comparison")
        st.dataframe(comparison, use_container_width=True)

        chart = px.bar(
            comparison,
            x="Strategy",
            y="Storage (GB)",
            color="Strategy",
            title="Estimated Retained Storage",
        )
        st.plotly_chart(chart, use_container_width=True)

        rpo_status = "satisfies" if interval <= rpo else "does not satisfy"
        st.info(f"The selected backup interval is {interval:g} hours and {rpo_status} the RPO of {rpo:g} hours.")

        recommendation = recommend_strategy(comparison, rpo, rto)
        st.success(recommendation)

        st.subheader("Restoration details")
        for _, row in comparison.iterrows():
            st.write(
                f"**{row['Strategy']}:** restore {row['Restore data (GB)']:.2f} GB "
                f"in {row['Recovery steps']} step(s), estimated at "
                f"{row['Restore duration (hours)']:.2f} hours."
            )
    except ValueError as exc:
        st.error(str(exc))
