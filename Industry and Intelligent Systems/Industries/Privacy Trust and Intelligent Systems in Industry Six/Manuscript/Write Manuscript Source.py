"""Assemble Manuscript Source.json (text, tables, figures, numbered citations and references)."""
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
AN = HERE.parent / "Experiments" / "Private Risk Control" / "Results" / "Analysis"
FIG = HERE.parent / "Figures"
N = json.loads((HERE / "Manuscript Numbers.json").read_text())


def mod(name):
    spec = importlib.util.spec_from_file_location(name.replace(" ", "_"), HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name.replace(" ", "_")] = m
    spec.loader.exec_module(m)
    return m


REFS = mod("References").REFS
TF, TR, TB = mod("Text Front"), mod("Text Results"), mod("Text Back")
pct, num = TR.pct, TR.num


def read(name):
    p = AN / f"{name}.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


# Sensitivity-derived numbers
S = {}
util = read("Utility")
loc = util[(util.model == "local") & (util.test_set == "test") & (util.metric == "pr_auc") & (util.dataset == "maintenance")]
g = loc.groupby("seed").value.agg(["mean", "min"])
S["local_mean_maint"], S["local_min_maint"] = float(g["mean"].mean()), float(g["min"].mean())
gaps = []
for key, d in N["utility"].items():
    fa, fp = d["fedavg"][0], d["fedprox"][0]
    if fa is None or fp is None:
        continue
    gaps.append(fp - fa if not key.startswith(("power", "gas")) else fa - fp)
S["fedprox_gap_max"] = max(gaps)
ext = util[(util.client.isna()) & (util.model == "fedavg")]
S["unseen_pr_fedavg"] = float(ext[(ext.test_set.str.startswith("unseen machine")) & (ext.metric == "pr_auc")].value.mean())
S["later_pr_fedavg"] = float(ext[(ext.test_set == "later periods") & (ext.metric == "pr_auc")].value.mean())
S["hai_later_pr_fedavg"] = float(ext[(ext.test_set == "later sessions") & (ext.metric == "pr_auc")].value.mean())
S["gas_rmse_2015"] = float(ext[(ext.test_set == "year 2015") & (ext.metric == "rmse")].value.mean())
ece = util[(util.client.isna()) & (util.test_set == "test") & (util.metric == "ece") & (util.model == "fedavg")]
S["ece_fedavg_maint"] = float(ece[ece.dataset == "maintenance"].value.mean())
S["ece_fedavg_secom"] = float(ece[ece.dataset == "semiconductor"].value.mean())
rs = read("Risk Control Summary")
be = rs[(rs.metric == "binning_ece") & (rs.test_set == "test") & (rs.model == "fedavg") & (rs.method == "proposed")]
S["binece_fedavg_maint"] = float(be[be.dataset == "maintenance"]["mean"].iloc[0])
S["binece_fedavg_secom"] = float(be[be.dataset == "semiconductor"]["mean"].iloc[0])
cost = read("Cost Summary")


def c(ds, model, item):
    v = cost[(cost.dataset == ds) & (cost.model == model) & (cost.item == item)]["mean"]
    return float(v.iloc[0]) if len(v) else float("nan")


S["dp_seconds_maint"] = c("maintenance", "dp eps 4", "train_seconds")
S["dp_seconds_iot"] = c("iot", "dp eps 4", "train_seconds")
S["secagg_seconds_maint"] = c("maintenance", "dp eps 4", "secure_aggregation_seconds")
S["secagg_extra_bytes"] = int(c("maintenance", "dp eps 4", "secure_aggregation_bytes") - c("maintenance", "dp eps 4", "parameter_bytes_up"))
S["cal_bytes_maint"] = int(c("maintenance", "dp eps 4", "calibration secure aggregation bytes"))

sens = read("Sensitivity Summary")


def sv(ds, variant, model, method, test, metric):
    g = sens[(sens.dataset == ds) & (sens.variant == variant) & (sens.model == model) & (sens.method.fillna("") == method)
             & (sens.test_set == test) & (sens.metric == metric)]
    return float(g["mean"].iloc[0]) if len(g) else None


