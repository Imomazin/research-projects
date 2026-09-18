# Table T9 — Configuration transfer audit (full portability matrix)

_transfer feasibility (pass/fail), utility regret vs best feasible target config, and constraint violations._

| Configuration | Transfer | Feasible | Utility regret | # violations | Target Pareto-eff. |
|---|---|---|---|---|---|
| agg=fedavg|priv=no-dp | clinical-sim→financial-sim | false | 0 | 1 | true |
| agg=fedavg|priv=no-dp | financial-sim→clinical-sim | false | 0 | 1 | true |
| agg=fedavg|priv=static-dp@6 | clinical-sim→financial-sim | false | 0.006078000000000028 | 2 | false |
| agg=fedavg|priv=static-dp@6 | financial-sim→clinical-sim | false | 0 | 1 | false |
| agg=fedavg|priv=static-dp@3 | clinical-sim→financial-sim | false | 0.008387999999999951 | 1 | false |
| agg=fedavg|priv=static-dp@3 | financial-sim→clinical-sim | false | 0.003265999999999991 | 1 | false |
| agg=median|priv=no-dp | clinical-sim→financial-sim | true | 0.0035530000000000284 | 0 | true |
| agg=median|priv=no-dp | financial-sim→clinical-sim | true | 0.009676000000000018 | 0 | true |
| agg=median|priv=static-dp@6 | clinical-sim→financial-sim | false | 0.007703000000000015 | 1 | false |
| agg=median|priv=static-dp@6 | financial-sim→clinical-sim | true | 0.0017280000000000628 | 0 | true |
| agg=median|priv=static-dp@3 | clinical-sim→financial-sim | false | 0.015031999999999934 | 1 | false |
| agg=median|priv=static-dp@3 | financial-sim→clinical-sim | true | 0.006556000000000006 | 0 | false |
| agg=trimmed-mean|priv=no-dp | clinical-sim→financial-sim | false | 0.00007899999999994023 | 1 | true |
| agg=trimmed-mean|priv=no-dp | financial-sim→clinical-sim | false | 0 | 1 | true |
| agg=trimmed-mean|priv=static-dp@6 | clinical-sim→financial-sim | false | 0.00640099999999999 | 2 | false |
| agg=trimmed-mean|priv=static-dp@6 | financial-sim→clinical-sim | false | 0 | 1 | true |
| agg=trimmed-mean|priv=static-dp@3 | clinical-sim→financial-sim | false | 0.009413000000000005 | 1 | false |
| agg=trimmed-mean|priv=static-dp@3 | financial-sim→clinical-sim | false | 0.004098000000000046 | 1 | false |
| agg=trust-weighted|priv=no-dp | clinical-sim→financial-sim | true | 0 | 0 | true |
| agg=trust-weighted|priv=no-dp | financial-sim→clinical-sim | true | 0.0005810000000000537 | 0 | true |
| agg=trust-weighted|priv=static-dp@6 | clinical-sim→financial-sim | false | 0.006172999999999984 | 1 | false |
| agg=trust-weighted|priv=static-dp@6 | financial-sim→clinical-sim | true | 0 | 0 | true |
| agg=trust-weighted|priv=static-dp@3 | clinical-sim→financial-sim | true | 0.008545000000000025 | 0 | false |
| agg=trust-weighted|priv=static-dp@3 | financial-sim→clinical-sim | true | 0.003895000000000093 | 0 | false |
