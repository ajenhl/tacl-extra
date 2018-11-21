"""Test suite for the JitC report."""

import os.path
import shlex
import subprocess
import tempfile

import tacl

from .tacl_extra_test_case import TaclExtraTestCase


class JitCTestCase (TaclExtraTestCase):

    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self._data_dir = os.path.join(base_dir, 'jitc_data')
        self._tokenizer = tacl.Tokenizer(*tacl.constants.TOKENIZERS['cbeta'])

    def _generate_database(self, data_store_path, corpus, tokenizer):
        """Generates a database from the `corpus`."""
        data_store = tacl.DataStore(data_store_path)
        data_store.add_ngrams(corpus, 1, 1)

    def test_cli(self):
        """Tests that the jitc CLI script runs correctly."""
        expected_dir = os.path.join(self._data_dir, 'expected')
        corpus_path = os.path.join(self._data_dir, 'corpus')
        corpus = tacl.Corpus(corpus_path, self._tokenizer)
        catalogue_path = os.path.join(self._data_dir, 'catalogue.txt')
        label = 'in'
        with tempfile.TemporaryDirectory() as temp_dir:
            actual_dir = os.path.join(temp_dir, 'actual')
            data_store_path = os.path.join(temp_dir, 'test.db')
            self._generate_database(data_store_path, corpus, self._tokenizer)
            command = 'jitc {} {} {} {} {}'.format(
                data_store_path, corpus_path, catalogue_path, label,
                actual_dir)
            subprocess.run(shlex.split(command))
            self._compare_results_dirs(actual_dir, expected_dir)

    def test_mismatched_labels(self):
        """Tests that an error is raised if the supplied label is not used in
        the catalogue."""
        corpus_path = os.path.join(self._data_dir, 'corpus')
        catalogue_path = os.path.join(self._data_dir, 'catalogue.txt')
        label = 'nope'
        with tempfile.TemporaryDirectory() as temp_dir:
            data_store_path = os.path.join(temp_dir, 'test.db')
            command = 'jitc {} {} {} {} {}'.format(
                data_store_path, corpus_path, catalogue_path, label,
                temp_dir)
            output = subprocess.run(shlex.split(command))
            self.assertEqual(output.returncode, 2)
            self.assertTrue('The specified label "nope" must be present in '
                            'the catalogue.', output.stderr)

    def test_too_many_labels(self):
        """Tests that an error is raised if the catalogue does not have two
        labels."""
        corpus_path = os.path.join(self._data_dir, 'corpus')
        catalogue_path = os.path.join(self._data_dir, 'bad_catalogue_1.txt')
        label = 'in'
        for catalogue_path in ['bad_catalogue_1.txt', 'bad_catalogue_2.txt']:
            full_catalogue_path = os.path.join(self._data_dir, catalogue_path)
            with tempfile.TemporaryDirectory() as temp_dir:
                data_store_path = os.path.join(temp_dir, 'test.db')
                command = 'jitc {} {} {} {} {}'.format(
                    data_store_path, corpus_path, full_catalogue_path, label,
                    temp_dir)
                output = subprocess.run(shlex.split(command))
                self.assertEqual(output.returncode, 2)
                self.assertTrue('The catalogue must specify only two labels.',
                                output.stderr)
