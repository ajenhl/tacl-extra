import os.path
import tempfile

import tacl
from taclextra import lifetime
from .tacl_extra_test_case import TaclExtraTestCase


class LifetimeTestCase (TaclExtraTestCase):

    # A, B, C, D, E: exists only in the work of the same name
    # F, G, H, I, J: starts in A and continues until corresponding work
    # K, L, M, N, O: starts in corresponding work and continues until E

    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self._data_dir = os.path.join(base_dir, 'lifetime_data')
        self._tokenizer = tacl.Tokenizer(*tacl.constants.TOKENIZERS['cbeta'])

    def _compare_results(self, corpus_dir, catalogue_name):
        """Compare all of the actual results files with the expected
        versions."""
        expected_dir = os.path.join(self._data_dir, 'expected')
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
                data_store, catalogue, self._tokenizer, output_dir)
            reporter.process()
            self._compare_results_dirs(output_dir, expected_dir)

    def test_process(self):
        self._compare_results('corpus', 'catalogue.txt')
