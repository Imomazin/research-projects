# Dataset Acquisition Status (P3 final stage)

**As of 2026-09-18, in the P3 execution environment.**

| Dataset | Role | Reachable here? | Status |
|---|---|---|---|
| Criteo Uplift v2.1 (unbiased) | randomized validation (E3) | **No** — `criteostorage.blob.core.windows.net` returns HTTP 403 at the network proxy (host not on the environment allow-list) | Pipeline validated on schema-exact fixture; canonical run **blocked by network policy** |
| Criteo Attribution for Bidding | observational journeys (E1/E4) | **No** — same host blocked | Observational methodology demonstrated on semi-synthetic journeys (E1); canonical run **blocked** |
| UCI Online Retail (id 352) | external validity (E7) | **No** — `archive.ics.uci.edu` returns HTTP 403 at the proxy; `ucimlrepo` therefore cannot fetch | Acquisition script ready; run **blocked by network policy** |

## What this means

- The environment's egress allow-list covers package registries (PyPI, npm, crates, …)
  and Anthropic APIs only. The dataset content-delivery hosts above are denied at the
  CONNECT stage (`recentRelayFailures` in the proxy status confirms the Criteo denial).
- This is a **data-access blocker**, not a compute/cost blocker. No paid compute was
  incurred and none is required for the semi-synthetic programme.
- The randomized (E3), observational-real (E4) and external-validity (E7) **canonical**
  runs require the operator to run the committed acquisition scripts
  (`03 Data/download_criteo_public.sh`, `03 Data/acquire_uci_online_retail.py`) from a
  network that permits those hosts, then invoke the (already validated) experiment
  scripts on the resulting files.

## What is NOT blocked and is complete here

- P3-E2 semi-synthetic truth recovery (known ATE/CATE).
- P3-E6 assumption/sensitivity and failure-region mapping.
- P3-E1 heuristic-vs-causal on semi-synthetic journeys (observational identification).
- P3-E5 matched-budget causal decision experiment.
- P3-E3 pipeline correctness, validated end-to-end on a schema-exact randomized fixture.

No real-data result is fabricated. The fixture is explicitly synthetic and never used
as manuscript evidence.
