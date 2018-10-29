#!/usr/bin/env python3

import argparse
import logging

from tacl.command.formatters import ParagraphFormatter
import tacl.command.utils
from taclextra import paired_intersector


DESCRIPTION = """\
    Produces intersect results files for every pair of labelled texts
    in the supplied catalogue."""
EPILOG = """\
    This process can take an extremely long time if the number of
    works in the catalogue is large. The process has been designed to
    track which intersections have been done, so the process can be
    killed and then rerun, by pointing to the same tracking file and
    output directory.

    If DATABASE is "memory", individual in-memory databases will be
    created for each pair. This can be much more performant than using
    a single database that includes data from all of the works in the
    corpus.

    Results are extended and reduced."""
MAXIMUM_HELP = 'Maximum size of n-grams to generate, if DATABASE is "memory".'
MINIMUM_HELP = 'Minimum size of n-grams to generate, if DATABASE is "memory".'


def main():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, epilog=EPILOG,
        formatter_class=ParagraphFormatter)
    parser.add_argument('--min_size', default=1, help=MINIMUM_HELP,
                        metavar='MINIMUM', type=int)
    parser.add_argument('--max_size', default=10, help=MAXIMUM_HELP,
                        metavar='MAXIMUM', type=int)
    tacl.command.utils.add_common_arguments(parser)
    tacl.command.utils.add_db_arguments(parser)
    tacl.command.utils.add_corpus_arguments(parser)
    tacl.command.utils.add_query_arguments(parser)
    parser.add_argument('output_dir', help='Path to output directory',
                        metavar='DIRECTORY')
    parser.add_argument('tracker_path', help='Path to tracking file',
                        metavar='TRACKING')
    args = parser.parse_args()
    logger = logging.getLogger('taclextra')
    if hasattr(args, 'verbose'):
        tacl.command.utils.configure_logging(args.verbose, logger)
    corpus = tacl.command.utils.get_corpus(args)
    if args.db == 'memory':
        data_store = None
    else:
        data_store = tacl.command.utils.get_data_store(args)
    tokenizer = tacl.command.utils.get_tokenizer(args)
    catalogue = tacl.command.utils.get_catalogue(args)
    pi = paired_intersector.PairedIntersector(
        data_store, corpus, tokenizer, catalogue, args.output_dir,
        args.tracker_path, args.min_size, args.max_size)
    pi.intersect_all()
