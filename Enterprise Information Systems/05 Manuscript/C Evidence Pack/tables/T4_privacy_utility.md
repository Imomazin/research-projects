# Table T4 — Privacy–utility (moderate non-IID, mean AUROC ± 95% CI, realized epsilon spent)

_Adaptive-DP uses conservative basic composition; at small nominal budgets over many rounds it becomes infeasible and the realized epsilon overshoots the nominal budget (see epsilon spent). Reported as a negative/limitation result._

| Domain | Config | Mean AUROC | 95% CI | Mean ε spent |
|---|---|---|---|---|
| clinical-sim | no-dp@0 | 0.801 | [0.791, 0.810] | 0.00 |
| clinical-sim | static-dp@1 | 0.760 | [0.729, 0.790] | 1.03 |
| clinical-sim | static-dp@3 | 0.793 | [0.777, 0.810] | 3.01 |
| clinical-sim | static-dp@6 | 0.798 | [0.785, 0.812] | 5.99 |
| clinical-sim | static-dp@10 | 0.800 | [0.788, 0.812] | 10.00 |
| clinical-sim | adaptive-dp@1 | 0.760 | [0.729, 0.790] | 7.63 |
| clinical-sim | adaptive-dp@6 | 0.760 | [0.730, 0.790] | 8.00 |
| clinical-sim | adaptive-dp@10 | 0.761 | [0.730, 0.792] | 10.47 |
| financial-sim | no-dp@0 | 0.736 | [0.728, 0.744] | 0.00 |
| financial-sim | static-dp@1 | 0.710 | [0.700, 0.721] | 1.03 |
| financial-sim | static-dp@3 | 0.727 | [0.719, 0.735] | 3.01 |
| financial-sim | static-dp@6 | 0.730 | [0.722, 0.737] | 5.99 |
| financial-sim | static-dp@10 | 0.730 | [0.722, 0.738] | 10.00 |
| financial-sim | adaptive-dp@1 | 0.710 | [0.700, 0.721] | 7.63 |
| financial-sim | adaptive-dp@6 | 0.711 | [0.700, 0.721] | 8.00 |
| financial-sim | adaptive-dp@10 | 0.709 | [0.699, 0.720] | 10.47 |
