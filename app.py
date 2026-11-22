import streamlit as st

from modules.raid import show_raid
from modules.disk_performance import show_disk
from modules.backup import show_backup
from modules.replication import show_replication
from modules.risk_assessment import show_risk


st.set_page_config(
    page_title="StorageLab",
    page_icon="storage",
    layout="wide",
)

st.sidebar.title("StorageLab")
page = st.sidebar.radio(
    "Navigate",
    [
        "Home",
        "RAID Simulator",
        "Disk Performance Analyzer",
        "Backup Strategy Planner",
        "Replication Simulator",
        "Storage Risk Assessment",
    ],
)


def show_home() -> None:
    st.title("StorageLab")
    st.subheader("RAID Simulator and Storage Performance Analyzer")
    st.write(
        "StorageLab is an interactive simulation tool for exploring RAID fault tolerance, "
        "disk performance, backup strategies, replication behavior, and storage risks."
    )

    cards = [
        ("RAID Simulator", "Configure RAID, calculate capacity, fail disks, recover XOR parity, and estimate rebuild time."),
        ("Disk Performance", "Analyze rotational latency, transfer time, IOPS, utilization, and queue response."),
        ("Backup Planner", "Compare full, incremental, and differential backup storage and recovery objectives."),
        ("Replication", "Compare synchronous and asynchronous replication assumptions."),
        ("Risk Assessment", "Calculate likelihood-impact risk scores and mitigations."),
    ]
    for title, description in cards:
        with st.container(border=True):
            st.markdown(f"### {title}")
            st.write(description)


if page == "Home":
    show_home()
elif page == "RAID Simulator":
    show_raid()
elif page == "Disk Performance Analyzer":
    show_disk()
elif page == "Backup Strategy Planner":
    show_backup()
elif page == "Replication Simulator":
    show_replication()
else:
    show_risk()
