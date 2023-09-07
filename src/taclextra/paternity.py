import copy
import os.path

import pandas as pd

import tacl.exceptions


class InvalidLabelError (tacl.exceptions.TACLError):

    pass


class PaternityTest:

    def __init__(self, data_store, catalogue, tokenizer, parent_label,
                 child_label, unrelated_label, max_works, output_dir):
        """Initialise the PaternityTest instance.

        :param data_store: connection to the store containing n-gram data
        :type data_store: `tacl.DataStore`
        :param catalogue: catalogue labelling the parent, child, and
                          unrelated corpora to operate on
        :type catalogue: `tacl.Catalogue`
        :param tokenizer: tokenizer for the n-grams
        :type tokenizer: `tacl.Tokenizer`
        :param parent_label: label of the parent corpus
        :type parent_label: `str`
        :param child_label: label of the child corpus
        :type child_label: `str`
        :param unrelated_label: label of the unrelated corpus
        :type unrelated_label: `str`
        :param max_works: maximum number of child works an n-gram may
                          belong to
        :type max_works: `int`
        :param output_dir: path to output directory, which must not
                           already exist
        :type output_dir: `str`

        """
        self._validate_labels(catalogue, parent_label, child_label,
                              unrelated_label)
        self._data_store = data_store
        self._catalogue = catalogue
        self._tokenizer = tokenizer
        self._parent_label = parent_label
        self._child_label = child_label
        self._unrelated_label = unrelated_label
        self._max_works = max_works
        output_dir = os.path.abspath(output_dir)
        os.mkdir(output_dir)
        self._output_dir = output_dir

    def _filter_results(self, results_path, max_works):
        """Filters the results at `results_path` to remove n-grams that occur
        in more than `max_works` works in the child corpus.

        :param results_path: path to results to filter
        :type results_path: `str`
        :param max_works: maximum number of child works an n-gram may belong to
        :type max_works: `int`

        """
        results = pd.read_csv(results_path, encoding='utf-8', na_filter=False)
        results = results.dropna(how='all')
        count_fieldname = 'tmp_count'
        filtered = results[results[tacl.constants.LABEL_FIELDNAME] ==
                           self._child_label]
        grouped = filtered.groupby(tacl.constants.NGRAM_FIELDNAME, sort=False)
        counts = pd.DataFrame(grouped[tacl.constants.WORK_FIELDNAME].nunique())
        counts.rename(columns={tacl.constants.WORK_FIELDNAME: count_fieldname},
                      inplace=True)
        counts = counts[counts[count_fieldname] <= max_works]
        results = pd.merge(results, counts,
                           left_on=tacl.constants.NGRAM_FIELDNAME,
                           right_index=True)
        del results[count_fieldname]
        with open(results_path, 'w', newline='') as fh:
            results.to_csv(fh, encoding='utf-8', float_format='%d',
                           index=False)

    def _generate_child_results(self):
        """Generates and returns the path to the results giving n-grams in the
        child works.

        :rtype: `str`

        """
        child_catalogue = self._catalogue.relabel(
            {self._child_label: self._child_label})
        child_results_path = os.path.join(self._output_dir, 'child.csv')
        with open(child_results_path, 'w') as fh:
            self._data_store.search(child_catalogue, [], fh)
        return child_results_path

    def _generate_parent_child_results(self, parent_unrelated_results_path,
                                       child_results_path):
        """Generates and returns the path to the results giving n-grams shared
        between the results at `parent_unrelated_results_path` and
        `child_results_path`.

        :param parent_unrelated_results_path: path to results of
                                              removing unrelated
                                              n-grams from the parent
                                              n-grams
        :type parent_unrealted_results_path: `str`
        :param child_results_path: path to results of child n-grams
        :type child_results_path: `str`
        :rtype: `str`

        """
        parent_child_results_path = os.path.join(
            self._output_dir, 'parent-child.csv')
        with open(parent_child_results_path, 'w') as fh:
            self._data_store.intersection_supplied(
                [parent_unrelated_results_path, child_results_path],
                [self._parent_label, self._child_label], fh)
        return parent_child_results_path

    def _generate_parent_unrelated_results(self):
        """Generates and return the path to the results giving n-grams in the
        parent corpus that are not in the unrelated corpus.

        :rtype: `str`

        """
        parent_unrelated_results_path = os.path.join(
            self._output_dir, 'parent-minus-unrelated.csv')
        parent_unrelated_catalogue = copy.deepcopy(self._catalogue)
        parent_unrelated_catalogue.remove_label(self._child_label)
        with open(parent_unrelated_results_path, 'w') as fh:
            self._data_store.diff_asymmetric(
                parent_unrelated_catalogue, self._parent_label,
                self._tokenizer, fh)
        return parent_unrelated_results_path

    def process(self):
        """Run the paternity test, saving the various results files."""
        parent_unrelated_path = self._generate_parent_unrelated_results()
        child_path = self._generate_child_results()
        parent_child_path = self._generate_parent_child_results(
            parent_unrelated_path, child_path)
        self._filter_results(parent_child_path, self._max_works)

    def _validate_labels(self, catalogue, parent_label, child_label,
                         unrelated_label):
        """Raises an exception if the labels in `catalogue` do not match
        `parent_label, `child_label`, and `unrelated_label`, or if any of
        those three labels are the same as each other.

        :param catalogue: catalogue to match labels with
        :type catalogue: `tacl.Catalogue`
        :param parent_label: label of parent corpus
        :type parent_label: `str`
        :param child_label: label of child corpus
        :type child_label: `str`
        :param unrelated_label: label of unrelated corpus
        :type unrelated_label: `str`

        """
        label_set = set([parent_label, child_label, unrelated_label])
        label_msg = 'The three supplied labels (parent, child, unrelated)'
        if len(label_set) != 3:
            raise InvalidLabelError('{} must be distinct.'.format(label_msg))
        if catalogue.labels != sorted(label_set):
            raise InvalidLabelError(
                '{} must match the labels in the catalogue.'.format(label_msg))
