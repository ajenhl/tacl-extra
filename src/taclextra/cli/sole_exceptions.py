"""Generate a set of results files giving "sole exceptions" for each
work in a sub-corpus compared to another sub-corpus.

Requires a catalogue with two labels.

"""

import argparse

import colorlog

import tacl.cli.utils as utils
from taclextra.sole_exceptions import SoleExceptionProcessor


DESCRIPTION = 'Generate "sole exceptions" results files.'
LABEL_HELP = "Label used for sole exception candidates."
MIN_COUNT_HELP = "Minimum number of occurrences within the base corpus for an n-gram to be a candidate sole exception."
MIN_WORKS_HELP = "Minimum number of works within the base corpus for an n-gram to be a candidate sole exception."
NGRAMS_HELP = "Path to file containing known n-grams to be excluded from results."
OUTPUT_HELP = "Path to directory to output results files into."
VERBOSE_HELP = "Log informational messages."


def main():
    parser = generate_parser()
    args = parser.parse_args()
    logger = colorlog.getLogger("tacl")
    if hasattr(args, "verbose"):
        utils.configure_logging(args.verbose, logger)
    catalogue = utils.get_catalogue(args)
    corpus = utils.get_corpus(args)
    tokenizer = utils.get_tokenizer(args)
    store = utils.get_data_store(args)
    exception_label = args.label
    exclude_ngrams = []
    if args.ngrams:
        exclude_ngrams = utils.get_ngrams(args.ngrams)
    min_count = args.min_count
    min_works = args.min_works
    output_dir = args.output
    base_works = [work for work, label in catalogue.items() if
                  label != exception_label]
    exception_works = catalogue.get_works_by_label(exception_label)
    processor = SoleExceptionProcessor(
        store, corpus, tokenizer, base_works, exception_works, min_count,
        min_works, exclude_ngrams, output_dir, logger)
    processor.process_works()


def generate_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    utils.add_common_arguments(parser)
    utils.add_db_arguments(parser)
    utils.add_corpus_arguments(parser)
    utils.add_query_arguments(parser)
    parser.add_argument("--min-count", dest="min_count", help=MIN_COUNT_HELP,
                        default=10)
    parser.add_argument("--min-works", dest="min_works", help=MIN_WORKS_HELP,
                        default=3)
    parser.add_argument("--ngrams", help=NGRAMS_HELP, metavar="NGRAMS")
    parser.add_argument("label", help=LABEL_HELP, metavar="LABEL")
    parser.add_argument("output", help=OUTPUT_HELP, metavar="OUTPUT_DIR")
    return parser


if __name__ == "__main__":
    main()
