# Table T8 — Cross-domain configuration evidence (mean over 20 seeds)

_utility = clean AUROC; robustness = retained AUROC under sign-flip ×5 @ 20% adversarial._

| Configuration | Domain | Utility | Robustness | ε spent |
|---|---|---|---|---|
| agg=fedavg|priv=no-dp | clinical-sim | 0.801 | 0.428 | 0.00 |
| agg=fedavg|priv=no-dp | financial-sim | 0.736 | 0.455 | 0.00 |
| agg=fedavg|priv=static-dp@6 | clinical-sim | 0.798 | 0.395 | 5.99 |
| agg=fedavg|priv=static-dp@6 | financial-sim | 0.730 | 0.444 | 5.99 |
| agg=fedavg|priv=static-dp@3 | clinical-sim | 0.793 | 0.402 | 3.01 |
| agg=fedavg|priv=static-dp@3 | financial-sim | 0.727 | 0.445 | 3.01 |
| agg=median|priv=no-dp | clinical-sim | 0.787 | 0.749 | 0.00 |
| agg=median|priv=no-dp | financial-sim | 0.732 | 0.723 | 0.00 |
| agg=median|priv=static-dp@6 | clinical-sim | 0.795 | 0.755 | 5.99 |
| agg=median|priv=static-dp@6 | financial-sim | 0.728 | 0.711 | 5.99 |
| agg=median|priv=static-dp@3 | clinical-sim | 0.790 | 0.749 | 3.01 |
| agg=median|priv=static-dp@3 | financial-sim | 0.721 | 0.700 | 3.01 |
| agg=trimmed-mean|priv=no-dp | clinical-sim | 0.798 | 0.548 | 0.00 |
| agg=trimmed-mean|priv=no-dp | financial-sim | 0.736 | 0.623 | 0.00 |
| agg=trimmed-mean|priv=static-dp@6 | clinical-sim | 0.797 | 0.566 | 5.99 |
| agg=trimmed-mean|priv=static-dp@6 | financial-sim | 0.729 | 0.662 | 5.99 |
| agg=trimmed-mean|priv=static-dp@3 | clinical-sim | 0.792 | 0.590 | 3.01 |
| agg=trimmed-mean|priv=static-dp@3 | financial-sim | 0.726 | 0.655 | 3.01 |
| agg=trust-weighted|priv=no-dp | clinical-sim | 0.796 | 0.755 | 0.00 |
| agg=trust-weighted|priv=no-dp | financial-sim | 0.736 | 0.726 | 0.00 |
| agg=trust-weighted|priv=static-dp@6 | clinical-sim | 0.797 | 0.745 | 5.99 |
| agg=trust-weighted|priv=static-dp@6 | financial-sim | 0.730 | 0.710 | 5.99 |
| agg=trust-weighted|priv=static-dp@3 | clinical-sim | 0.793 | 0.747 | 3.01 |
| agg=trust-weighted|priv=static-dp@3 | financial-sim | 0.727 | 0.700 | 3.01 |
