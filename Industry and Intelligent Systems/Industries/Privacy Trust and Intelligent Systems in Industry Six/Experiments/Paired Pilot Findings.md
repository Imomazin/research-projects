# Paired exploratory pilot

Source GitHub Actions run: https://github.com/Imomazin/research-projects/actions/runs/40363184807

Date: 26 October 2026. Status: two jobs passed, six seed-specific training runs completed, nine design and integrity tests passed, zero failed trials. Unmodified JSON outputs, CSV seed summaries, and failure registries are archived as named GitHub Actions run artefacts: Paired Research steel and Paired Research maintenance.

## Frozen small-pilot parameters

Three paired seeds (11, 23, 37), 800 subsampled source observations per task, 559 training records, 121 validation records and 120 held-out test records; two simulated clients, two federated rounds, Dirichlet concentration 0.5, DP-SGD Gaussian noise multiplier 1.2. Train-only imputing/scaling, disjoint splits, no cryptographic secure aggregation. Opacus reports maximum per-client privacy epsilon between 4.608 and 5.702 for steel, and 4.608 for maintenance, under its recorded delta and Poisson-sampling assumptions. These conditions are pilot settings, not matched operating points for a final privacy–utility frontier.

## Held-out test balanced accuracy averaged over three seeds

| Task | Linear baseline | Pooled neural network | FedAvg neural network | DP-SGD FedAvg |
|---|---:|---:|---:|---:|
| Steel defect classification | 0.719 | 0.216 | 0.161 | 0.133 |
| Maintenance failure classification | 0.542 | 0.500 | 0.500 | 0.500 |

## Held-out test macro F one averaged over three seeds

| Task | Linear baseline | Pooled neural network | FedAvg neural network | DP-SGD FedAvg |
|---|---:|---:|---:|---:|
| Steel defect classification | 0.708 | 0.159 | 0.112 | 0.061 |
| Maintenance failure classification | 0.559 | 0.492 | 0.492 | 0.492 |

For steel, the exploratory 95% t interval for the linear balanced-accuracy mean was 0.595–0.844, while the DP-SGD mean interval was 0.055–0.211. Such intervals reflect variation across only three seeded simulations, may be unstable and should not be interpreted as population confidence intervals or evidence of methodological superiority.

## Implications and required tests

Current neural pilots do not learn sufficient minority-defect and minority-failure signals. Future experiments should test full-data runs, longer learning horizons, class-sensitive loss, validated thresholds, client imbalance, explicit holdout protocols, calibration, privacy attacks, secure aggregation where actually implemented, energy and network cost, device-group holdouts and matched computation. The linear reference should remain mandatory.

These observations do not establish that differential privacy caused the shortfall: the neural baselines are undertrained, the models have unequal training dynamics, and privacy protection is confounded with random seeds and short training schedules. No overall claim about industrial trust, privacy preservation or Industry 6.0 performance should be made from this pilot alone.
