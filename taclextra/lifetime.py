import os
import os.path

import pandas as pd

import tacl


CONTINUED_LABEL = 'continued'
CURRENT_LABEL = 'current'
INTRODUCED_LABEL = 'introduced'
NOT_CURRENT_LABEL = 'not current'


def generate_label_map(current_label, not_current_labels):
    """Returns a mapping of `current_label` to the current label constant,
    and `not_current_labels` to the not current label constant."""
    mapping = {current_label: CURRENT_LABEL}
    for label in not_current_labels:
        mapping[label] = NOT_CURRENT_LABEL
    return mapping


def order_labels(labels, deferred):
    """Returns a copy of `labels` with `deferred` labels moved to the end
    of the list.

    :param labels: labels to reorder
    :type labels: `list`
    :param deferred: labels to move to the end
    :type deferred: `list`
    :rtype: `list`

    """
    ordered = []
    for label in labels:
        if label not in deferred:
            ordered.append(label)
    ordered.extend(deferred)
    return ordered


class LifetimeReporter:

    def __init__(self, data_store, catalogue, tokenizer, deferred_labels,
                 output_dir):
        self._data_store = data_store
        self._catalogue = catalogue
        self._tokenizer = tokenizer
        self._ordered_labels = order_labels(
            self._catalogue.ordered_labels, deferred_labels)
        self._output_dir = output_dir
        os.mkdir(self._output_dir)

    def _concatenate_results(self, result_filenames):
        """Returns a `tacl.Results` containing all of the results from the
        files specified in `result_filenames`.

        :param result_filenames: filenames of results to concatenate
        :type result_filenames: `list` of `str`
        :rtype: `tacl.Results`

        """
        results = [pd.read_csv(filename, encoding='utf-8', na_filter=False) for
                   filename in result_filenames]
        combined = pd.concat(results, ignore_index=True)
        identifying_fields = list(tacl.constants.QUERY_FIELDNAMES)
        identifying_fields.remove(tacl.constants.LABEL_FIELDNAME)
        combined.drop_duplicates(subset=identifying_fields, inplace=True)
        return tacl.Results(combined, self._tokenizer)

    def _generate_results_for_label(self, label_dir, earlier_labels,
                                    current_label, later_labels):
        """Generates results files in `label_dir` based on the supplied
        labels.

        :param label_dir: path to directory to save results files
        :type label_dir: `str`
        :param earlier_labels: labels of earlier corpora
        :type earlier_labels: `list` of `str`
        :param current_label: label of the corpus that is the current focus
        :type current_label: `str`
        :param later_labels: labels of later corpora
        :type later_labels: `list` of `str`

        """
        earlier_catalogue = self._catalogue.relabel(
            generate_label_map(current_label, earlier_labels))
        later_catalogue = self._catalogue.relabel(
            generate_label_map(current_label, later_labels))
        # Generate the various results.
        introduced_results = os.path.join(label_dir, 'introduced.csv')
        end_of_life_results = os.path.join(label_dir, 'end_of_life.csv')
        full_continued_results = os.path.join(label_dir, 'continued_full.csv')
        continued_results = os.path.join(label_dir, 'continued.csv')
        full_results = os.path.join(label_dir, 'full.csv')
        results_to_join = []
        if earlier_labels:
            with open(introduced_results, 'w') as fh:
                self._data_store.diff_asymmetric(
                    earlier_catalogue, CURRENT_LABEL,
                    self._tokenizer, fh)
            results_to_join.append(introduced_results)
        if later_labels:
            with open(end_of_life_results, 'w') as fh:
                self._data_store.diff_asymmetric(
                    later_catalogue, CURRENT_LABEL,
                    self._tokenizer, fh)
            results_to_join.append(end_of_life_results)
            with open(full_continued_results, 'w') as fh:
                self._data_store.intersection(later_catalogue, fh)
        if earlier_labels and later_labels:
            with open(continued_results, 'w') as fh:
                self._data_store.intersection_supplied(
                    [introduced_results, full_continued_results],
                    [INTRODUCED_LABEL, CONTINUED_LABEL], fh)
            results_to_join.append(continued_results)
        # Concatenate all of the results.
        results = self._concatenate_results(results_to_join)
        results.relabel(self._catalogue)
        with open(full_results, 'w') as fh:
            results.csv(fh)

    def process(self):
        """Generates and saves results files providing lifetime data."""
        for index in range(len(self._ordered_labels)):
            earlier_labels = self._ordered_labels[:index]
            current_label = self._ordered_labels[index]
            later_labels = self._ordered_labels[index+1:]
            label_dir = os.path.join(self._output_dir, current_label)
            os.mkdir(label_dir)
            self._generate_results_for_label(label_dir, earlier_labels,
                                             current_label, later_labels)
        all_results = self._concatenate_results(
            [os.path.join(self._output_dir, label, 'full.csv') for label in
             self._ordered_labels])
        with open(os.path.join(self._output_dir, 'full.csv'), 'w') as fh:
            all_results.csv(fh)
