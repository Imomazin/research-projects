#!/usr/bin/env python3
"""P2 evidence-constrained assurance analysis.

Consumes aggregate experiment evidence exported from Meridian. It never infers
missing metrics and never collapses the five objectives into a hidden weighted
score.

Expected CSV columns:
  configuration_id,domain,utility,robustness,epsilon,runtime_ms,
  communication_bytes,evidence_complete

Contract JSON example:
{
  "healthcare": {
    "min_utility": 0.80,
    "min_robustness": 0.70,
    "max_epsilon": 6,
    "max_runtime_ms": 60000,
    "max_communication_bytes": 100000000,
    "require_complete_evidence": true
  },
  "finance": { ... }
}

The script outputs:
- per-domain assurance evaluation
- per-domain Pareto fronts
- cross-domain assurance envelope
- transfer audit for each domain's best feasible-utility configuration

These outputs are analysis artefacts, not manuscript prose.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Evidence:
    configuration_id: str
    domain: str
    utility: float
    robustness: float
    epsilon: float
    runtime_ms: float
    communication_bytes: float
    evidence_complete: bool


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError(f"invalid boolean: {value}")


def load_evidence(path: Path) -> list[Evidence]:
    rows: list[Evidence] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "configuration_id",
            "domain",
            "utility",
            "robustness",
            "epsilon",
            "runtime_ms",
            "communication_bytes",
            "evidence_complete",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"evidence CSV missing columns: {sorted(missing)}")
        for row in reader:
            rows.append(
                Evidence(
                    configuration_id=row["configuration_id"].strip(),
                    domain=row["domain"].strip(),
                    utility=float(row["utility"]),
                    robustness=float(row["robustness"]),
                    epsilon=float(row["epsilon"]),
                    runtime_ms=float(row["runtime_ms"]),
                    communication_bytes=float(row["communication_bytes"]),
                    evidence_complete=parse_bool(row["evidence_complete"]),
                )
            )
    if not rows:
        raise ValueError("evidence CSV is empty")
    return rows


def evaluate(row: Evidence, contract: dict[str, Any]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []

    checks = [
        ("utility", "min_utility", row.utility, "min"),
        ("robustness", "min_robustness", row.robustness, "min"),
        ("epsilon", "max_epsilon", row.epsilon, "max"),
        ("runtime_ms", "max_runtime_ms", row.runtime_ms, "max"),
        (
            "communication_bytes",
            "max_communication_bytes",
            row.communication_bytes,
            "max",
        ),
    ]
    for field, key, observed, direction in checks:
        if key not in contract:
            continue
        required = float(contract[key])
        failed = observed < required if direction == "min" else observed > required
        if failed:
            violations.append(
                {"field": field, "observed": observed, "required": required}
            )

    if contract.get("require_complete_evidence", False) and not row.evidence_complete:
        violations.append(
            {"field": "evidence_complete", "observed": False, "required": True}
        )
    return violations


def dominates(a: Evidence, b: Evidence) -> bool:
    no_worse = (
        a.utility >= b.utility
        and a.robustness >= b.robustness
        and a.epsilon <= b.epsilon
        and a.runtime_ms <= b.runtime_ms
        and a.communication_bytes <= b.communication_bytes
    )
    strictly_better = (
        a.utility > b.utility
        or a.robustness > b.robustness
        or a.epsilon < b.epsilon
        or a.runtime_ms < b.runtime_ms
        or a.communication_bytes < b.communication_bytes
    )
    return no_worse and strictly_better


def pareto_front(rows: list[Evidence]) -> list[Evidence]:
    return [
        candidate
        for i, candidate in enumerate(rows)
        if not any(
            i != j and dominates(other, candidate)
            for j, other in enumerate(rows)
        )
    ]


def row_dict(row: Evidence) -> dict[str, Any]:
    return {
        "configuration_id": row.configuration_id,
        "domain": row.domain,
        "utility": row.utility,
        "robustness": row.robustness,
        "epsilon": row.epsilon,
        "runtime_ms": row.runtime_ms,
        "communication_bytes": row.communication_bytes,
        "evidence_complete": row.evidence_complete,
    }


def analyse(evidence: list[Evidence], contracts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    requested_domains = list(contracts)
    available_domains = {row.domain for row in evidence}
    missing_domains = [d for d in requested_domains if d not in available_domains]
    if missing_domains:
        raise ValueError(f"no evidence for required domains: {missing_domains}")

    by_domain: dict[str, list[Evidence]] = {
        domain: [row for row in evidence if row.domain == domain]
        for domain in requested_domains
    }

    domain_results: dict[str, Any] = {}
    feasible_sets: dict[str, set[str]] = {}

    for domain, rows in by_domain.items():
        contract = contracts[domain]
        evaluations = []
        feasible: list[Evidence] = []
        for row in rows:
            violations = evaluate(row, contract)
            passed = len(violations) == 0
            if passed:
                feasible.append(row)
            evaluations.append(
                {
                    "configuration_id": row.configuration_id,
                    "pass": passed,
                    "violations": violations,
                }
            )
        feasible_sets[domain] = {row.configuration_id for row in feasible}
        front = pareto_front(rows)
        domain_results[domain] = {
            "n_configurations": len(rows),
            "n_feasible": len(feasible),
            "evaluations": evaluations,
            "pareto_front": [row_dict(row) for row in front],
            "best_feasible_utility_configuration": (
                row_dict(max(feasible, key=lambda row: row.utility)) if feasible else None
            ),
        }

    cross_domain_ids = sorted(
        set.intersection(*(feasible_sets[domain] for domain in requested_domains))
        if requested_domains
        else set()
    )

    lookup = {(row.configuration_id, row.domain): row for row in evidence}
    transfer_audits: list[dict[str, Any]] = []

    for source_domain in requested_domains:
        source_best = domain_results[source_domain]["best_feasible_utility_configuration"]
        if source_best is None:
            continue
        configuration_id = source_best["configuration_id"]

        for target_domain in requested_domains:
            if target_domain == source_domain:
                continue
            target = lookup.get((configuration_id, target_domain))
            if target is None:
                transfer_audits.append(
                    {
                        "configuration_id": configuration_id,
                        "source_domain": source_domain,
                        "target_domain": target_domain,
                        "target_evidence_present": False,
                        "target_assurance_pass": False,
                        "utility_regret_to_best_feasible": None,
                        "target_pareto_efficient": None,
                        "violations": [],
                    }
                )
                continue

            violations = evaluate(target, contracts[target_domain])
            target_feasible = [
                row
                for row in by_domain[target_domain]
                if not evaluate(row, contracts[target_domain])
            ]
            best_target_utility = (
                max(row.utility for row in target_feasible) if target_feasible else None
            )
            target_front_ids = {
                row.configuration_id for row in pareto_front(by_domain[target_domain])
            }
            transfer_audits.append(
                {
                    "configuration_id": configuration_id,
                    "source_domain": source_domain,
                    "target_domain": target_domain,
                    "target_evidence_present": True,
                    "target_assurance_pass": len(violations) == 0,
                    "utility_regret_to_best_feasible": (
                        max(0.0, best_target_utility - target.utility)
                        if best_target_utility is not None
                        else None
                    ),
                    "target_pareto_efficient": configuration_id in target_front_ids,
                    "violations": violations,
                }
            )

    return {
        "domains": domain_results,
        "cross_domain_assurance_envelope": cross_domain_ids,
        "transfer_audits": transfer_audits,
        "analysis_rule": "Objectives are not collapsed into a weighted score. Assurance uses hard declared constraints; Pareto dominance preserves objective direction; transfer regret is utility loss relative to the best feasible target-domain configuration.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, help="Aggregate Meridian evidence CSV")
    parser.add_argument("--contracts", required=True, help="Domain assurance contracts JSON")
    parser.add_argument("--out", default="results/p2-assurance-analysis.json")
    args = parser.parse_args()

    evidence = load_evidence(Path(args.evidence))
    with Path(args.contracts).open("r", encoding="utf-8") as handle:
        contracts = json.load(handle)
    if not isinstance(contracts, dict) or not contracts:
        raise ValueError("contracts JSON must be a non-empty object keyed by domain")

    result = analyse(evidence, contracts)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
