import csv
import filecmp
import os.path
import tempfile
import unittest

import tacl
from taclextra import lifetime


class LifetimeTestCase (unittest.TestCase):

    # A, B, C, D, E: exists only in the work of the same name
    # F, G, H, I, J: starts in A and continues until corresponding work
    # K, L, M, N, O: starts in corresponding work and continues until E

    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self._data_dir = os.path.join(base_dir, 'lifetime_data')
        self._tokenizer = tacl.Tokenizer(*tacl.constants.TOKENIZERS['cbeta'])

    def _check_common(self, dircmp):
        for common_file in dircmp.common_files:
            self._compare_results_files(
                os.path.join(dircmp.left, common_file),
                os.path.join(dircmp.right, common_file))
        for sd in dircmp.subdirs.values():
            self._check_common(sd)

    def _check_unshared(self, dircmp):
        self.assertEqual(dircmp.left_only, [], 'Actual results contains unexpected files and/or subdirectories in {}'.format(dircmp.left))
        self.assertEqual(dircmp.right_only, [], 'Actual results missing expected files and/or subdirectories found in {}'.format(dircmp.right))
        for sd in dircmp.subdirs.values():
            self._check_unshared(sd)

    def _compare_results(self, corpus_dir, catalogue_name,
                               deferred_labels, expected_dir_name):
        """Compare all of the actual results files with the expected
        versions."""
        expected_dir = os.path.join(self._data_dir, 'expected',
                                    expected_dir_name)
        corpus = tacl.Corpus(os.path.join(self._data_dir, corpus_dir),
                             self._tokenizer)
        catalogue = tacl.Catalogue()
        catalogue.load(os.path.join(self._data_dir, catalogue_name))
        with tempfile.TemporaryDirectory() as temp_dir:
            data_store = tacl.DataStore(os.path.join(temp_dir, 'test.db'),
                                        False)
            data_store.add_ngrams(corpus, 1, 1)
            output_dir = os.path.join(temp_dir, 'output')
            reporter = lifetime.LifetimeReporter(
                data_store, catalogue, self._tokenizer, deferred_labels,
                output_dir)
            reporter.process()
            # First check that the two directories contain only the same
            # files and subdirectories.
            dircmp = filecmp.dircmp(output_dir, expected_dir)
            self._check_unshared(dircmp)
            # Then check that the common files are the same.
            self._check_common(dircmp)

    def _compare_results_files(self, actual_path, expected_path):
        """Checks that the results files at `actual_path` and `expected_path`
        contain the same results."""
        self.assertEqual(self._get_results(actual_path),
                         self._get_results(expected_path),
                         'Actual results in {} do not match expected results in {}'.format(actual_path, expected_path))

    def _get_results(self, path):
        rows = []
        with open(path, newline='') as fh:
            reader = csv.reader(fh)
            for row in reader:
                rows.append(tuple(row))
        return set(rows)

    def test_process(self):
        self._compare_results('corpus', 'catalogue.txt', [], 'no_deferred')