if len(sens) and (sens.dataset == "maintenance").any():
    a01 = sv("maintenance", "alpha 0.1", "fedavg", "", "test", "pr_auc")
    a2 = sv("maintenance", "alpha 2.0", "fedavg", "", "test", "pr_auc")
    d01 = sv("maintenance", "alpha 0.1", "dp eps 4", "", "test", "pr_auc")
    d2 = sv("maintenance", "alpha 2.0", "dp eps 4", "", "test", "pr_auc")
    k8 = sv("maintenance", "clients 8", "fedavg", "", "test", "pr_auc")
    k8d = sv("maintenance", "clients 8", "dp eps 4", "", "test", "pr_auc")
    pp = sv("maintenance", "participation 0.5", "fedavg", "", "test", "pr_auc")
    S["alpha_text"] = (f"On AI4I, stronger label skew (Dirichlet 0.1) gave a FedAvg PR-AUC of {num(a01)} and weaker skew (2.0) gave {num(a2)}; the DP model at ε = 4 moved from {num(d01)} to {num(d2)}. Doubling the number of clients to eight gave {num(k8)} for FedAvg and {num(k8d)} at ε = 4, because each DP client then has fewer records to average its noise over, and half participation per round gave {num(pp)}.")
else:
    S["alpha_text"] = "Sensitivity runs for heterogeneity are reported in the workbook."
rec = read("Reconstruction")
if len(rec):
    m = rec[rec.dataset == "maintenance"].set_index("setting")
    S["recon_text"] = (f"Update leakage was severe without protection: from a single-record update the first-layer gradients recovered the AI4I input exactly (median cosine similarity {num(m.loc['no protection','median_cosine'])}, share above 0.99 {pct(m.loc['no protection','share_cosine_above_0_99'],0)}), and clipping alone did not change this (median cosine {num(m.loc['clipping only','median_cosine'])}) because clipping rescales but does not perturb the gradient. Adding Gaussian noise at multiplier 1 reduced the median cosine to {num(m.loc['clip and noise multiplier 1','median_cosine'])}. This is why DP noise is added on the client and why secure aggregation of updates is worth its small cost.")
else:
    S["recon_text"] = ""
sw = read("Calibration Sweep")
if len(sw):
    t = sw[sw.method.isin(["proposed", "nonprivate_ltt"])].groupby(["dataset", "method", "epsilon"])["escalation_rate"].mean()
    def esc(ds, m, e):
        try:
            return float(t.loc[(ds, m, e)])
        except KeyError:
            return None
    S["sweep_text"] = (f"On AI4I the escalation rate under PARC was {pct(esc('maintenance','proposed',8.0))} at ε~C~ = 8, {pct(esc('maintenance','proposed',4.0))} at 4, {pct(esc('maintenance','proposed',2.0))} at 2, {pct(esc('maintenance','proposed',1.0))} at 1 and {pct(esc('maintenance','proposed',0.5))} at 0.5, against {pct(esc('maintenance','nonprivate_ltt',4.0))} for exact Learn-then-Test on the same model. On HAI the corresponding values were {pct(esc('hai','proposed',4.0))} at ε~C~ = 4 and {pct(esc('hai','proposed',1.0))} at 1 against {pct(esc('hai','nonprivate_ltt',4.0))}. Private calibration is therefore nearly free at ε~C~ ≥ 4 and costly at ε~C~ ≤ 1 on federations of this size, in line with the evidence floor.")
else:
    S["sweep_text"] = ""
if len(sens):
    def pr(ds, variant, model, metric="pr_auc", test="test", method=""):
        return sv(ds, variant, model, method, test, metric)
    p_fa = pr("maintenance", "poison", "fedavg")
    p_tr = pr("maintenance", "poison", "trimmed")
    p_md = pr("maintenance", "poison", "median")
    p_dp = pr("maintenance", "poison", "dp eps 4")
    hb = {lvl: sv("maintenance", "histogram poison", "dp eps 4", f"proposed, fake faults {lvl} x n1", "test", "miss_rate") for lvl in ("0.25", "0.5", "1", "2")}
    hbe = {lvl: sv("maintenance", "histogram poison", "dp eps 4", f"proposed, fake faults {lvl} x n1", "test", "escalation_rate") for lvl in ("0.25", "0.5", "1", "2")}
    hbf = {lvl: sv("hai", "histogram poison", "dp eps 4", f"proposed, fake faults {lvl} x n1", "test", "miss_rate") for lvl in ("0.25", "0.5", "1", "2")}
    cg = sv("maintenance", "corruption", "fedavg", "", "gaussian 1", "pr_auc")
    cm = sv("maintenance", "corruption", "fedavg", "", "missing 0.4", "pr_auc")
    cgm = sv("maintenance", "corruption", "fedavg", "proposed", "gaussian 1", "miss_rate")
    cmm = sv("maintenance", "corruption", "fedavg", "proposed", "missing 0.4", "miss_rate")
    ln = sv("maintenance", "label noise", "fedavg", "", "test", "pr_auc")
    S["attack_text"] = (f"A single malicious AI4I client sending a scaled sign-flipped update reduced FedAvg to a PR-AUC of {num(p_fa)}; coordinate-wise median and trimmed-mean aggregation gave {num(p_md)} and {num(p_tr)}, and DP-FedAvg with secure aggregation, which cannot screen updates, gave {num(p_dp)}. Fabricated high-score faults in one client's calibration counts inflate the denominator of the miss rate; on AI4I at ε = 4 the realised miss rate under PARC was {pct(hb['0.25'])}, {pct(hb['0.5'])}, {pct(hb['1'])} and {pct(hb['2'])} for fabricated counts of 0.25, 0.5, 1 and 2 times the true number of calibration faults, while escalation fell to {pct(hbe['2'])} at the largest level. Test-time sensor corruption reduced FedAvg PR-AUC to {num(cg)} with Gaussian noise of one standard deviation and {num(cm)} with 40 per cent missing values, with realised miss rates under PARC of {pct(cgm)} and {pct(cmm)}. Flipping 30 per cent of one client's labels gave a PR-AUC of {num(ln)} («F:robustness» and «T:robustness»).")
    S["discussion_attack_text"] = (f"One malicious client cut FedAvg PR-AUC on AI4I from {num(N['utility']['maintenance|simulated']['fedavg'][0])} to {num(p_fa)}, and fabricated calibration counts raised the realised miss rate under PARC to {pct(hb['2'])} at the largest level tested, so the certificate holds only if clients report honest counts.")
