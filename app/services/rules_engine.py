from dataclasses import dataclass
from typing import List
from app.models import Priority
from app.services.pverify_client import EligibilityResponse

_DEDUCTIBLE_HIGH = 1000.0
_DEDUCTIBLE_MEDIUM = 500.0


@dataclass
class Flag:
    priority: Priority
    flag_type: str
    description: str
    recommended_action: str


def evaluate(response: EligibilityResponse, service_type: str) -> List[Flag]:
    flags: List[Flag] = []

    if response.not_found:
        flags.append(Flag(
            priority=Priority.CRITICAL,
            flag_type="PATIENT_NOT_FOUND",
            description=f"Patient not found in {response.payer_name} system",
            recommended_action=(
                "Call patient to verify insurance information. "
                "Collect updated insurance card at check-in or obtain self-pay agreement."
            ),
        ))
        return flags  # no point running further rules

    if not response.is_active:
        flags.append(Flag(
            priority=Priority.CRITICAL,
            flag_type="INACTIVE_COVERAGE",
            description=f"Coverage is inactive with {response.payer_name}",
            recommended_action=(
                "Contact patient immediately. Do not proceed without confirmed active coverage "
                "or a signed self-pay agreement on file."
            ),
        ))

    if response.prior_auth_required:
        flags.append(Flag(
            priority=Priority.HIGH,
            flag_type="PRIOR_AUTH_REQUIRED",
            description=f"Prior authorization required by {response.payer_name} for {service_type}",
            recommended_action=(
                "Verify auth is on file before appointment. "
                "If missing, initiate request now — allow 48-72 hours for approval."
            ),
        ))

    if not response.in_network:
        flags.append(Flag(
            priority=Priority.MEDIUM,
            flag_type="OUT_OF_NETWORK",
            description=(
                f"Provider is out-of-network for {response.payer_name} {response.plan_name}. "
                f"Patient coinsurance: {response.coinsurance:.0%}"
            ),
            recommended_action=(
                "Notify patient of out-of-network cost difference before the visit. "
                "Obtain signed financial responsibility form."
            ),
        ))

    if response.is_active:
        remaining = response.deductible_individual - response.deductible_met
        if remaining > _DEDUCTIBLE_HIGH:
            flags.append(Flag(
                priority=Priority.HIGH,
                flag_type="HIGH_DEDUCTIBLE_REMAINING",
                description=(
                    f"${remaining:,.2f} remaining on individual deductible "
                    f"(${response.deductible_individual:,.2f} plan, ${response.deductible_met:,.2f} met)"
                ),
                recommended_action=(
                    f"Collect estimated patient responsibility at time of service. "
                    f"Verify payment method on file."
                ),
            ))
        elif remaining > _DEDUCTIBLE_MEDIUM:
            flags.append(Flag(
                priority=Priority.MEDIUM,
                flag_type="MEDIUM_DEDUCTIBLE_REMAINING",
                description=f"${remaining:,.2f} remaining on individual deductible",
                recommended_action="Inform patient of remaining deductible. Confirm payment method on file.",
            ))

    return flags
