import os.path
import shlex
import subprocess
import tempfile

import tacl
from taclextra import paternity
from .tacl_extra_test_case import TaclExtraTestCase


class PaternityTestCase (TaclExtraTestCase):

    # A, B, C: exclusive to parent (P texts)
    # D, E, F: shared between all (P, C, and U texts)
    # G, H, I: shared between parent and child (P and C texts)
    # J, K, L: exclusive to child (C texts)
    # M, N, O: exclusive to unrelated (U texts)
    # P, Q, R: shared between parent and unrelated (P and U texts)

    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self._data_dir = os.path.join(base_dir, 'paternity_data')
        self._tokenizer = tacl.Tokenizer(*tacl.constants.TOKENIZERS['cbeta'])
        self._corpus = os.path.join(self._data_dir, 'corpus')
        self._catalogue = os.path.join(self._data_dir, 'catalogue.txt')

    def _compare_results(self, max_works, expected_dir_name):
        expected_dir = os.path.join(self._data_dir, 'expected',
                                    expected_dir_name)
        corpus = tacl.Corpus(self._corpus, self._tokenizer)
        catalogue = tacl.Catalogue()
        catalogue.load(self._catalogue)
        with tempfile.TemporaryDirectory() as temp_dir:
            data_store = tacl.DataStore(os.path.join(temp_dir, 'test.db'),
                                        must_exist=False)
            data_store.add_ngrams(corpus, 1, 1)
            output_dir = os.path.join(temp_dir, 'output')
            test = paternity.PaternityTest(
                data_store, catalogue, self._tokenizer, 'P', 'C', 'U',
                max_works, output_dir)
            test.process()
            self._compare_results_dirs(output_dir, expected_dir)

    def test_duplicate_labels(self):
        """Tests that providing duplicate labels fails properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_store = os.path.join(temp_dir, 'test.db')
            command = 'paternity {} {} {} A B B 2 {}'.format(
                data_store, self._corpus, self._catalogue, temp_dir)
            output = subprocess.run(shlex.split(command))
            self.assertEqual(output.returncode, 2)

    def test_mismatched_labels(self):
        """Tests that providing labels that don't match the catalogue's fails
        properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_store = os.path.join(temp_dir, 'test.db')
            command = 'paternity {} {} {} A B D 2 {}'.format(
                data_store, self._corpus, self._catalogue, temp_dir)
            output = subprocess.run(shlex.split(command))
            self.assertEqual(output.returncode, 2)

    def test_non_integer_maximum(self):
        """Tests that the maximum works argument must be an integer."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_store = os.path.join(temp_dir, 'test.db')
            command = 'paternity {} {} {} A B C foo {}'.format(
                data_store, self._corpus, self._catalogue, temp_dir)
            output = subprocess.run(shlex.split(command))
            self.assertEqual(output.returncode, 2)

    def test_process(self):
        self._compare_results(1, 'max_works_1')
        self._compare_results(2, 'max_works_2')
        self._compare_results(3, 'max_works_3')
