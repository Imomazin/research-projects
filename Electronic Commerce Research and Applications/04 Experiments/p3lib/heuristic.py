"""Non-causal multi-touch attribution baselines.

Mirrors Orbit's inherited heuristic attribution (first-touch, last-touch, linear,
time-decay, fixed weighted/position-based). These answer a DESCRIPTIVE credit-
assignment question, not a causal-incrementality question, and are used strictly
as the non-causal comparison baseline. Credits sum to 1 within each converting
journey; channel shares are normalised across all converting journeys.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Sequence, Tuple

# A touchpoint: (channel, days_before_conversion). Earlier touches have larger t.
Touchpoint = Tuple[str, float]

MODELS = ["first-touch", "last-touch", "linear", "time-decay", "weighted"]


def _order_by_time(journey: Sequence[Touchpoint]) -> List[Touchpoint]:
    # Earliest first: larger days_before_conversion == earlier.
    return sorted(journey, key=lambda tp: -tp[1])


def credit_journey(journey: Sequence[Touchpoint], model: str, half_life_days: float = 7.0) -> Dict[str, float]:
    tps = _order_by_time(journey)
    k = len(tps)
    if k == 0:
        return {}
    credit: Dict[str, float] = defaultdict(float)

    if model == "first-touch":
        credit[tps[0][0]] += 1.0
    elif model == "last-touch":
        credit[tps[-1][0]] += 1.0
    elif model == "linear":
        for ch, _ in tps:
            credit[ch] += 1.0 / k
    elif model == "time-decay":
        weights = [0.5 ** (t / half_life_days) for _, t in tps]
        s = sum(weights) or 1.0
        for (ch, _), w in zip(tps, weights):
            credit[ch] += w / s
    elif model == "weighted":
        # Position-based U-shape: 40% first, 40% last, 20% split across the middle.
        if k == 1:
            credit[tps[0][0]] += 1.0
        elif k == 2:
            credit[tps[0][0]] += 0.5
            credit[tps[-1][0]] += 0.5
        else:
            credit[tps[0][0]] += 0.4
            credit[tps[-1][0]] += 0.4
            mid = tps[1:-1]
            for ch, _ in mid:
                credit[ch] += 0.2 / len(mid)
    else:
        raise ValueError(f"unknown attribution model {model!r}")
    return dict(credit)


def attribute(journeys: Sequence[Sequence[Touchpoint]], converted: Sequence[int],
              model: str, half_life_days: float = 7.0) -> Dict[str, float]:
    """Total credit per channel across converting journeys."""
    totals: Dict[str, float] = defaultdict(float)
    for journey, conv in zip(journeys, converted):
        if conv != 1:
            continue
        for ch, c in credit_journey(journey, model, half_life_days).items():
            totals[ch] += c
    return dict(totals)


def attribution_shares(journeys, converted, model, half_life_days: float = 7.0) -> Dict[str, float]:
    totals = attribute(journeys, converted, model, half_life_days)
    s = sum(totals.values()) or 1.0
    return {ch: v / s for ch, v in totals.items()}