else:
    S["attack_text"] = S["discussion_attack_text"] = ""

# Tables
TABLES = {}
TABLES["novelty"] = {"caption": "**Table {n}.** Closest methods and the features of this study. DP: differential privacy; SecAgg: secure aggregation.",
    "header": ["Study", "Setting", "Privacy and who adds noise", "Guarantee", "Risks controlled", "Industrial data"],
    "widths": [2.2, 1.6, 2.2, 1.6, 1.6, 1.2],
    "rows": [["Angelopoulos et al. {angelopoulos2022private}", "Central", "DP quantile, trusted curator", "Coverage, noise-corrected", "Miscoverage", "No"],
             ["Romanus and Molinari {romanus2026}; Wu et al. {wu2026}", "Central", "DP quantile or DP training, trusted curator", "Approximate or conditional coverage", "Miscoverage", "No"],
             ["Penso et al. {penso2025}", "Local users", "Local DP on labels or scores", "Finite-sample coverage", "Miscoverage", "No"],
             ["Lu et al. {lu2023}", "Federated", "None", "Coverage under partial exchangeability", "Miscoverage", "No"],
             ["Humbert et al. {humbert2023}", "Federated, one round", "Local DP variant", "Coverage", "Miscoverage", "No"],
             ["Plassier et al. {plassier2023}", "Federated, label shift", "Client Gaussian on gradients; no SecAgg", "Approximate coverage", "Miscoverage", "No"],
             ["Maddock et al. {maddock2025}", "Federated calibration", "SecAgg plus server-added Gaussian; user-level", "Calibration error", "None (ECE)", "No"],
             ["Lari et al. {lari2026}", "Federated, Byzantine", "None (histograms in clear)", "Coverage under attack", "Miscoverage", "No"],
             ["Talpini et al. {talpini2025}", "Federated IDS calibration", "None formal", "Empirical", "None", "Intrusion data"],
             ["Padmavathi and Saminathan {padmavathi2025}; Kamali Poorazad et al. {kamali2025}", "Federated IoT/IIoT detection", "DP without accounting; homomorphic encryption", "None for decisions", "None", "Yes"],
             ["This study (PARC)", "Federated, cross-site", "Client-side Skellam under SecAgg; record-level; exact accounting", "Finite-sample PAC bound including noise", "Miss and false-alarm rates; selective error; interval exceedance", "Yes: 8 tasks, 3 machines, ICS sessions"]]}
reg = pd.read_csv(HERE.parent / "Datasets" / "Source Register.csv")
reg = reg[reg["Observations"].notna()]
TABLES["datasets"] = {"caption": "**Table {n}.** Datasets, provenance and evaluation designs. All licences permit research use with attribution.",
    "header": ["Task", "Source and licence", "Records", "Features", "Target", "Evidence", "Clients and test designs"],
    "widths": [1.5, 2.1, 0.9, 0.8, 1.6, 1.5, 2.4],
    "rows": [[r["Dataset"], f"{r['Identifier']}; {r['Licence']}", f"{int(r['Observations']):,}", str(int(r["Attributes"])),
              r["Outcome"].split(";")[0], r["Observed or synthetic"], r["Supported evaluation scenarios"]] for _, r in reg.iterrows()]}
