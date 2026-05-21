import asyncio
import logging
from dataclasses import dataclass
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EligibilityResponse:
    is_active: bool
    payer_name: str
    group_number: str
    plan_name: str
    deductible_individual: float
    deductible_met: float
    out_of_pocket_max: float
    out_of_pocket_met: float
    copay: float
    coinsurance: float
    prior_auth_required: bool
    in_network: bool
    not_found: bool = False
    error: Optional[str] = None
    response_id: str = ""


# Realistic scenarios covering the most common denial root causes
_MOCK_SCENARIOS = [
    EligibilityResponse(
        is_active=True, payer_name="Blue Cross Blue Shield", group_number="GRP001",
        plan_name="BCBS PPO High Deductible", deductible_individual=3000.0, deductible_met=450.0,
        out_of_pocket_max=6000.0, out_of_pocket_met=450.0, copay=50.0, coinsurance=0.20,
        prior_auth_required=False, in_network=True,
    ),
    EligibilityResponse(
        is_active=False, payer_name="Aetna", group_number="GRP002",
        plan_name="Aetna Choice POS II", deductible_individual=2000.0, deductible_met=0.0,
        out_of_pocket_max=4000.0, out_of_pocket_met=0.0, copay=40.0, coinsurance=0.20,
        prior_auth_required=False, in_network=True,
    ),
    EligibilityResponse(
        is_active=True, payer_name="UnitedHealthcare", group_number="GRP003",
        plan_name="UHC Choice Plus", deductible_individual=1500.0, deductible_met=200.0,
        out_of_pocket_max=3000.0, out_of_pocket_met=200.0, copay=60.0, coinsurance=0.20,
        prior_auth_required=True, in_network=True,
    ),
    EligibilityResponse(
        is_active=True, payer_name="Cigna", group_number="GRP004",
        plan_name="Cigna Connect OON", deductible_individual=1000.0, deductible_met=800.0,
        out_of_pocket_max=2500.0, out_of_pocket_met=800.0, copay=75.0, coinsurance=0.40,
        prior_auth_required=False, in_network=False,
    ),
    EligibilityResponse(
        is_active=True, payer_name="Humana", group_number="GRP005",
        plan_name="Humana Gold Plus", deductible_individual=500.0, deductible_met=500.0,
        out_of_pocket_max=1500.0, out_of_pocket_met=1200.0, copay=25.0, coinsurance=0.10,
        prior_auth_required=False, in_network=True,
    ),
    EligibilityResponse(
        is_active=False, payer_name="Medicare", group_number="",
        plan_name="", deductible_individual=0, deductible_met=0,
        out_of_pocket_max=0, out_of_pocket_met=0, copay=0, coinsurance=0,
        prior_auth_required=False, in_network=False, not_found=True,
    ),
    EligibilityResponse(
        is_active=True, payer_name="Anthem", group_number="GRP006",
        plan_name="Anthem PPO", deductible_individual=2500.0, deductible_met=1900.0,
        out_of_pocket_max=5000.0, out_of_pocket_met=1900.0, copay=45.0, coinsurance=0.20,
        prior_auth_required=False, in_network=True,
    ),
]


async def check_eligibility(
    member_id: str,
    payer_id: str,
    service_type: str,
    provider_npi: str,
) -> EligibilityResponse:
    if not settings.pverify_mock_mode:
        raise NotImplementedError("Live pVerify integration: set PVERIFY_CLIENT_ID and PVERIFY_CLIENT_SECRET")

    await asyncio.sleep(0.05)  # simulate network latency

    scenario = _MOCK_SCENARIOS[hash(member_id) % len(_MOCK_SCENARIOS)]
    result = EligibilityResponse(
        **{**scenario.__dict__, "response_id": f"MOCK-{abs(hash(member_id)):08x}"}
    )

    # Log only non-PHI reference data
    logger.info(
        "pVerify check payer=%s service=%s response_id=%s active=%s",
        payer_id, service_type, result.response_id, result.is_active,
    )
    return result
