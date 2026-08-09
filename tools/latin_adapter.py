#!/usr/bin/env python3
"""Minimal deterministic reference implementation of LanguageAdapter<lat>."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools.semantic_fingerprint import semantic_fingerprint_v1
from tools.source_text_normalization import (
    SourceTextDiagnostic,
    normalize_source_text,
    rejected_source_text,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEXICON = ROOT / "examples" / "latin-adapter" / "minimal-lexicon.json"
TOKEN_RE = re.compile(r"[^\W\d_]+|[^\s]", re.UNICODE)
PREPOSITIONS = {"a", "ab", "ad", "per"}
PUNCTUATION = {".", ",", ";", ":", "!", "?"}
AMBIGUITY_POLICIES = {
    "StrictReject",
    "InteractiveResolve",
    "ContextualDeterministic",
    "LegacyPermissive",
}
REQUIRED_TRANSFER_ROLES = ("Patient", "Source", "Goal")


def _diagnostic(
    code: str,
    severity: str,
    *,
    evidence_ids: list[str] | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "evidence_ids": evidence_ids or [],
    }
    if message is not None:
        result["message"] = message
    return result


def _lookup_key(surface: str) -> str:
    """Return the adapter-owned lexical lookup key without changing source text."""
    return surface.casefold()


def _map_source_span(
    normalized_span: dict[str, int], source_map: dict[str, Any]
) -> dict[str, Any]:
    start = normalized_span["start"]
    end = normalized_span["end"]
    overlapping = [
        entry
        for entry in source_map["entries"]
        if entry["output_span"]["start"] <= start
        and entry["output_span"]["end"] >= end
    ]
    if len(overlapping) == 1:
        entry = overlapping[0]
        if entry["exact"]:
            delta = start - entry["output_span"]["start"]
            return {
                "start": entry["source_span"]["start"] + delta,
                "end": entry["source_span"]["start"] + delta + (end - start),
                "exact": True,
            }
        return {
            "start": entry["source_span"]["start"],
            "end": entry["source_span"]["end"],
            "exact": False,
        }

    touched = [
        entry
        for entry in source_map["entries"]
        if entry["output_span"]["start"] < end
        and start < entry["output_span"]["end"]
    ]
    if not touched:
        return {"start": start, "end": end, "exact": False}
    return {
        "start": min(entry["source_span"]["start"] for entry in touched),
        "end": max(entry["source_span"]["end"] for entry in touched),
        "exact": False,
    }


class LatinLanguageAdapter:
    """Lexicon-driven Latin reference adapter for the accepted minimal corpus."""

    adapter_id = "lat"
    adapter_revision = "reference-pre-v0.8-1"

    def __init__(self, lexicon_path: Path = DEFAULT_LEXICON) -> None:
        self.lexicon_path = Path(lexicon_path)
        self.lexicon = json.loads(self.lexicon_path.read_text(encoding="utf-8"))
        if self.lexicon.get("adapter_id") != self.adapter_id:
            raise ValueError("Latin adapter requires a lexicon with adapter_id=lat")
        self.lexicon_revision = str(self.lexicon["lexicon_revision"])
        self._surface_index: dict[str, list[dict[str, Any]]] = {}
        for entry in self.lexicon["entries"]:
            for surface in entry.get("surface_forms", [entry["lemma"]]):
                self._surface_index.setdefault(_lookup_key(surface), []).append(entry)

    def _tokenize(
        self, normalized: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        text = normalized["output"]["normalized_text"]
        public_tokens: list[dict[str, Any]] = []
        analyses: list[dict[str, Any]] = []

        for ordinal, match in enumerate(TOKEN_RE.finditer(text), start=1):
            surface = match.group(0)
            token_id = f"t{ordinal}"
            normalized_span = {"start": match.start(), "end": match.end()}
            source_span = _map_source_span(
                normalized_span, normalized["source_map"]
            )
            record: dict[str, Any] = {
                "token_id": token_id,
                "surface": surface,
                "normalized_span": normalized_span,
                "source_span": source_span,
            }
            analysis: dict[str, Any] = {
                "record": record,
                "entries": [],
                "morphology": [],
            }
            lookup = _lookup_key(surface)
            if surface in PUNCTUATION:
                record["lexical_kind"] = "punctuation"
            elif lookup in PREPOSITIONS:
                record["lexical_kind"] = "preposition"
                record["lookup_key"] = lookup
            else:
                entries = self._surface_index.get(lookup, [])
                analysis["entries"] = entries
                record["lookup_key"] = lookup
                if entries:
                    record["lexeme_ids"] = sorted(
                        entry["lexeme_id"] for entry in entries
                    )
                    morphology = [
                        (entry, candidate)
                        for entry in entries
                        for candidate in entry.get("morphology", {}).get(
                            "candidates", []
                        )
                        if _lookup_key(candidate["surface"]) == lookup
                    ]
                    analysis["morphology"] = morphology
                    record["morphology_candidate_ids"] = sorted(
                        candidate["candidate_id"] for _, candidate in morphology
                    )
            public_tokens.append(record)
            analyses.append(analysis)
        return public_tokens, analyses

    @staticmethod
    def _is_preposition(analysis: dict[str, Any], values: list[str]) -> bool:
        record = analysis["record"]
        return (
            record.get("lexical_kind") == "preposition"
            and record.get("lookup_key") in values
        )

    @staticmethod
    def _morphology_with_case(
        analysis: dict[str, Any], latin_case: str
    ) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        return [
            pair
            for pair in analysis["morphology"]
            if pair[1]["features"].get("case") == latin_case
        ]

    @staticmethod
    def _semantic_value(entry: dict[str, Any]) -> dict[str, Any] | None:
        for candidate in entry.get("semantic_candidates", []):
            proposal = candidate["proposal"]
            if proposal == "ThermalEnergyExpression":
                return {
                    "kind": "SemanticKind",
                    "semantic_kind": "Energy",
                    "mode": "Thermal",
                }
            if proposal == "SymbolicSelectorCandidate":
                symbol = candidate.get("qualifiers", {}).get("symbol")
                if isinstance(symbol, str) and symbol:
                    return {
                        "kind": "SelectorProposal",
                        "selector": {"kind": "Symbolic", "symbol": symbol},
                    }
        return None

    def _transfer_analysis(
        self, analyses: list[dict[str, Any]]
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]], set[str]]:
        action_matches: list[
            tuple[int, dict[str, Any], dict[str, Any]]
        ] = []
        for index, analysis in enumerate(analyses):
            for entry, morphology in analysis["morphology"]:
                proposals = {
                    candidate["proposal"]
                    for candidate in entry.get("semantic_candidates", [])
                }
                if (
                    "TransferCommand" in proposals
                    and morphology["features"].get("mood") == "imperative"
                ):
                    action_matches.append((index, entry, morphology))
        if len(action_matches) != 1:
            return None, [], set()

        action_index, action_entry, action_morphology = action_matches[0]
        frame = action_entry.get("argument_frame")
        if not frame:
            return None, [], set()

        choices: dict[
            str,
            list[
                tuple[
                    int,
                    dict[str, Any],
                    dict[str, Any],
                    int | None,
                ]
            ],
        ] = {}
        for slot in frame["slots"]:
            role = slot["role"]
            morphosyntax = slot["morphosyntax"]
            latin_case = morphosyntax["case"]
            prepositions = morphosyntax.get("prepositions", [])
            role_choices: list[
                tuple[
                    int,
                    dict[str, Any],
                    dict[str, Any],
                    int | None,
                ]
            ] = []

            if prepositions:
                for prep_index, prep_analysis in enumerate(analyses[:-1]):
                    if not self._is_preposition(prep_analysis, prepositions):
                        continue
                    argument_index = prep_index + 1
                    for entry, morphology in self._morphology_with_case(
                        analyses[argument_index], latin_case
                    ):
                        role_choices.append(
                            (argument_index, entry, morphology, prep_index)
                        )
            else:
                for argument_index, analysis in enumerate(analyses[:action_index]):
                    if analysis["record"].get("lexical_kind"):
                        continue
                    if (
                        argument_index > 0
                        and analyses[argument_index - 1]["record"].get(
                            "lexical_kind"
                        )
                        == "preposition"
                    ):
                        continue
                    for entry, morphology in self._morphology_with_case(
                        analysis, latin_case
                    ):
                        role_choices.append(
                            (argument_index, entry, morphology, None)
                        )
            choices[role] = role_choices

        if any(len(choices.get(role, [])) != 1 for role in REQUIRED_TRANSFER_ROLES):
            ambiguous = [
                {
                    "role": role,
                    "candidate_token_ids": [
                        analyses[index]["record"]["token_id"]
                        for index, _, _, _ in choices.get(role, [])
                    ],
                }
                for role in REQUIRED_TRANSFER_ROLES
                if len(choices.get(role, [])) > 1
            ]
            return None, ambiguous, set()

        evidence: list[dict[str, Any]] = []
        evidence_ids: set[str] = set()
        roles: list[dict[str, Any]] = []
        role_proposals: list[dict[str, Any]] = []
        identity_parts: list[str] = []

        for role in REQUIRED_TRANSFER_ROLES:
            argument_index, entry, morphology, prep_index = choices[role][0]
            argument_token = analyses[argument_index]["record"]
            argument_token["selected_morphology_candidate_ids"] = [
                morphology["candidate_id"]
            ]
            token_ids = [argument_token["token_id"]]
            if prep_index is not None:
                token_ids.insert(0, analyses[prep_index]["record"]["token_id"])
            frame_evidence_id = f"frame-{role.lower()}"
            morphology_evidence_id = f"morphology:{morphology['candidate_id']}"
            evidence.extend(
                [
                    {
                        "evidence_id": frame_evidence_id,
                        "kind": "verb-frame",
                        "lexeme_id": action_entry["lexeme_id"],
                        "frame_id": frame["frame_id"],
                        "slot": role,
                    },
                    {
                        "evidence_id": morphology_evidence_id,
                        "kind": "morphology",
                        "lexeme_id": entry["lexeme_id"],
                        "candidate_id": morphology["candidate_id"],
                        "token_id": argument_token["token_id"],
                    },
                ]
            )
            role_evidence = [
                *token_ids,
                morphology_evidence_id,
                frame_evidence_id,
            ]
            evidence_ids.update(role_evidence)
            semantic_value = self._semantic_value(entry)
            if semantic_value is None:
                return None, [], set()
            semantic_value["evidence_ids"] = role_evidence
            roles.append({"role": role, "value": semantic_value})
            role_proposals.append(
                {
                    "role": role,
                    "token_ids": token_ids,
                    "evidence_ids": role_evidence,
                    "status": "proposal",
                }
            )
            identity_parts.append(entry["lexeme_id"].removeprefix("lat:"))

        action_record = analyses[action_index]["record"]
        action_record["selected_morphology_candidate_ids"] = [
            action_morphology["candidate_id"]
        ]
        action_evidence_id = f"morphology:{action_morphology['candidate_id']}"
        evidence.append(
            {
                "evidence_id": action_evidence_id,
                "kind": "morphology",
                "lexeme_id": action_entry["lexeme_id"],
                "candidate_id": action_morphology["candidate_id"],
                "token_id": action_record["token_id"],
            }
        )
        evidence_ids.update({action_record["token_id"], action_evidence_id})

        roles.append(
            {
                "role": "Quantity",
                "value": {
                    "kind": "Unknown",
                    "reason": "MissingSurfaceArgument",
                    "evidence_ids": [],
                },
            }
        )
        candidate_id = "lat:transfer:" + ":".join(identity_parts)
        nsr: dict[str, Any] = {
            "schema_version": "0.7.3",
            "kind": "TransferCommand",
            "action": "transfer",
            "roles": roles,
            "unknowns": [
                {
                    "field": "Quantity",
                    "reason": "MissingSurfaceArgument",
                    "required_for": ["TypedMIR elaboration"],
                }
            ],
            "provenance": {
                "adapter_id": self.adapter_id,
                "adapter_revision": self.adapter_revision,
                "source_language_tags": ["lat"],
                "provider": "LexiconDriven",
                "source_hash": None,
                "evidence_ids": sorted(evidence_ids),
            },
            "ambiguity": {
                "policy": "StrictReject",
                "candidate_id": candidate_id,
                "alternative_candidate_ids": [],
                "decision_evidence_ids": [
                    "frame-patient",
                    "frame-source",
                    "frame-goal",
                ],
            },
        }
        nsr["semantic_fingerprint"] = semantic_fingerprint_v1(nsr)
        return (
            {
                "candidate_id": candidate_id,
                "unresolved_fields": ["Quantity"],
                "provider": "LexiconDriven",
                "evidence_ids": sorted(evidence_ids),
                "nsr": nsr,
                "role_proposals": role_proposals,
                "action_proposal": {
                    "action": "transfer",
                    "token_ids": [action_record["token_id"]],
                    "evidence_ids": [
                        action_record["token_id"],
                        action_evidence_id,
                    ],
                    "status": "proposal",
                },
                "evidence": evidence,
            },
            [],
            evidence_ids,
        )

    def normalize(
        self,
        source: str | bytes,
        *,
        ambiguity_policy: str = "StrictReject",
    ) -> dict[str, Any]:
        if ambiguity_policy not in AMBIGUITY_POLICIES:
            raise ValueError(f"unsupported AmbiguityPolicy: {ambiguity_policy}")

        adapter = {
            "adapter_id": self.adapter_id,
            "adapter_revision": self.adapter_revision,
            "lexicon_revision": self.lexicon_revision,
        }
        try:
            normalized = normalize_source_text(
                source,
                adapter_id=self.adapter_id,
                external_language_tags=("lat",),
                script_hints=("Latn",),
            )
        except SourceTextDiagnostic as error:
            boundary = "utf8-bytes" if isinstance(source, bytes) else "unicode-text"
            return {
                "adapter": adapter,
                "source_normalization": rejected_source_text(
                    error,
                    adapter_id=self.adapter_id,
                    boundary=boundary,
                ),
                "tokens": [],
                "evidence": [],
                "role_proposals": [],
                "normalization_candidate_set": {
                    "policy": ambiguity_policy,
                    "decision_status": "Rejected",
                    "selected_candidate_id": None,
                    "candidates": [],
                },
                "diagnostics": [
                    _diagnostic(error.code, "fatal", message=error.message),
                    _diagnostic(
                        "NormalizationFailed",
                        "fatal",
                        message="source normalization did not produce adapter input",
                    ),
                ],
            }

        tokens, analyses = self._tokenize(normalized)
        diagnostics: list[dict[str, Any]] = []
        for analysis in analyses:
            record = analysis["record"]
            if record.get("lexical_kind"):
                continue
            if not analysis["entries"]:
                diagnostics.append(
                    _diagnostic(
                        "LexiconEntryMissing",
                        "fatal",
                        evidence_ids=[record["token_id"]],
                        message=f"no Latin lexicon entry for {record['surface']!r}",
                    )
                )
            elif not analysis["morphology"]:
                diagnostics.append(
                    _diagnostic(
                        "MorphologicalAnalysisIncomplete",
                        "fatal",
                        evidence_ids=[record["token_id"]],
                        message=(
                            "lexicon entry exists but has no morphology candidate "
                            f"for {record['surface']!r}"
                        ),
                    )
                )

        candidate: dict[str, Any] | None = None
        ambiguous_roles: list[dict[str, Any]] = []
        if not diagnostics:
            candidate, ambiguous_roles, _ = self._transfer_analysis(analyses)

        raw_ambiguities = [
            {
                "token_id": analysis["record"]["token_id"],
                "morphology_candidate_ids": analysis["record"].get(
                    "morphology_candidate_ids", []
                ),
            }
            for analysis in analyses
            if len(analysis["record"].get("morphology_candidate_ids", [])) > 1
            and not analysis["record"].get("selected_morphology_candidate_ids")
        ]
        semantic_ambiguity = bool(ambiguous_roles or raw_ambiguities)

        if candidate is not None:
            candidate["nsr"]["ambiguity"]["policy"] = ambiguity_policy
            result_candidates = [
                {
                    key: value
                    for key, value in candidate.items()
                    if key not in {"role_proposals", "action_proposal", "evidence"}
                }
            ]
            decision_status = "Selected"
            selected_candidate_id = candidate["candidate_id"]
            role_proposals = candidate["role_proposals"]
            action_proposal = candidate["action_proposal"]
            evidence = candidate["evidence"]
        else:
            result_candidates = []
            selected_candidate_id = None
            role_proposals = []
            action_proposal = None
            evidence = []
            if semantic_ambiguity:
                ambiguous_evidence = sorted(
                    {
                        *(
                            ambiguity["token_id"]
                            for ambiguity in raw_ambiguities
                        ),
                        *(
                            token_id
                            for ambiguity in ambiguous_roles
                            for token_id in ambiguity["candidate_token_ids"]
                        ),
                    }
                )
                diagnostics.append(
                    _diagnostic(
                        "SemanticRoleAmbiguous",
                        "conditional",
                        evidence_ids=ambiguous_evidence,
                        message="morphology/frame evidence does not determine one semantic role",
                    )
                )
                if ambiguity_policy == "StrictReject":
                    decision_status = "Rejected"
                    diagnostics.append(
                        _diagnostic(
                            "AmbiguousNormalization",
                            "fatal",
                            evidence_ids=ambiguous_evidence,
                        )
                    )
                elif ambiguity_policy == "InteractiveResolve":
                    decision_status = "PendingInteraction"
                    diagnostics.append(
                        _diagnostic(
                            "AmbiguityInteractionRequired",
                            "conditional",
                            evidence_ids=ambiguous_evidence,
                        )
                    )
                else:
                    decision_status = "Unreproducible"
                    diagnostics.append(
                        _diagnostic(
                            "AmbiguityDecisionUnreproducible",
                            "fatal",
                            evidence_ids=ambiguous_evidence,
                            message="no versioned selection profile was supplied",
                        )
                    )
            else:
                decision_status = "Rejected"

            diagnostics.append(
                _diagnostic(
                    "NormalizationFailed",
                    "fatal" if decision_status != "PendingInteraction" else "conditional",
                    message="no usable NSR candidate was produced",
                )
            )

        result: dict[str, Any] = {
            "adapter": adapter,
            "source_normalization": normalized,
            "tokens": tokens,
            "evidence": evidence,
            "role_proposals": role_proposals,
            "normalization_candidate_set": {
                "policy": ambiguity_policy,
                "decision_status": decision_status,
                "selected_candidate_id": selected_candidate_id,
                "candidates": result_candidates,
            },
            "diagnostics": diagnostics,
        }
        if action_proposal is not None:
            result["action_proposal"] = action_proposal
        if semantic_ambiguity:
            result["unresolved_ambiguity"] = {
                "morphology": raw_ambiguities,
                "roles": ambiguous_roles,
            }
        return result


def normalize_with_adapter(
    adapter_id: str,
    source: str | bytes,
    *,
    ambiguity_policy: str = "StrictReject",
    lexicon_path: Path = DEFAULT_LEXICON,
) -> dict[str, Any]:
    """Dispatch an explicitly selected project adapter without language detection."""
    if adapter_id != "lat":
        return {
            "adapter": {"adapter_id": adapter_id},
            "tokens": [],
            "evidence": [],
            "role_proposals": [],
            "normalization_candidate_set": {
                "policy": ambiguity_policy,
                "decision_status": "Rejected",
                "selected_candidate_id": None,
                "candidates": [],
            },
            "diagnostics": [
                _diagnostic(
                    "LanguageAdapterUnavailable",
                    "fatal",
                    message=f"project adapter {adapter_id!r} is unavailable",
                )
            ],
        }
    return LatinLanguageAdapter(lexicon_path).normalize(
        source,
        ambiguity_policy=ambiguity_policy,
    )