TABLES["settings"] = {"caption": "**Table {n}.** Fixed experimental settings (frozen before confirmatory runs).",
    "header": ["Component", "Setting"], "widths": [1.5, 5],
    "rows": [["Roles", "Independent per-record coin flips: training 0.6, calibration 0.2, test 0.2"],
             ["Clients", "4 simulated (Dirichlet 0.5) where no natural identity; Bosch machines (3 or 2); HAI sessions (3)"],
             ["Model", "Perceptron 64-32, ReLU; 25 rounds × 2 local epochs; batch 64 (RT-IoT 256); size-weighted averaging"],
             ["Baselines", "Reference, linear, pooled network, local-only, FedAvg, FedProx, SCAFFOLD, median, trimmed mean, DP-FedAvg"],
             ["DP-SGD", "Poisson sampling, per-example clip C = 1, Gaussian noise, RDP accountant; ε ∈ {1, 2, 4, 8}, δ = 10^-5^"],
             ["Secure aggregation", "X25519, HKDF-SHA256, ChaCha20 masks, 32-bit modular sums; no dropout recovery"],
             ["Calibration", "26 logit-spaced bins; Skellam noise with exact privacy profile; ε~C~ = ε of the model (4 for FedAvg)"],
             ["Targets", "α~miss~ = 0.10, α~fa~ = 0.05, selective α = 0.10, interval α = 0.10; δ~test~ = 0.04, δ~count~ = 0.01 per side"],
             ["Seeds", "1 to 10 (RT-IoT 1 to 5); tuning seed 0; sensitivity seeds 1 to 5"]]}
order = [("maintenance|simulated", "AI4I (PR-AUC)"), ("semiconductor|simulated", "SECOM (PR-AUC)"), ("steel|simulated", "Steel (macro F1)"),
         ("power|simulated", "Power (RMSE, MW)"), ("gas|simulated", "Gas NOx (RMSE, mg/m^3^)"), ("iot|simulated", "RT-IoT (PR-AUC)"),
         ("bosch|machines", "Bosch machines (PR-AUC)"), ("bosch|time holdout", "Bosch early periods (PR-AUC)"),
         ("bosch|machine holdout", "Bosch two machines (PR-AUC)"), ("hai|sessions", "HAI sessions (PR-AUC)")]
cols = ["reference", "linear", "central", "fedavg", "fedprox", "scaffold", "median", "dp eps 8", "dp eps 4", "dp eps 1"]
names = ["Ref.", "Linear", "Pooled", "FedAvg", "FedProx", "SCAFFOLD", "Median", "DP ε=8", "DP ε=4", "DP ε=1"]
dec = 2
TABLES["utility"] = {"caption": "**Table {n}.** Held-out utility by method (mean over seeds; 95% bootstrap intervals in the workbook). Higher is better except RMSE.",
    "header": ["Task"] + names, "widths": [2.2] + [0.8] * len(cols),
    "rows": [[lab] + [num(N["utility"][k][m][0], 2 if k.startswith(("power", "gas")) else 3) for m in cols] for k, lab in order]}
pv = N["privacy"]
TABLES["privacy"] = {"caption": "**Table {n}.** Privacy accounting (record level, δ = 10^-5^; ranges over clients and runs).",
    "header": ["Target ε", "Max training ε", "Skellam μ", "ε~C~ with SecAgg", "ε~C~ without SecAgg", "Pipeline ε", "Sequential ε (δ = 2×10^-5^)"],
    "widths": [1, 1.2, 1, 1.2, 1.3, 1, 1.5],
    "rows": [[str(e), num(pv[f"dp eps {e}"]["epsilon_training_max"][1]), num(pv[f"dp eps {e}"]["skellam_mu_total"][0], 3),
              num(pv[f"dp eps {e}"]["epsilon_calibration_secure_sum"][1], 2),
              f"{num(pv[f'dp eps {e}']['epsilon_calibration_without_secure_aggregation'][0],2)} to {num(pv[f'dp eps {e}']['epsilon_calibration_without_secure_aggregation'][1],2)}",
              num(pv[f"dp eps {e}"]["epsilon_total_parallel"][1], 2), num(pv[f"dp eps {e}"]["epsilon_total_sequential_worst_client"][1], 2)]
             for e in (1, 2, 4, 8)]}
D = N["decisions"]
meth = [("default", "Default 0.5"), ("nonprivate_plugin", "Plug-in, exact"), ("nonprivate_ltt", "LTT, exact"),
        ("plugin", "Plug-in, private"), ("ucb_without_noise", "Binomial, no noise term"), ("proposed", "PARC")]
