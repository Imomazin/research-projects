"""Focused data and experiment design checks; no empirical accuracy claim."""
import importlib.util
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def load_script(filename, module_name):
    source = HERE / filename
    spec = importlib.util.spec_from_file_location(module_name, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


benchmark = load_script("Industrial Federated Benchmark.py", "industrial_benchmark")
paired = load_script("Run Paired Benchmarks.py", "paired_benchmark")


class DatasetEvidenceTests(unittest.TestCase):

    def test_maintenance_excludes_label_leakage(self):
        X, y, task, hashes, periods = benchmark.load_data("maintenance")
        self.assertEqual((len(y), int(y.sum()), task), (10000, 339, "classification"))
        self.assertTrue({"TWF", "HDF", "PWF", "OSF", "RNF", "Machine failure",
                         "Product ID", "UDI"}.isdisjoint(X.columns))
        self.assertGreaterEqual(len(hashes), 1)
        self.assertIsNone(periods)

    def test_steel_multiclass_integrity(self):
        X, y, task, _, _ = benchmark.load_data("steel")
        self.assertEqual((len(y), X.shape[1], len(np.unique(y))),
                         (1941, 27, 7))
        self.assertEqual(task, "classification")

    def test_semiconductor_record_alignment(self):
        X, y, task, _, _ = benchmark.load_data("semiconductor")
        self.assertEqual(X.shape, (1567, 590))
        self.assertEqual((int(y.sum()), task), (104, "classification"))

    def test_power_prediction_target_separation(self):
        X, y, task, _, _ = benchmark.load_data("power")
        self.assertEqual((len(y), X.shape[1], task), (9568, 4, "regression"))
        self.assertNotIn("PE", X.columns)

    def test_gas_unseen_year_holdout(self):
        X, y, task, _, periods = benchmark.load_data("gas")
        self.assertEqual((len(y), task), (36733, "regression"))
        self.assertTrue(set(np.unique(periods)) == {2011, 2012, 2013, 2014, 2015})
        self.assertTrue({"NOX", "CO"}.isdisjoint(X.columns))
        _, _, _, meta = benchmark.split_and_prepare(
            X, y, task, seed=11, max_rows=500, periods=periods
        )
        self.assertTrue(meta["temporal_holdout_by_year"])
        self.assertEqual(meta["training_rows"] + meta["validation_rows"] +
                         meta["test_rows"], 500)

    def test_iot_attacks_are_not_features(self):
        X, y, task, _, _ = benchmark.load_data("iot")
        self.assertEqual((len(y), task), (123117, "classification"))
        self.assertTrue({"Attack_type", "Unnamed: 0"}.isdisjoint(X.columns))
        self.assertTrue(set(np.unique(y)) == {0, 1})


class FederatedDesignTests(unittest.TestCase):

    def test_partition_is_exhaustive_and_nonoverlapping(self):
        y = np.asarray([0] * 150 + [1] * 150, dtype=int)
        groups, _ = benchmark.client_partitions(
            y, task="classification", clients=3, concentration=0.5, seed=11
        )
        self.assertEqual(len(groups), 3)
        flattened = np.concatenate(groups)
        self.assertEqual(len(flattened), len(y))
        np.testing.assert_array_equal(np.sort(flattened), np.arange(len(y)))
        self.assertGreaterEqual(min(map(len, groups)), 20)

    def test_filename_identifiers_contain_no_digits(self):
        name = paired.trial_name("maintenance", 42, 0.5, 1.2)
        self.assertFalse(any(c.isdigit() for c in name))
        self.assertTrue(name.endswith(".json"))

    def test_summary_reports_independent_seed_count(self):
        template = {"dataset": "maintenance", "alpha": 0.5, "noise": 1.2,
                    "model": "fedavg", "evaluation_split": "validation",
                    "metric": "macro_f1"}
        rows = [{**template, "value": v} for v in [0.5, 0.6, 0.7]]
        summary = paired.group_summary(rows)
        self.assertEqual(summary[0]["seeds"], 3)
        self.assertAlmostEqual(summary[0]["mean"], 0.6)
        self.assertLess(summary[0]["confidence_interval_lower"], 0.6)
        self.assertGreater(summary[0]["confidence_interval_upper"], 0.6)


if __name__ == "__main__":
    unittest.main()
