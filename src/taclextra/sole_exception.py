import csv
import logging
from math import ceil

from jinja2 import Environment, PackageLoader, select_autoescape

import pandas as pd

import tacl
from tacl.report import Report


CORPORA_STATS_FIELDNAME_AVERAGE_LENGTH = "average length"
CORPORA_STATS_FIELDNAME_COUNT_WORKS = "works"
CORPORA_STATS_FIELDNAME_CORPUS = "corpus"
CORPORA_STATS_FIELDNAME_LENGTH = "length"

GREY_STATS_FIELDNAME_LENGTH = "length"
GREY_STATS_FIELDNAME_WORK = "work"
GREY_STATS_FIELDNAMES = [GREY_STATS_FIELDNAME_WORK,
                         GREY_STATS_FIELDNAME_LENGTH]

OTHER_CORPUS_LABEL = "other"

CORPORA_STATS_RESULTS_FILENAME = "corpora-stats.csv"
CORPUS_MARKERS_FILENAME = "{}-markers.txt"
CORPUS_RESULTS_FILENAME = "{}-results.csv"
GREY_ALL_RESULTS_FILENAME = "{}-results.csv"
GREY_RESULTS_FILENAME = "{}-in-grey-results.csv"
GREY_STATS_RESULTS_FILENAME = "grey-stats.csv"
REPORT_CORPUS_FILENAME = "{}.html"
REPORT_DATA_FILENAME = "report-data.csv"
REPORT_FULL_FILENAME = "report.html"
REPORT_WORK_FILENAME = "{}.html"


def make_percentage(value):
    return "{:.1%}".format(value)


def make_rounded(value):
    return str(round(value))


