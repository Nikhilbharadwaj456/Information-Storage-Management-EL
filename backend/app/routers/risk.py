from fastapi import APIRouter

from backend.app.schemas import RiskRequest
from modules.risk_assessment import MITIGATIONS, calculate_risk, risk_category
from modules.explainability import risk_explanation


router = APIRouter(prefix="/api/risk", tags=["Risk"])


@router.post("/calculate")
async def calculate(request: RiskRequest) -> dict:
    score = calculate_risk(request.likelihood, request.impact)
    category = risk_category(score)
    mitigation = MITIGATIONS.get(
        request.threat,
        "Document the risk, apply compensating controls, and review regularly.",
    )
    return {
        "asset": request.asset,
        "threat": request.threat,
        "vulnerability": request.vulnerability,
        "likelihood": request.likelihood,
        "impact": request.impact,
        "risk_score": score,
        "risk_category": category,
        "suggested_mitigation": mitigation,
        "score_scale": "1-25",
        "explanation": risk_explanation(
            request.asset,
            request.threat,
            request.vulnerability,
            request.likelihood,
            request.impact,
            score,
            category,
            mitigation,
        ),
    }
