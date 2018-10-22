import os
import os.path
import tempfile

import tacl
from taclextra.paired_intersector import PairedIntersector
from .tacl_extra_test_case import TaclExtraTestCase


class IntAllTestCase (TaclExtraTestCase):

    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self._data_dir = os.path.join(base_dir, 'int_all_data')
        self._tokenizer = tacl.Tokenizer(*tacl.constants.TOKENIZERS['cbeta'])

    def _compare_results(self, expected_dir_name, minimum, maximum,
                         catalogue, seen_pairs, db_name='test.db'):
        expected_dir = os.path.join(self._data_dir, 'expected',
                                    expected_dir_name)
        corpus = tacl.Corpus(os.path.join(self._data_dir, 'corpus'),
                             self._tokenizer)
        with tempfile.TemporaryDirectory() as temp_dir:
            if db_name is None:
                data_store = None
            else:
                data_store = tacl.DataStore(os.path.join(temp_dir, db_name),
                                            False)
                data_store.add_ngrams(corpus, minimum, maximum)
            actual_dir = os.path.join(temp_dir, 'actual')
            tracker_path = os.path.join(actual_dir, 'tracker.csv')
            if seen_pairs:
                os.makedirs(actual_dir, exist_ok=True)
                with open(tracker_path, 'w') as fh:
                    fh.writelines(['{},{}\n'.format(a, b) for a, b in
                                   seen_pairs])
            pi = PairedIntersector(data_store, corpus, self._tokenizer,
                                   catalogue, actual_dir, tracker_path, 1, 1)
            pi.intersect_all()
            self._compare_results_dirs(actual_dir, expected_dir)

    def test_intersect_all_catalogue(self):
        catalogue = tacl.Catalogue({'A': 'A', 'B': 'B', 'C': 'C'})
        self._compare_results('catalogue', 1, 1, catalogue, None)

    def test_intersect_all_extend(self):
        catalogue = tacl.Catalogue({'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'})
        self._compare_results('extend', 2, 2, catalogue, None)

    def test_intersect_all_no_extend(self):
        catalogue = tacl.Catalogue({'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'})
        self._compare_results('no-extend', 1, 1, catalogue, None)

    def test_intersect_all_no_db(self):
        catalogue = tacl.Catalogue({'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'})
        self._compare_results('no-db', 1, 1, catalogue, None, None)

    def test_tracking(self):
        """Tests that seen pairs are not regenerated."""
        catalogue = tacl.Catalogue({'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'})
        seen_pairs = (('A', 'B'), ('A', 'C'), ('B', 'C'))
        self._compare_results('tracking', 1, 1, catalogue, seen_pairs)
