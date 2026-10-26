"""Unit, integration and research-validity tests for the private risk control study.

Run from this folder:  python "Test Private Risk Control.py" -v
"""
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("private_risk_control", HERE / "Private Risk Control Library.py")
L = importlib.util.module_from_spec(spec)
sys.modules["private_risk_control"] = L
spec.loader.exec_module(L)


class DataIntegrity(unittest.TestCase):
    def test_row_counts_and_targets(self):
        expected = {"maintenance": (10000, 339), "semiconductor": (1567, 104), "bosch": (1702, 70),
                    "hai": (13400, 330), "iot": (123117, None), "power": (9568, None),
                    "gas": (36733, None), "steel": (1941, None)}
        for name, (rows, positives) in expected.items():
            task = L.load_task(name)
            self.assertEqual(len(task.y), rows, name)
            self.assertEqual(len(task.X), rows, name)
            if positives is not None:
                self.assertEqual(int(task.y.sum()), positives, name)

    def test_no_target_leakage_columns(self):
        m = L.load_task("maintenance")
        for col in ["Machine failure", "TWF", "HDF", "PWF", "OSF", "RNF", "UDI", "Product ID"]:
            self.assertNotIn(col, m.X.columns)
        iot = L.load_task("iot")
        self.assertFalse(any("Attack_type" in c for c in iot.X.columns))
        hai = L.load_task("hai")
        for col in ["Attack", "Attack Seconds", "Event ID", "Event First Second", "Session", "Window Index"]:
            self.assertNotIn(col, hai.X.columns)
        self.assertFalse(any(c.startswith("attack") for c in hai.X.columns))
        gas = L.load_task("gas")
        self.assertNotIn("NOX", gas.X.columns)
        self.assertNotIn("CO", gas.X.columns)
        bosch = L.load_task("bosch")
        for col in ["Anomaly", "Condition", "Machine", "Samples", "Source SHA", "Source File"]:
            self.assertNotIn(col, bosch.X.columns)

    def test_steel_mapping_matches_uci_counts(self):
        task = L.load_task("steel")
        counts = {n: int((task.y == i).sum()) for i, n in enumerate(task.class_names)}
        self.assertEqual(counts, L.STEEL_PUBLIC_COUNTS)

    def test_hashes_match_audits(self):
        audit = json.loads((L.DATA / "HAI Industrial Control" / "HAI Acquisition Audit.json").read_text())
        self.assertEqual(L.sha256_file(L.DATA / "HAI Industrial Control" / "HAI Window Features.csv.gz"),
                         audit["derived_table_sha256"])
        bosch = json.loads((L.DATA / "Bosch CNC" / "Bosch CNC Acquisition Audit.json").read_text())
        self.assertEqual(L.sha256_file(L.DATA / "Bosch CNC" / "Bosch CNC Derived Features.csv"),
                         bosch["feature_table_sha256"])


class Partitions(unittest.TestCase):
    def test_roles_disjoint_and_complete(self):
        task = L.load_task("maintenance")
        prep = L.prepare(task, 3, "simulated")
        rows = []
        for c in prep.clients:
            r = c["rows"]
            self.assertFalse(set(r["train"]) & set(r["cal"]))
            self.assertFalse(set(r["train"]) & set(r["test"]))
            self.assertFalse(set(r["cal"]) & set(r["test"]))
            rows += [*r["train"], *r["cal"], *r["test"]]
        self.assertEqual(len(rows), len(set(rows)))
        self.assertEqual(len(rows), len(task.y))

    def test_scaler_uses_training_rows_only(self):
        task = L.load_task("power")
        a = L.prepare(task, 5, "simulated")
        test_rows = np.concatenate([c["rows"]["test"] for c in a.clients])
        task.X.iloc[test_rows, 0] = task.X.iloc[test_rows, 0] + 1e6
        b = L.prepare(task, 5, "simulated")
        np.testing.assert_allclose(a.scaler["median"], b.scaler["median"])
        np.testing.assert_allclose(a.scaler["scale"], b.scaler["scale"])

    def test_gas_years_held_out(self):
        task = L.load_task("gas")
        prep = L.prepare(task, 2, "simulated")
        used = np.concatenate([np.concatenate([c["rows"]["train"], c["rows"]["cal"], c["rows"]["test"]])
                               for c in prep.clients])
        self.assertTrue(np.all(task.periods[used] <= 2013))
        self.assertTrue(np.all(task.periods[prep.extra_tests["year 2015"][2]] == 2015))

    def test_machine_holdout_excludes_unseen_machine(self):
        task = L.load_task("bosch")
        for seed in (1, 2, 3):
            prep = L.prepare(task, seed, "machine holdout")
            label = [k for k in prep.extra_tests][0]
            unseen = label.split()[-1]
            rows = np.concatenate([np.concatenate([c["rows"]["train"], c["rows"]["cal"]]) for c in prep.clients])
            self.assertNotIn(unseen, set(task.natural_clients[rows]))

    def test_hai_sessions_chronological(self):
        task = L.load_task("hai")
        prep = L.prepare(task, 1, "sessions")
        rows = np.concatenate([np.concatenate([c["rows"]["train"], c["rows"]["cal"]]) for c in prep.clients])
        self.assertTrue(set(task.sessions[rows]) <= {"test1", "test2", "test3"})
        later = prep.extra_tests["later sessions"][2]
        self.assertTrue(set(task.sessions[later]) == {"test4", "test5"})