rows = []
for key, lab in [("maintenance|simulated", "AI4I"), ("hai|sessions", "HAI"), ("bosch|machines", "Bosch"), ("iot|simulated", "RT-IoT")]:
    for model, mlab in [("fedavg", "FedAvg"), ("dp eps 4", "DP ε=4")]:
        row = [f"{lab}, {mlab}"]
        for m, _ in meth:
            mi = D.get(f"{key}|{model}|{m}|miss_rate")
            es = D.get(f"{key}|{model}|{m}|escalation_rate")
            row.append(f"{pct(mi,1)} / {pct(es,0)}")
        rows.append(row)
TABLES["decisions"] = {"caption": "**Table {n}.** Realised miss rate / escalation rate on held-out records by certification rule (target miss rate 10%; calibration ε = 4).",
    "header": ["Task and model"] + [b for _, b in meth], "widths": [1.6] + [1.1] * 6, "rows": rows}
TABLES["floor"] = {"caption": "**Table {n}.** Evidence floor: smallest calibration count at which any automatic region can be certified (exact computation; δ~test~ = 0.04, δ~count~ = 0.01).",
    "header": ["Target", "Non-private", "ε = 8", "ε = 4", "ε = 2", "ε = 1", "ε = 0.5"], "widths": [2] + [1] * 6,
    "rows": [[t] + [str(N["floor"][f"{t}|{e}"]) for e in ("non-private", "8", "4", "2", "1", "0.5")]
             for t in ("miss rate 0.10", "false-alarm rate 0.05", "miss rate 0.20")]}
h = N["hyp"]
TABLES["tests"] = {"caption": "**Table {n}.** Pre-specified confirmatory tests (Holm adjustment across H2 to H4).",
    "header": ["Hypothesis", "Evidence", "Test", "Result"], "widths": [2, 3, 2, 1.6],
    "rows": [["H1 validity with known distributions", f"Worst PARC violation {pct(N.get('mc_proposed_max_miss_violation'))} (miss), {pct(N.get('mc_proposed_max_fa_violation'))} (false alarm); plug-in up to {pct(N.get('mc_plugin_max_miss_violation'))}", f"{N.get('mc_rows')} Monte Carlo conditions × 1,000", "Supported"],
             ["H2 fewer exceedances than private plug-in", f"{h['H2']['proposed_exceedances']} vs {h['H2']['plugin_exceedances']} of {h['H2']['runs']} runs", f"Exact McNemar, adjusted p = {h['holm_adjusted']['H2']:.1e}", "Supported"],
             ["H3 extra escalation < 5 points at ε = 4", f"Mean {h['H3']['mean_difference']*100:.2f} points (95% CI {h['H3']['ci_low']*100:.2f} to {h['H3']['ci_high']*100:.2f})", "Bootstrap against margin", "Supported; uninformative (both near full escalation)"],
             ["H4 higher risk under shift", f"Mean rise {h['H4']['mean_difference']*100:.1f} points (95% CI {h['H4']['ci_low']*100:.1f} to {h['H4']['ci_high']*100:.1f}); carried by gas", f"Wilcoxon, adjusted p = {h['holm_adjusted']['H4']:.1e}", "Supported for gas; untested where all faults escalated"]]}
TABLES["costs"] = {"caption": "**Table {n}.** Computation and communication per training run (mean over seeds; one CPU core; in-process measurement).",
    "header": ["Task", "FedAvg s", "DP ε=4 s", "SecAgg s", "Model bytes up", "SecAgg key bytes", "Calibration bytes"],
    "widths": [1.8, 0.9, 0.9, 0.9, 1.4, 1.2, 1.2],
    "rows": [[lab, num(c(k.split("|")[0], "fedavg", "train_seconds"), 2), num(c(k.split("|")[0], "dp eps 4", "train_seconds"), 2),
              num(c(k.split("|")[0], "dp eps 4", "secure_aggregation_seconds"), 3),
              f"{int(c(k.split('|')[0], 'dp eps 4', 'parameter_bytes_up')):,}",
              f"{int(c(k.split('|')[0], 'dp eps 4', 'secure_aggregation_bytes') - c(k.split('|')[0], 'dp eps 4', 'parameter_bytes_up')):,}",
              f"{int(c(k.split('|')[0], 'dp eps 4', 'calibration secure aggregation bytes')):,}"]
             for k, lab in [("maintenance|simulated", "AI4I"), ("semiconductor|simulated", "SECOM"), ("steel|simulated", "Steel"),
                            ("power|simulated", "Power"), ("gas|simulated", "Gas"), ("iot|simulated", "RT-IoT"),
                            ("hai|sessions", "HAI")]]}
