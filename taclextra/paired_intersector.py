import csv
import io
import logging
import os.path

import tacl


class PairedIntersector:

    def __init__(self, data_store, corpus, tokenizer, output_dir,
                 tracker_path):
        self._logger = logging.getLogger(__name__)
        self._output_dir = os.path.abspath(output_dir)
        self._tracking_path = os.path.abspath(tracker_path)
        self._store = data_store
        self._corpus = corpus
        self._tokenizer = tokenizer
        self._seen_pairs = self._get_seen_pairs(self._tracking_path)

    def intersect_all(self):
        os.makedirs(self._output_dir, exist_ok=True)
        works = sorted(self._corpus.get_works())
        with open(self._tracking_path, 'a', newline='') as tracking_fh:
            writer = csv.writer(tracking_fh)
            for filename in works:
                output_path = os.path.join(self._output_dir, filename)
                os.makedirs(output_path, exist_ok=True)
                catalogue = tacl.Catalogue()
                catalogue[filename] = filename
                for alt_filename in works:
                    self.process_pair(filename, alt_filename, catalogue,
                                      output_path, writer)

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
        self._logger.debug('Validating corpus/catalogue')
        self._store.validate(self._corpus, catalogue)
        self._logger.debug('Running intersection')
        self._store.intersection(catalogue, results)
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

    def process_pair(self, filename, alt_filename, catalogue, output_path,
                     writer):
        if alt_filename in self._seen_pairs.get(filename, []) or \
           filename == alt_filename:
                self._logger.info(
                    'Skipping {} with {} as already done'.format(
                        filename, alt_filename))
        else:
            self._logger.info('Intersecting {} with {}'.format(
                filename, alt_filename))
            catalogue[alt_filename] = alt_filename
            results = self._get_results(catalogue)
            results_filename = self._get_results_filename(
                output_path, filename, alt_filename)
            with open(results_filename, 'w', newline='') as results_fh:
                results.csv(results_fh)
            del catalogue[alt_filename]
            self._seen_pairs.setdefault(filename, []).append(alt_filename)
            self._seen_pairs.setdefault(alt_filename, []).append(filename)
            self._logger.debug(
                'Writing {} and {} to tracking CSV'.format(filename,
                                                           alt_filename))
            writer.writerow([filename, alt_filename])
