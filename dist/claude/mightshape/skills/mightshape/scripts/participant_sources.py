#!/usr/bin/env python3
"""Participant-source boundary for Inquiry Lab.

V1 implements synthetic sourcing and bring-your-own invitation handoff.  The
Exchange class is an intentionally non-operational provider contract: every
marketplace-like operation returns a structured future-feature status without
affecting the other providers.
"""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable

from dc_core import DesignCouncilError, json_output, schema_validation


PROVIDER_VERSION = "1.0.0"
SOURCES = ("SYNTHETIC", "BRING_YOUR_OWN", "EXCHANGE")
EXCHANGE_OPERATIONS = (
    "create_recruitment_request",
    "estimate_participant_pool",
    "match_participants",
    "invite_participants",
    "track_participation",
    "return_completed_sessions",
)


@dataclass(frozen=True)
class SourceRequest:
    study_id: str
    target_count: int = 1
    grounding_level: str = "RESEARCHED"
    invite_url: str | None = None

    def validate(self) -> None:
        if not self.study_id.startswith("STUDY-") or not self.study_id[6:].isdigit():
            raise DesignCouncilError("study_id must use STUDY-###")
        if not 1 <= self.target_count <= 100:
            raise DesignCouncilError("target_count must be between 1 and 100")
        if self.grounding_level not in {"FAST", "RESEARCHED", "DEEP"}:
            raise DesignCouncilError("grounding_level must be FAST, RESEARCHED, or DEEP")


class ParticipantSource(ABC):
    """Stable participant-sourcing boundary, independent of interview logic."""

    provider: str

    @abstractmethod
    def prepare(self, request: SourceRequest) -> dict[str, Any]:
        """Return a provider-specific readiness result without mutating a study."""

    def _result(
        self,
        request: SourceRequest,
        *,
        status: str,
        next_action: str,
        capabilities: list[str],
        limitations: list[str],
        configuration: dict[str, Any],
    ) -> dict[str, Any]:
        result = {
            "provider": self.provider,
            "provider_version": PROVIDER_VERSION,
            "status": status,
            "study_id": request.study_id,
            "configuration": configuration,
            "next_action": next_action,
            "capabilities": capabilities,
            "limitations": limitations,
        }
        validation = schema_validation(result, "participant-source.schema.json")
        if not validation["valid"]:
            raise DesignCouncilError("participant-source contract failure: " + "; ".join(validation["errors"]))
        return result


class SyntheticParticipantSource(ParticipantSource):
    provider = "SYNTHETIC"

    def prepare(self, request: SourceRequest) -> dict[str, Any]:
        request.validate()
        return self._result(
            request,
            status="READY",
            next_action="BUILD_REALITY_PACKET_THEN_GENERATE_INDEPENDENT_PERSONAS",
            capabilities=[
                "research_grounded_persona_generation",
                "sealed_independent_interviews",
                "synthetic_convergence_check",
            ],
            limitations=[
                "Outputs remain synthetic evidence and never become human evidence.",
                "A Reality Packet is required for consequential simulation.",
            ],
            configuration={
                "target_count": request.target_count,
                "grounding_level": request.grounding_level,
                "invite_url": None,
                "exchange_connector": None,
            },
        )


class BringYourOwnParticipantSource(ParticipantSource):
    provider = "BRING_YOUR_OWN"

    def prepare(self, request: SourceRequest) -> dict[str, Any]:
        request.validate()
        status = "READY" if request.invite_url else "NEEDS_HOSTING"
        action = "INVITE_PARTICIPANTS_WITH_APPROVED_EXTERNAL_PACKET" if request.invite_url else "CREATE_OR_DEPLOY_SHAREABLE_INTERVIEW_LINK"
        return self._result(
            request,
            status=status,
            next_action=action,
            capabilities=[
                "researcher_supplied_participants",
                "ai_facilitated_interview",
                "human_interview_evidence_ingestion",
            ],
            limitations=[
                "Recruitment is owned by the researcher.",
                "A URL is never fabricated when hosting is unavailable.",
                "Disclosure review and participant consent are required before collection.",
            ],
            configuration={
                "target_count": request.target_count,
                "grounding_level": request.grounding_level,
                "invite_url": request.invite_url,
                "exchange_connector": None,
            },
        )