# robustness table from sensitivity summary
rrows = []
if len(sens):
    spec = [("maintenance", "alpha 0.1", "Dirichlet 0.1"), ("maintenance", "alpha 2.0", "Dirichlet 2.0"),
            ("maintenance", "clients 8", "Eight clients"), ("maintenance", "participation 0.5", "Half participation"),
            ("maintenance", "label noise", "30% labels flipped at one client"), ("maintenance", "poison", "One malicious client"),
            ("maintenance", "bins 13", "13 bins"), ("maintenance", "bins 51", "51 bins"),
            ("bosch", "poison", "Bosch: one malicious machine"), ("hai", "poison", "HAI: one malicious session")]
    for ds, var, lab in spec:
        row = [lab]
        for model in ("fedavg", "trimmed", "median", "dp eps 4"):
            row.append(num(sv(ds, var, model, "", "test", "pr_auc")))
        row.append(pct(sv(ds, var, "fedavg", "proposed", "test", "miss_rate")))
        row.append(pct(sv(ds, var, "fedavg", "proposed", "test", "escalation_rate"), 0))
        rrows.append(row)
TABLES["robustness"] = {"caption": "**Table {n}.** Sensitivity and attack experiments (seeds 1 to 5; PR-AUC on held-out records; PARC outcomes for FedAvg at calibration ε = 4).",
    "header": ["Condition", "FedAvg", "Trimmed", "Median", "DP ε=4", "PARC miss", "PARC escalated"],
    "widths": [2.6, 0.9, 0.9, 0.9, 0.9, 1, 1.1], "rows": rrows}
TABLES["implications"] = {"caption": "**Table {n}.** Operational implications and their limits.",
    "header": ["Finding", "Decision for operators", "Owner", "Limit of the evidence"], "widths": [2.3, 2.6, 1.2, 2.2],
    "rows": [["Certification needs ≥31 faults (10% target) without privacy, 36 at ε = 4, 118 at ε = 1", "Count calibration events per target before setting ε; pool calibration across sites", "Data governance lead", "Floors assume the stated δ and a 26-bin grid"],
             ["Plug-in thresholds exceed targets in about one run in eight", "Use certified thresholds for any automated stop or pass", "Reliability engineering", "Measured on eight public tasks"],
             ["DP training at ε ≤ 4 erodes rare-fault ranking", "Spend privacy on calibration first; test ranking at the chosen ε before deployment", "Model owner", "Small networks; tuning not privatised"],
             ["Drift breaks interval coverage (gas 2014 and 2015)", "Date certificates; recalibrate and retrain on schedule; monitor realised error", "Operations manager", "One turbine"],
             ["Secure aggregation hides counts and updates from the server", "Require client-side noise and bounded contributions; audit client software", "Security team", "No range proofs implemented"],
             ["Escalation carries most decisions for rare faults", "Staff the review queue; record overrides for audit", "Plant management", "Human review quality not measured"]]}

FIGS = {"framework": ("Research Framework.png", "Research framework. Solid links were measured in this study; dashed links are proposed."),
        "architecture": ("Architecture and Protocol.png", "Private aggregate risk control. Clients train with DP-SGD and release Skellam-noised histograms of calibration scores through pairwise-mask secure summation; the server certifies thresholds with a noise-aware fixed-sequence test, and sites route scores between the thresholds to people."),
        "privacy_utility": ("Privacy Utility.png", "Utility of DP-FedAvg by privacy budget (mean and 95% bootstrap interval over seeds) against FedAvg (dashed) and the pooled network (dotted)."),
        "models": ("Model Comparison.png", "Held-out utility of all methods by task (mean and 95% bootstrap interval)."),
        "ablation": ("Ablation of Certification Rules.png", "Realised miss rate, false-alarm rate and escalation by certification rule for FedAvg models across the seven binary designs (points are runs; bars are means; percentages are the share of runs above target)."),
        "shift": ("Shift and Unseen Machines.png", "Realised risk under PARC in period and under shift (FedAvg; dashed line marks the 10% target)."),
        "robustness": ("Robustness Under Attack and Corruption.png", "Sensitivity analyses, means over seeds 1 to 5. (a) Label skew on AI4I. (b) PR-AUC with and without one client sending a scaled sign-flipped update. (c) Realised miss rate under PARC when one client fabricates high-score faults in its calibration counts. (d) FedAvg PR-AUC under Gaussian sensor noise and missing values at test time."),
        "reliability": ("Guarantee Validity and Evidence Floor.png", "Left: worst miss-rate violation rate of each rule across Monte Carlo conditions (dashed line at the 5 per cent per-side allowance). Centre: minimum calibration events needed to certify each target, by calibration budget (log scale). Right: share of decisions automated by PARC on the non-private FedAvg model as the calibration budget varies (seeds 1 to 5).")}

