#!/usr/bin/env python3

import argparse
import logging

from tacl.command.formatters import ParagraphFormatter
import tacl.command.utils
from taclextra import paired_intersector


DESCRIPTION = """\
    Produces intersect results files for every pair of texts in the
    supplied corpus."""
EPILOG = """\
    This process can take an extremely long time if the number of
    works in the corpus is large. The process has been designed to
    track which intersections have been done, so the process can be
    killed and then rerun, by pointing to the same tracking file and
    output directory.

    Results are extended and reduced."""


def main():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, epilog=EPILOG,
        formatter_class=ParagraphFormatter)
    tacl.command.utils.add_common_arguments(parser)
    tacl.command.utils.add_db_arguments(parser)
    tacl.command.utils.add_corpus_arguments(parser)
    parser.add_argument('output_dir', help='Path to output directory',
                        metavar='DIRECTORY')
    parser.add_argument('tracker_path', help='Path to tracking file',
                        metavar='TRACKING')
    args = parser.parse_args()
    logger = logging.getLogger('taclextra')
    if hasattr(args, 'verbose'):
        tacl.command.utils.configure_logging(args.verbose, logger)
    corpus = tacl.command.utils.get_corpus(args)
    data_store = tacl.command.utils.get_data_store(args)
    tokenizer = tacl.command.utils.get_tokenizer(args)
    pi = paired_intersector.PairedIntersector(
        data_store, corpus, tokenizer, args.output_dir, args.tracker_path)
    pi.intersect_all()