class ExchangeParticipantSource(ParticipantSource):
    """Future provider facade. No recruitment, payments, or matching run in V1."""

    provider = "EXCHANGE"

    def prepare(self, request: SourceRequest) -> dict[str, Any]:
        request.validate()
        return self._result(
            request,
            status="NOT_CONFIGURED",
            next_action="USE_SYNTHETIC_OR_BRING_YOUR_OWN",
            capabilities=[],
            limitations=[
                "MightShape Exchange is a FUTURE_FEATURE in V1.",
                "No marketplace, recruitment, verification, compensation, payments, or credit operations are implemented.",
            ],
            configuration={
                "target_count": request.target_count,
                "grounding_level": request.grounding_level,
                "invite_url": None,
                "exchange_connector": None,
            },
        )

    def _future_operation(self, operation: str, request: SourceRequest) -> dict[str, Any]:
        request.validate()
        if operation not in EXCHANGE_OPERATIONS:
            raise DesignCouncilError(f"unsupported Exchange operation: {operation}")
        return {
            "provider": "EXCHANGE",
            "provider_version": PROVIDER_VERSION,
            "operation": operation,
            "study_id": request.study_id,
            "status": "FUTURE_FEATURE",
            "configured": False,
            "side_effect_performed": False,
            "message": "MightShape Exchange is not configured in V1; use SYNTHETIC or BRING_YOUR_OWN.",
        }

    def create_recruitment_request(self, request: SourceRequest) -> dict[str, Any]:
        return self._future_operation("create_recruitment_request", request)

    def estimate_participant_pool(self, request: SourceRequest) -> dict[str, Any]:
        return self._future_operation("estimate_participant_pool", request)

    def match_participants(self, request: SourceRequest) -> dict[str, Any]:
        return self._future_operation("match_participants", request)

    def invite_participants(self, request: SourceRequest) -> dict[str, Any]:
        return self._future_operation("invite_participants", request)

    def track_participation(self, request: SourceRequest) -> dict[str, Any]:
        return self._future_operation("track_participation", request)

    def return_completed_sessions(self, request: SourceRequest) -> dict[str, Any]:
        return self._future_operation("return_completed_sessions", request)


SOURCE_FACTORIES: dict[str, Callable[[], ParticipantSource]] = {
    "SYNTHETIC": SyntheticParticipantSource,
    "BRING_YOUR_OWN": BringYourOwnParticipantSource,
    "EXCHANGE": ExchangeParticipantSource,
}


def get_participant_source(name: str) -> ParticipantSource:
    try:
        return SOURCE_FACTORIES[name.upper()]()
    except KeyError as exc:
        raise DesignCouncilError(f"participant source must be one of: {', '.join(SOURCES)}") from exc


def prepare_source(name: str, request: SourceRequest) -> dict[str, Any]:
    return get_participant_source(name).prepare(request)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or prepare an Inquiry Lab participant source")
    parser.add_argument("--source", required=True, choices=SOURCES)
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--target-count", type=int, default=1)
    parser.add_argument("--grounding-level", choices=["FAST", "RESEARCHED", "DEEP"], default="RESEARCHED")
    parser.add_argument("--invite-url")
    parser.add_argument("--exchange-operation", choices=EXCHANGE_OPERATIONS)
    args = parser.parse_args()

    request = SourceRequest(
        study_id=args.study_id,
        target_count=args.target_count,
        grounding_level=args.grounding_level,
        invite_url=args.invite_url,
    )
    try:
        source = get_participant_source(args.source)
        if args.exchange_operation:
            if not isinstance(source, ExchangeParticipantSource):
                raise DesignCouncilError("--exchange-operation requires --source EXCHANGE")
            method = getattr(source, args.exchange_operation)
            result = method(request)
        else:
            result = source.prepare(request)
        json_output(result)
        return 0
    except DesignCouncilError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