# Assemble
blocks = [{"type": "title", "text": "Privacy, Trust & Intelligent Systems in Industry 6.0"},
          {"type": "meta", "text": "Imo Enang"},
          {"type": "meta", "text": "Department of Electrical Engineering and Computer Science, Florida Atlantic University, Boca Raton, FL 33431, USA; imowo.enang@gmail.com"}]
h = N["hyp"]
abstract = (f"Industrial sites want to learn from each other's data without disclosing it and to automate decisions only where errors stay within stated limits. Private federated detectors report accuracy and privacy budgets but give no certified bound on the decisions that follow. We propose private aggregate risk control (PARC): sites train a model with differentially private federated averaging, add Skellam noise to histograms of calibration scores and combine them by secure aggregation, and the server certifies automatic-pass and automatic-alarm thresholds with a binomial-Skellam test. We prove finite-sample validity under the privacy noise and derive the minimum calibration evidence that certification needs. On eight industrial and security tasks ({N['n_units']:,} observations; {N['main_runs']} confirmatory runs) PARC exceeded a 10% miss-rate target in {h['H2']['proposed_exceedances']} of {h['H2']['runs']} runs against {h['H2']['plugin_exceedances']} for a private plug-in rule. Private calibration was nearly free at ε ≥ 4, but a 10% miss-rate certificate needed at least {N['floor']['miss rate 0.10|non-private']} calibration faults without privacy and {N['floor']['miss rate 0.10|1']} at ε = 1. DP training cut rare-fault PR-AUC on AI4I from {num(N['utility']['maintenance|simulated']['fedavg'][0])} to {num(N['utility']['maintenance|simulated']['dp eps 4'][0])} at ε = 4 and drift broke interval coverage on a gas turbine. Operators should count failure evidence before choosing privacy budgets and treat escalation as the channel for human oversight.")
blocks.append({"type": "h1", "text": "Abstract"})
blocks.append({"type": "p", "text": abstract})
blocks.append({"type": "p", "text": "**Keywords:** privacy-preserving deep learning; federated learning; differential privacy; secure aggregation; conformal risk control; trustworthy AI; industrial fault detection; Industry 6.0"})
blocks += TF.front(N) + TR.results(N, S) + TR.discussion(N, S) + TB.declarations(N)
app = TB.appendices(N)
# Appendix C (extended utility with intervals) and D (hyperparameters)
tuned = json.loads((HERE.parent / "Experiments" / "Private Risk Control" / "Tuned Hyperparameters.json").read_text())
ext_rows = []
for k, lab in order:
    for m in ["fedavg", "dp eps 4", "dp eps 1"]:
        v = N["utility"][k][m]
        ext_rows.append([lab, {"fedavg": "FedAvg", "dp eps 4": "DP-FedAvg, ε = 4", "dp eps 1": "DP-FedAvg, ε = 1"}[m], num(v[0]), f"{num(v[1])} to {num(v[2])}"])
app_c = [{"type": "h1", "text": "Appendix C. Extended Results"},
         {"type": "p", "text": "The analysis workbook holds every run, every metric and every summary used in the text. «T:extended» gives intervals for the main utility comparisons."},
         {"type": "table_ref", "id": "extended"},
         {"type": "h1", "text": "Appendix D. Selected Hyperparameters"},
         {"type": "p", "text": "Learning rates were chosen from {0.01, 0.03, 0.1, 0.3} (DP: {0.03, 0.1, 0.3, 1.0} with batch {64, 256} or {256, 1024} for RT-IoT, momentum {0.5, 0.9} and class weight {1, public}) on tuning seed 0 using validation PR-AUC, macro F1 or RMSE («T:hyper»)."},
         {"type": "table_ref", "id": "hyper"},
         {"type": "h1", "text": "Appendix E. Dataset Provenance"},
         {"type": "p", "text": "Datasets/Source Register.csv in the repository records for every source the identifier, organisation, citation and DOI, acquisition date, version or commit, licence, redistribution terms, observed or synthetic status, counts, missing share, class distribution, natural clients, temporal information, supported designs, limitations, SHA-256 checksums and validation outcome. Six further candidates are listed with the reason they were not acquired."}]
TABLES["extended"] = {"caption": "**Table {n}.** Utility with 95% bootstrap intervals over seeds.", "header": ["Task", "Model", "Mean", "95% interval"],
                      "widths": [2.5, 1.2, 1, 1.6], "rows": ext_rows}