class Gradients(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(0)
        self.X = self.rng.normal(size=(7, 5)).astype(np.float32)

    def test_batch_gradient_matches_finite_differences(self):
        for kind, y, out in [("binary", (self.rng.random(7) < .5).astype(int), 1),
                             ("multiclass", self.rng.integers(0, 3, 7), 3),
                             ("regression", self.rng.normal(size=7).astype(np.float32), 1)]:
            m = L.MLP(5, out, (6, 4), np.random.default_rng(1))
            params = [p.astype(np.float64) for p in m.params]
            w = np.ones(7)
            g = L.batch_gradient(params, self.X.astype(np.float64), y, kind, w)
            eps = 1e-6
            for i in (0, 2, 4):
                idx = (1, min(1, params[i].shape[1] - 1))
                plus = [p.copy() for p in params]
                minus = [p.copy() for p in params]
                plus[i][idx] += eps
                minus[i][idx] -= eps
                num = (L.per_example_loss(plus, self.X.astype(np.float64), y, kind).mean()
                       - L.per_example_loss(minus, self.X.astype(np.float64), y, kind).mean()) / (2 * eps)
                self.assertAlmostEqual(float(g[i][idx]), float(num), places=5)

    def test_per_example_norms_and_clipping(self):
        m = L.MLP(5, 1, (6, 4), np.random.default_rng(2))
        y = np.array([0, 1, 1, 0, 1, 0, 0])
        w = np.ones(7, dtype=np.float32)
        explicit = []
        for i in range(7):
            g = L.batch_gradient(m.params, self.X[i:i + 1], y[i:i + 1], "binary", w[i:i + 1])
            explicit.append(math.sqrt(sum(float(np.square(x).sum()) for x in g)))
        _, norms = L.clipped_noisy_gradient(m.params, self.X, y, "binary", w, clip=1e9, sigma=0.0,
                                            expected_batch=1.0, rng=self.rng)
        np.testing.assert_allclose(norms, explicit, rtol=1e-4)
        clipped, _ = L.clipped_noisy_gradient(m.params, self.X, y, "binary", w, clip=0.01, sigma=0.0,
                                              expected_batch=1.0, rng=self.rng)
        total = math.sqrt(sum(float(np.square(x).sum()) for x in clipped))
        self.assertLessEqual(total, 7 * 0.01 + 1e-6)

    def test_noise_scale(self):
        m = L.MLP(5, 1, (6, 4), np.random.default_rng(2))
        Xe, ye = self.X[:0], np.zeros(0, dtype=int)
        draws = [np.concatenate([g.ravel() for g in L.clipped_noisy_gradient(
            m.params, Xe, ye, "binary", np.ones(0, np.float32), 1.0, 2.0, 10.0, np.random.default_rng(s))[0]])
            for s in range(200)]
        self.assertAlmostEqual(float(np.std(np.concatenate(draws))), 0.2, delta=0.01)


class Accounting(unittest.TestCase):
    def test_calibrated_sigma_meets_target(self):
        for eps in (1.0, 4.0):
            s = L.calibrate_dpsgd_sigma(eps, 0.05, 500, 1e-5)
            self.assertLessEqual(L.dpsgd_epsilon(0.05, s, 500, 1e-5), eps + 1e-6)
            self.assertGreater(L.dpsgd_epsilon(0.05, s * 0.98, 500, 1e-5), eps)

    def test_skellam_exact_profile(self):
        for eps in (1.0, 2.0, 4.0):
            mu = L.calibrate_skellam_mu(eps, 1e-5)
            self.assertLessEqual(L.skellam_delta_exact(mu, eps), 1e-5)
            self.assertLessEqual(L.skellam_epsilon_exact(mu, 1e-5), eps + 1e-6)
            # RDP conversion is valid but looser than the exact profile
            self.assertGreaterEqual(L.skellam_epsilon(mu, 1e-5) + 1e-6, L.skellam_epsilon_exact(mu, 1e-5) * 0.999)

    def test_skellam_rdp_approaches_gaussian(self):
        mu = 2000.0
        rdp = L.skellam_rdp(mu)
        gauss = L.RDP_ORDERS / (2 * 2 * mu)
        np.testing.assert_allclose(rdp[:12], gauss[:12], rtol=0.02)

    def test_noise_sum_is_skellam(self):
        rng = np.random.default_rng(4)
        z = sum(L.skellam_noise(0.75, 200000, rng) for _ in range(4))
        self.assertAlmostEqual(float(z.var()), 2 * 3.0, delta=0.06)


class SecureAggregation(unittest.TestCase):
    def test_masks_cancel(self):
        rng = np.random.default_rng(1)
        vecs = [rng.integers(-50, 50, 30) for _ in range(5)]
        agg = L.SecureAggregator(5, b"test")
        np.testing.assert_array_equal(agg.sum_integers(vecs, 0), np.sum(vecs, axis=0))

    def test_masked_inputs_hide_values(self):
        agg = L.SecureAggregator(3, b"hide")
        v = np.zeros(1000, dtype=np.uint32)
        masked = agg.masked_input(0, v, 0)
        self.assertGreater(np.unique(masked).size, 990)

    def test_dropout_breaks_sum(self):
        agg = L.SecureAggregator(3, b"drop")
        vecs = [np.ones(10, dtype=np.int64) * k for k in range(3)]
        masked = [agg.masked_input(i, (np.asarray(v) % agg.MOD).astype(np.uint32), 0) for i, v in enumerate(vecs)]
        partial = (masked[0].astype(np.uint64) + masked[1].astype(np.uint64)) % agg.MOD
        self.assertFalse(np.array_equal(partial.astype(np.int64), np.sum(vecs[:2], axis=0)))

    def test_weighted_parameter_mean(self):
        rng = np.random.default_rng(3)
        lists = [[rng.normal(size=(3, 2)).astype(np.float32), rng.normal(size=2).astype(np.float32)] for _ in range(4)]
        w = [10, 20, 30, 40]
        agg = L.SecureAggregator(4, b"mean")
        got = agg.mean_parameters(lists, 0, weights=w)
        ref = L.aggregate(lists, "mean", w)
        for a, b in zip(got, ref):
            np.testing.assert_allclose(a, b, atol=1e-5)


class RiskControl(unittest.TestCase):
    def test_nonprivate_pvalue_is_binomial(self):
        self.assertAlmostEqual(L.binomial_skellam_pvalue(3, 40, 0.1, 0.0), stats.binom.cdf(3, 40, 0.1))

    def test_noisy_pvalue_valid_under_null(self):
        rng = np.random.default_rng(9)
        n, alpha, mu = 60, 0.1, 2.0
        p = [L.binomial_skellam_pvalue(rng.binomial(n, alpha) + L.skellam_noise(mu, 1, rng)[0], n, alpha, mu)
             for _ in range(4000)]
        self.assertLessEqual(np.mean(np.array(p) <= 0.05), 0.05 + 0.012)

    def test_scan_stops_at_first_failure(self):
        cum = np.array([0, 0, 1, 50, 2])  # non-monotone tail is ignored after the first failure
        self.assertEqual(L.risk_scan(cum, 0.0, 100, 0.1, 0.05, "ucb_without_noise"), 3)

    def test_policy_regions_partition(self):
        rng = np.random.default_rng(2)
        p = rng.random(500)
        y = (rng.random(500) < p).astype(int)
        r = L.apply_binary_policy(p, y, {"t_low": 0.2, "t_high": 0.7})
        self.assertAlmostEqual(r["auto_pass_rate"] + r["auto_alarm_rate"] + r["escalation_rate"], 1.0)

    def test_miss_guarantee_nonprivate_monte_carlo(self):
        rng = np.random.default_rng(11)
        policy = L.RiskPolicy(alpha_miss=0.1, alpha_false_alarm=0.05)
        violations = 0
        reps = 300
        grid = np.linspace(0, 1, 200001)
        for _ in range(reps):
            sp = rng.beta(4, 2, 150)
            sn = rng.beta(2, 5, 1500)
            pol = L.binary_policy([sp, sn], [np.ones(150, int), np.zeros(1500, int)], 0.0, policy,
                                  "nonprivate_ltt", rng)
            true_miss = stats.beta.cdf(pol["t_low"], 4, 2) if np.isfinite(pol["t_low"]) else 0.0
            violations += true_miss > 0.1
        self.assertLessEqual(violations / reps, 0.04 + 0.03)


class Aggregation(unittest.TestCase):
    def test_trimmed_and_median_robust_to_one_outlier(self):
        good = [[np.ones((2, 2), np.float32)] for _ in range(3)]
        bad = [[np.full((2, 2), 1e6, np.float32)]]
        self.assertTrue(np.allclose(L.aggregate(good + bad, "median")[0], 1.0))
        self.assertTrue(np.allclose(L.aggregate(good + bad, "trimmed")[0], 1.0))


if __name__ == "__main__":
    unittest.main()
