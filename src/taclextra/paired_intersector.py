import csv
import io
import logging
import os.path

import tacl


class PairedIntersector:

    def __init__(self, data_store, corpus, tokenizer, catalogue, output_dir,
                 tracker_path, minimum=1, maximum=10):
        """Initialise a PairedIntersector object.

        :param data_store: database to query, or None to use
                           individually created databases
        :type data_store: `tacl.DataStore` or None
        :param corpus: corpus of works to intersect
        :type corpus: `tacl.Corpus`
        :param tokenizer: tokenizer for the n-grams
        :type tokenizer: `tacl.Tokenizer`
        :param catalogue: catalogue to limit the works to intersect
        :type catalogue: `tacl.Catalogue`
        :param output_dir: path to directory to output results to
        :type ouput_dir: `str`
        :param tracker_path: path to tracker file
        :type tracker_path: `str`
        :param minimum: minimum n-gram size when creating individual databases
        :type minimum: `int`
        :param maximum: maximum n-gram size when creating individual databases
        :type maximum: `int`

        """
        self._logger = logging.getLogger(__name__)
        self._output_dir = os.path.abspath(output_dir)
        self._tracking_path = os.path.abspath(tracker_path)
        self._store = data_store
        self._corpus = corpus
        self._tokenizer = tokenizer
        self._catalogue = catalogue
        self._seen_pairs = self._get_seen_pairs(self._tracking_path)
        self._minimum = minimum
        self._maximum = maximum

    def intersect_all(self):
        os.makedirs(self._output_dir, exist_ok=True)
        works = sorted(self._catalogue.keys())
        if self._tracking_path is not None:
            with open(self._tracking_path, 'a', newline='') as tracking_fh:
                writer = csv.writer(tracking_fh)
                self._intersect_all(works, writer)
        else:
            self._intersect_all(works, None)

    def _intersect_all(self, works, writer):
        for work in works:
            output_path = os.path.join(self._output_dir, work)
            os.makedirs(output_path, exist_ok=True)
            catalogue = tacl.Catalogue()
            catalogue[work] = work
            for alt_work in works:
                if writer is None:
                    self.process_pair(work, alt_work, catalogue, output_path)
                else:
                    self.process_pair_with_tracking(work, alt_work, catalogue,
                                                    output_path, writer)
            # Delete output directory if empty.
            try:
                os.rmdir(output_path)
            except OSError:
                pass

    def _get_seen_pairs(self, tracking_filename):
        seen_pairs = {}
        if os.path.exists(tracking_filename):
            with open(tracking_filename) as tracking_fh:
                reader = csv.reader(tracking_fh)
                for row in reader:
                    seen_pairs.setdefault(row[0], []).append(row[1])
                    seen_pairs.setdefault(row[1], []).append(row[0])
        return seen_pairs

    def _get_results(self, catalogue):
        results = io.StringIO()
        if self._store is None:
            store = tacl.DataStore(':memory:', True)
            store.add_ngrams(self._corpus, self._minimum, self._maximum,
                             catalogue)
        else:
            store = self._store
        self._logger.debug('Validating corpus/catalogue')
        store.validate(self._corpus, catalogue)
        self._logger.debug('Running intersection')
        store.intersection(catalogue, results)
        store = None
        results.seek(0)
        self._logger.debug('Generating results')
        results = tacl.Results(results, self._tokenizer)
        self._logger.debug('Extending results')
        results.extend(self._corpus)
        self._logger.debug('Reducing')
        results.reduce()
        return results

    def _get_results_filename(self, output_path, filename, alt_filename):
        return os.path.join(output_path, '{}-{}.csv'.format(
            filename, alt_filename))

    def process_pair(self, work, alt_work, catalogue, output_path):
        self._logger.info('Intersecting {} with {}'.format(work, alt_work))
        catalogue[alt_work] = alt_work
        results = self._get_results(catalogue)
        results_filename = self._get_results_filename(output_path, work,
                                                      alt_work)
        with open(results_filename, 'w', newline='') as results_fh:
            results.csv(results_fh)
        del catalogue[alt_work]

    def process_pair_with_tracking(self, work, alt_work, catalogue,
                                   output_path, writer):
        if alt_work in self._seen_pairs.get(work, []) or \
           work == alt_work:
                self._logger.info(
                    'Skipping {} with {} as already done'.format(
                        work, alt_work))
        else:
            self.process_pair(work, alt_work, catalogue, output_path)
            self._seen_pairs.setdefault(work, []).append(alt_work)
            self._seen_pairs.setdefault(alt_work, []).append(work)
            self._logger.debug(
                'Writing {} and {} to tracking CSV'.format(work, alt_work))
            writer.writerow([work, alt_work])