class SEProcessor(Report):

    _package_name = "taclextra"
    _report_name = "sole_exception"

    def __init__(self, data_store, corpus, catalogue, tokenizer,
                 grey_label, output_dir, extra_work_df):
        self._logger = logging.getLogger("tacl")
        self._catalogue = catalogue
        self._corpus = corpus
        self._data_store = data_store
        self._extra_work_df = extra_work_df
        self._grey_label = grey_label
        self._output_dir = output_dir
        self._tokenizer = tokenizer
        self._corpus_labels = self._get_corpus_labels()
        self._grey_works = catalogue.get_works_by_label(grey_label)

    def _create_diff_catalogue(self, corpus_labels, corpus_label):
        """Return a new catalogue with all labels in `corpus_labels`
        except `corpus_label` changed to a single label; `corpus_label` is
        unchanged."""
        label_map = {corpus_label: corpus_label}
        for other_corpus_label in corpus_labels:
            if other_corpus_label != corpus_label:
                label_map[other_corpus_label] = OTHER_CORPUS_LABEL
        return self._catalogue.relabel(label_map)

    def filter_markers(self):
        grey_path = self._output_dir / GREY_ALL_RESULTS_FILENAME.format(
            self._grey_label)
        results = tacl.Results(grey_path, self._tokenizer)
        # Filtering itself goes here; currently there is no filtering
        # performed.
        self._generate_report_data(results._matches)

    def generate(self):
        self._logger.info("Generating HTML report.")
        df = pd.read_csv(self._output_dir / REPORT_DATA_FILENAME)
        # Rename columns for display.
        df = df.rename(columns={
            tacl.constants.LABEL_FIELDNAME: "corpus",
            "corpus_length": "corpus length",
            "markers_to_length": "markers:length",
            "number_of_markers": "number of markers",
            "work_length": "work length",
        })
        columns = [
            "corpus",
            "corpus length",
            tacl.constants.WORK_FIELDNAME,
            "work length",
            "number of markers",
            "markers:length",
            "score",
        ]
        has_extra_cols = False
        sort_index = columns.index("score")
        if self._extra_work_df is not None:
            df = df.merge(self._extra_work_df, how="left", on="work",
                          suffixes=(None, " extra"))
            df.fillna("", inplace=True)
            i = columns.index(tacl.constants.WORK_FIELDNAME) + 1
            for column in self._extra_work_df.columns:
                if column != "work":
                    columns.insert(i, column)
                    i += 1
                    sort_index += 1
            has_extra_cols = True
        formatters = {
            "corpus": str,
            tacl.constants.WORK_FIELDNAME: str,
            "marker length": make_rounded,
            "markers:length": str,
            "number of markers": make_rounded,
            "% of work in markers": make_percentage,
        }
        table = df.to_html(columns=columns, formatters=formatters,
                           index=False, justify="left", table_id="report")
        table = self._link_corpora(table)
        table = self._link_works(table)
        # Add links to corpora and works.
        output_dir = self._output_dir / "reports"
        output_dir.mkdir(exist_ok=True, parents=True)
        context = {
            "has_extra_cols": has_extra_cols,
            "sort_index": sort_index,
            "table": table,
            "title": "All",
        }
        # Main report.
        main_context = context | {"corpora": self._corpus_labels,
                                  "works": self._grey_works}
        self._write(main_context, output_dir, REPORT_FULL_FILENAME)
        # Corpus reports.
        for label in self._corpus_labels:
            report_name = REPORT_CORPUS_FILENAME.format(label)
            table = df[df["corpus"] == label].to_html(
                columns=columns, formatters=formatters, index=False,
                justify="left", table_id="report")
            table = self._link_works(table)
            corpus_context = context | {"table": table, "title": label}
            self._write(corpus_context, output_dir, report_name)
        # Work reports.
        for work in self._grey_works:
            report_name = REPORT_WORK_FILENAME.format(work)
            table = df[df[tacl.constants.WORK_FIELDNAME] == work].to_html(
                columns=columns, formatters=formatters, index=False,
                justify="left", table_id="report")
            table = self._link_corpora(table)
            work_context = context | {"table": table, "title": work}
            self._write(work_context, output_dir, report_name)

    def generate_corpora_markers(self):
        """Generate marker files containing the markers exclusive to
        each benchmark corpus in `catalogue` against all other
        benchmark corpora together."""
        for corpus_label in self._corpus_labels:
            self._generate_corpus_markers(self._corpus_labels, corpus_label)

    def generate_corpora_stats(self):
        self._logger.info("Generating corpus lengths for benchmark corpora and individual unclassified works.")
        results_path = self._output_dir / CORPORA_STATS_RESULTS_FILENAME
        if results_path.exists():
            self._logger.info("  Output file for corpora stats exists; skipping.")
        else:
            stats = []
            for corpus_label in self._corpus_labels:
                stats.append(self._generate_corpus_stats(corpus_label))
            df = pd.DataFrame(stats)
            df.to_csv(results_path, index=False)
        results_path = self._output_dir / GREY_STATS_RESULTS_FILENAME
        if results_path.exists():
            self._logger.info("  Output file for unclassified works stats exists; skipping.")
        else:
            stats = []
            for work in self._catalogue.get_works_by_label(self._grey_label):
                length = ceil(self._get_work_length(work))
                stats.append({
                    GREY_STATS_FIELDNAME_WORK: work,
                    GREY_STATS_FIELDNAME_LENGTH: length,
                })
            with open(results_path, "w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=GREY_STATS_FIELDNAMES)
                writer.writeheader()
                for row in stats:
                    writer.writerow(row)

    def _generate_corpus_markers(self, corpus_labels, corpus_label):
        self._logger.info("Processing {}".format(corpus_label))
        new_catalogue = self._create_diff_catalogue(
            corpus_labels, corpus_label)
        results_path = self._output_dir / CORPUS_RESULTS_FILENAME.format(
            corpus_label)
        if results_path.exists():
            self._logger.info("  Output file for results exists; skipping.")
        else:
            with open(results_path, "w", encoding="utf-8", newline="") as fh:
                self._data_store.diff_asymmetric(
                    new_catalogue, corpus_label, self._tokenizer, fh)
        markers_path = self._output_dir / CORPUS_MARKERS_FILENAME.format(
            corpus_label)
        if markers_path.exists():
            self._logger.info("  Output file for markers exists; skipping.")
        else:
            results_df = tacl.Results(results_path, self._tokenizer)._matches
            markers = list(results_df[
                results_df[tacl.constants.COUNT_FIELDNAME] > 1][
                    tacl.constants.NGRAM_FIELDNAME].unique())
            markers = sorted(markers, key=len)
            with open(markers_path, "w", encoding="utf-8") as fh:
                fh.writelines(["{}\n".format(marker) for marker in markers])

    def _generate_corpus_stats(self, corpus_label):
        work_lengths = []
        work_count = 0
        for work in self._catalogue.get_works_by_label(corpus_label):
            work_lengths.append(self._get_work_length(work))
            work_count += 1
        total_length = ceil(sum(work_lengths))
        return {
            CORPORA_STATS_FIELDNAME_CORPUS: corpus_label,
            CORPORA_STATS_FIELDNAME_LENGTH: total_length,
            CORPORA_STATS_FIELDNAME_COUNT_WORKS: work_count,
            CORPORA_STATS_FIELDNAME_AVERAGE_LENGTH: total_length / work_count,
        }

    def generate_grey_markers(self):
        """Generate a results file containing every instance of the
        various corpus markers found in the unclassified works.

        Each work is labelled according to the benchmark corpus the
        marker came from.

        """
        for corpus_label in self._corpus_labels:
            self._generate_grey_markers_for_corpus(corpus_label)
        grey_path = self._output_dir / GREY_ALL_RESULTS_FILENAME.format(
            self._grey_label)
        self._logger.info("Creating combined {} data".format(self._grey_label))
        if grey_path.exists():
            self._logger.info("  Output file for combined results exists; skipping.")
            return
        data_frames = []
        for corpus_label in self._corpus_labels:
            results_path = self._output_dir / GREY_RESULTS_FILENAME.format(
                corpus_label)
            data_frames.append(pd.read_csv(results_path, encoding="utf-8"))
        grey_df = pd.concat(data_frames, ignore_index=True)
        # Reduce the combined grey results. This introduces an
        # inaccuracy for any comparison of the number of markers
        # against the number of corpus markers, and without extend
        # does not allow for accurate calculation of the number of
        # tokens the results cover (maximum size n-grams are likely to
        # have overlaps). However, it gives a more accurate count of
        # the number of individual markers found, since fewer of them
        # will be counted more than once (again, only maximum size
        # overlapping n-grams could introduce inaccuracies here).
        results = tacl.Results(grey_df, self._tokenizer)
        results.reduce()
        results.csv(grey_path)

    def _generate_grey_markers_for_corpus(self, corpus_label):
        """Generate a results file containing every instance of the
        markers for `corpus_label` in the unclassified works."""
        self._logger.info("Processing {} works against {}".format(
            self._grey_label, corpus_label))
        results_path = self._output_dir / GREY_RESULTS_FILENAME.format(
            corpus_label)
        if results_path.exists():
            self._logger.info("  Output file for results exists; skipping.")
            return
        catalogue = self._catalogue.relabel(
            {self._grey_label: corpus_label})
        corpus_markers_path = \
            self._output_dir / CORPUS_MARKERS_FILENAME.format(corpus_label)
        with open(corpus_markers_path, encoding="utf-8") as fh:
            markers = [line.strip() for line in fh.readlines()]
        with open(results_path, "w", encoding="utf-8") as fh:
            self._data_store.search(catalogue, markers, fh)

    def _generate_report_data(self, df):
        df = df.assign(number_of_markers=1)
        # This is an inaccurate calculation and should be replaced by
        # the slower but more accurate one in remove_markers.py.
        #
        # However, fields involving this data are not output in the
        # final reports, so it doesn't matter at this point.
        df = df.assign(total_size=df[tacl.constants.SIZE_FIELDNAME] *
                       df[tacl.constants.COUNT_FIELDNAME])
        group_cols = [tacl.constants.LABEL_FIELDNAME,
                      tacl.constants.WORK_FIELDNAME,
                      tacl.constants.SIGLUM_FIELDNAME]
        agg_cols = ["total_size", "number_of_markers"]
        siglum_df = df.groupby(group_cols, as_index=False)[agg_cols].agg("sum")
        group_cols = [tacl.constants.LABEL_FIELDNAME,
                      tacl.constants.WORK_FIELDNAME]
        work_df = siglum_df.groupby(group_cols, as_index=False)[agg_cols].agg(
            "mean")
        siglum_df = None
        grey_lengths = self._get_grey_stats()
        work_df = work_df.assign(work_length=lambda x: pd.Series(
            [grey_lengths[work] for work in
             work_df[tacl.constants.WORK_FIELDNAME]]))
        work_df = work_df.assign(
            marker_work_length_ratio=work_df["total_size"] /
            work_df["work_length"])
        # Generate the ratio between the number of markers and the
        # length of the work.
        work_df = work_df.assign(
            markers_to_length=work_df["number_of_markers"] /
            work_df["work_length"])
        # Normalise the markers_to_length value to account for
        # differences in benchmark corpus sizes (and hence the
        # possible number of markers).
        corpora_stats = self._get_corpora_stats()
        maximum_corpus_length = max(corpora_stats.values())
        work_df = work_df.assign(corpus_length=lambda x: pd.Series(
            [corpora_stats[label] for label in
             work_df[tacl.constants.LABEL_FIELDNAME]]))
        work_df = work_df.assign(
            markers_to_length_normalised=work_df["markers_to_length"] *
            maximum_corpus_length / work_df["corpus_length"])
        # Generate a score, which is the normalised markers to length
        # ratio scaled to between 0 and 1.
        max_ratio = work_df["markers_to_length_normalised"].max()
        work_df = work_df.assign(
            score=work_df["markers_to_length_normalised"] / max_ratio)
        output_path = self._output_dir / REPORT_DATA_FILENAME
        work_df.to_csv(output_path, encoding="utf-8", index=False)

    def _get_corpora_stats(self):
        stats_path = self._output_dir / CORPORA_STATS_RESULTS_FILENAME
        stats = {}
        with open(stats_path, encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                corpus = row[CORPORA_STATS_FIELDNAME_CORPUS]
                length = int(row[CORPORA_STATS_FIELDNAME_LENGTH])
                stats[corpus] = length
        return stats

    def _get_grey_stats(self):
        stats_path = self._output_dir / GREY_STATS_RESULTS_FILENAME
        stats = {}
        with open(stats_path, encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                work = row[GREY_STATS_FIELDNAME_WORK]
                length = int(row[GREY_STATS_FIELDNAME_LENGTH])
                stats[work] = length
        return stats

    def _get_corpus_labels(self):
        corpus_labels = self._catalogue.labels
        corpus_labels.remove(self._grey_label)
        self._logger.info("Benchmark corpora labels: {}".format(
            "; ".join(corpus_labels)))
        return corpus_labels

    def _get_work_length(self, work):
        """Return the average length of the witnesses to `work`."""
        witness_lengths = []
        for witness in self._corpus.get_witnesses(name=work):
            witness_lengths.append(len(witness.get_tokens()))
        return sum(witness_lengths) / len(witness_lengths)

    def _link_corpora(self, table):
        for label in self._corpus_labels:
            table = table.replace(
                "<td>{}</td>".format(label),
                '<td><a href="{}.html">{}</a></td>'.format(label, label))
        return table

    def _link_works(self, table):
        for work in self._grey_works:
            table = table.replace(
                "<td>{}</td>".format(work),
                '<td><a href="{}.html">{}</a></td>'.format(work, work))
        return table
