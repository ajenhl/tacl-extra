import csv
import filecmp
import os.path
import unittest


class TaclExtraTestCase (unittest.TestCase):

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

    def _compare_results_dirs(self, actual_dir, expected_dir):
        # First check that the two directories contain only the same
        # files and subdirectories.
        dircmp = filecmp.dircmp(actual_dir, expected_dir)
        self._check_unshared(dircmp)
        # Then check that the common files are the same.
        self._check_common(dircmp)

    def _compare_results_files(self, actual_path, expected_path):
        """Checks that the results files at `actual_path` and `expected_path`
        contain the same results."""
        self.assertEqual(
            self._get_results(actual_path), self._get_results(expected_path),
            'Actual results in {} do not match expected results in {}'.format(
                actual_path, expected_path))

    def _get_results(self, path):
        rows = []
        with open(path, newline='') as fh:
            reader = csv.reader(fh)
            for row in reader:
                rows.append(tuple(row))
        return set(rows)
