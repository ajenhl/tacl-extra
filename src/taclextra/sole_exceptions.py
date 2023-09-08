"""Library for generating sole exceptions results files, giving the
n-grams that are sole exceptions for each work in a sub-corpus
compared to another sub-corpus.

The operations for each work X in corpus-A compared to the base
corpus-B is:

1. Generate two catalogues:
     a. corpus-B vs X; and
     b. corpus-B vs corpus-A without X

2. Diff with catalogue 1b filtered by min-works and min-count (results-1)

3. Intersect with catalogue 1a (results-2)

4. Supplied intersect of results-1 and results-2 (results-3-raw)

5. Remove from results-3-raw any n-grams occurring in the list of
   known n-grams (results-3-filtered)

6. Apply zero-fill and witness collapse (results-3-filtered-trimmed)

The SoleExceptionProcessor class here is entirely distinct from the
SEProcessor in sole_exception.py, which is a reporting tool on its own
generated data.

"""

import os
import tempfile

import tacl


DIFF_RESULTS_NAME = "diff.csv"
INTERSECT_RESULTS_NAME = "intersect.csv"
SUPPLIED_INTERSECT_RESULTS_NAME = "supplied_intersect.csv"


class SoleExceptionProcessor:

    def __init__(self, store, corpus, tokenizer, base_works,
                 exception_works, min_count, min_works, exclude_ngrams,
                 output_dir, logger):
        self._store = store
        self._corpus = corpus
        self._tokenizer = tokenizer
        self._base_works = base_works
        self._exception_works = exception_works
        self._exclude_ngrams = exclude_ngrams
        self._min_count = min_count
        self._min_works = min_works
        self._output_dir = output_dir
        self._logger = logger

    def _diff(self, work, output_dir):
        other_works = self._exception_works.copy()
        other_works.remove(work)
        catalogue = self._generate_catalogue(other_works)
        output_path = os.path.join(output_dir, "diff_base.csv")
        with open(output_path, "w", encoding="utf-8", newline="") as fh:
            self._store.diff_asymmetric(catalogue, "base", self._tokenizer, fh)
        results = tacl.Results(output_path, self._tokenizer)
        results.prune_by_work_count(minimum=self._min_works)
        results.prune_by_ngram_count(minimum=self._min_count)
        output_path = os.path.join(output_dir, DIFF_RESULTS_NAME)
        with open(output_path, "w", encoding="utf-8", newline="") as fh:
            results.csv(fh)

    def _generate_catalogue(self, other_works):
        catalogue = tacl.Catalogue()
        for work in self._base_works:
            catalogue[work] = 'base'
        for work in other_works:
            catalogue[work] = 'other'
        return catalogue

    def _intersect(self, work, output_dir):
        catalogue = self._generate_catalogue([work])
        output_path = os.path.join(output_dir, INTERSECT_RESULTS_NAME)
        with open(output_path, "w", encoding="utf-8", newline="") as fh:
            self._store.intersection(catalogue, fh)

    def process_works(self):
        os.makedirs(self._output_dir, exist_ok=True)
        for work in self._exception_works:
            self.process_work(work)

    def process_work(self, work):
        self._logger.info('Processing work "{}".'.format(work))
        output_path = os.path.join(self._output_dir, "{}.csv".format(work))
        if os.path.exists(output_path):
            self._logger.info(
                'Found existing results for "{}"; skipping.'.format(work))
            return
        with tempfile.TemporaryDirectory() as temp_dir:
            self._diff(work, temp_dir)
            self._intersect(work, temp_dir)
            results = self._supplied_intersect(work, temp_dir)
            if self._exclude_ngrams:
                results.prune_by_ngram(self._exclude_ngrams)
            results.zero_fill(self._corpus)
            results.collapse_witnesses()
            with open(output_path, "w", encoding="utf-8", newline="") as fh:
                results.csv(fh)

    def _supplied_intersect(self, work, output_dir):
        result_paths = [
            os.path.join(output_dir, DIFF_RESULTS_NAME),
            os.path.join(output_dir, INTERSECT_RESULTS_NAME)
        ]
        labels = ["base", work]
        output_path = os.path.join(output_dir, SUPPLIED_INTERSECT_RESULTS_NAME)
        with open(output_path, "w", encoding="utf-8", newline="") as fh:
            self._store.intersection_supplied(result_paths, labels, fh)
        return tacl.Results(output_path, self._tokenizer)