hrows = []
for ds, d in tuned.items():
    dp = d["dp"]
    DSN = {"maintenance": "AI4I", "semiconductor": "SECOM", "steel": "Steel plates", "power": "Power plant", "gas": "Gas turbine",
           "iot": "RT-IoT2022", "bosch": "Bosch CNC", "hai": "HAI"}
    hrows.append([DSN.get(ds, ds), str(d["fedavg"]["lr"]), f"{d['fedprox']['lr']} (μ {d['fedprox'].get('mu')})", str(d["scaffold"]["lr"]),
                  str(d["central"]["lr"]), f"lr {dp['lr']}, batch {dp.get('batch')}, momentum {dp.get('momentum')}, class weight {dp.get('pos_weight'):g}"])
TABLES["hyper"] = {"caption": "**Table {n}.** Selected hyperparameters.", "header": ["Task", "FedAvg lr", "FedProx", "SCAFFOLD lr", "Pooled lr", "DP-FedAvg"],
                   "widths": [1.3, 0.9, 1.3, 1, 0.9, 3], "rows": hrows}
blocks += app[:app.index(next(b for b in app if b.get("text") == "Appendix F. Reproducibility"))] + app_c + \
    app[app.index(next(b for b in app if b.get("text") == "Appendix F. Reproducibility")):]

# Number tables and figures by first appearance of their reference blocks
tnum, fnum = {}, {}
for b in blocks:
    if b["type"] == "table_ref" and b["id"] not in tnum:
        tnum[b["id"]] = len(tnum) + 1
    if b["type"] == "figure_ref" and b["id"] not in fnum:
        fnum[b["id"]] = len(fnum) + 1
for tok in re.findall(r"\{T:([a-z_]+)\}", json.dumps(blocks)) + re.findall(r"\{F:([a-z_]+)\}", json.dumps(blocks)):
    pass


def subst(text):
    text = text.replace(", and ", " and ")
    text = re.sub(r"«T:([a-z_]+)»", lambda m: f"Table {tnum[m.group(1)]}", text)
    text = re.sub(r"«F:([a-z_]+)»", lambda m: f"Figure {fnum[m.group(1)]}", text)
    return text


# Citation numbering by first appearance
order_refs = []


def cite(text):
    def rep(m):
        keys = [k.strip() for k in m.group(1).split(",")]
        if not all(k in REFS for k in keys):
            if any(k in REFS for k in keys):
                raise KeyError(keys)
            return m.group(0)
        nums = []
        for k in keys:
            if k not in REFS:
                raise KeyError(k)
            if k not in order_refs:
                order_refs.append(k)
            nums.append(order_refs.index(k) + 1)
        nums = sorted(set(nums))
        parts, start = [], nums[0]
        prev = start
        for n in nums[1:] + [None]:
            if n is not None and n == prev + 1:
                prev = n
                continue
            parts.append(f"{start}" if start == prev else (f"{start},{prev}" if prev == start + 1 else f"{start}–{prev}"))
            if n is not None:
                start = prev = n
        return "[" + ",".join(parts) + "]"
    return re.sub(r"\{([a-z][a-z0-9]*(?:\s*,\s*[a-z][a-z0-9]*)*)\}", rep, text)


out = []
for b in blocks:
    if b["type"] == "table_ref":
        t = TABLES[b["id"]]
        out.append({"type": "table", "caption": cite(subst(t["caption"].replace("{n}", str(tnum[b["id"]])))),
                    "header": [cite(subst(x)) for x in t["header"]], "widths": t["widths"],
                    "rows": [[cite(subst(str(x))) for x in r] for r in t["rows"]]})
    elif b["type"] == "figure_ref":
        path, cap = FIGS[b["id"]]
        if not (FIG / path).exists():
            raise FileNotFoundError(path)
        out.append({"type": "figure", "path": f"../Figures/{path}", "alt": cap[:120],
                    "caption": cite(subst(f"**Figure {fnum[b['id']]}.** {cap}"))})
    elif "text" in b:
        out.append({**b, "text": cite(subst(b["text"]))})
    else:
        out.append(b)
out.append({"type": "h1", "text": "References"})
out.append({"type": "refs", "items": [REFS[k] for k in order_refs]})
unused = sorted(set(REFS) - set(order_refs))
(HERE / "Manuscript Source.json").write_text(json.dumps({"title": "Privacy, Trust & Intelligent Systems in Industry 6.0",
                                                         "blocks": out}, indent=1, ensure_ascii=False))
words = sum(len(b.get("text", "").split()) for b in out if b["type"] in ("p",))
print("blocks", len(out), "references cited", len(order_refs), "unused", unused, "body words", words)
