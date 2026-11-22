from __future__ import annotations

MITIGATIONS = {
    "Hardware failure": "Use RAID redundancy, monitoring, and hot spares.",
    "Ransomware": "Maintain isolated, immutable backups and test restore procedures.",
    "Unauthorized access": "Enforce MFA, least privilege, encryption, and audit logs.",
}


def risk_category(score: int) -> str:
    if score <= 5:
        return "Low"
    if score <= 10:
        return "Medium"
    if score <= 15:
        return "High"
    return "Critical"


def calculate_risk(likelihood: int, impact: int) -> int:
    if (not isinstance(likelihood, int) or isinstance(likelihood, bool)
            or not isinstance(impact, int) or isinstance(impact, bool)):
        raise ValueError("Likelihood and impact must be integers on the 1 to 5 scale.")
    if not 1 <= likelihood <= 5 or not 1 <= impact <= 5:
        raise ValueError("Likelihood and impact must use the 1 to 5 scale.")
    return likelihood * impact


def show_risk() -> None:
    import pandas as pd
    import streamlit as st

    st.header("Storage Security and Risk Assessment")
    asset = st.selectbox("Asset", ["Stored data", "Storage devices", "Backup servers"])
    threat = st.selectbox("Threat", list(MITIGATIONS))
    vulnerability = st.selectbox(
        "Vulnerability",
        ["Weak authentication", "Unencrypted backups", "Lack of redundancy"],
    )
    c1, c2 = st.columns(2)
    likelihood = c1.slider("Likelihood (1-5)", 1, 5, 3)
    impact = c2.slider("Impact (1-5)", 1, 5, 3)

    try:
        score = calculate_risk(likelihood, impact)
        category = risk_category(score)
        st.metric("Risk score", f"{score}/25")
        st.metric("Risk category", category)
        st.warning(f"Suggested mitigation: {MITIGATIONS[threat]}")
        st.dataframe(pd.DataFrame([{
            "Asset": asset,
            "Threat": threat,
            "Vulnerability": vulnerability,
            "Likelihood": likelihood,
            "Impact": impact,
            "Score": score,
            "Category": category,
        }]), use_container_width=True)
    except ValueError as exc:
        st.error(str(exc))
