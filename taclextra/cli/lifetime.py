"""Loop over (ordered) labels in catalogue:

  * Create new catalogue (earlier-current) containing all files in
    earlier labels under one label, and current label as is, with
    later labels removed. Any user-specified labels are first moved to
    the end of the catalogue.

  * Asymmetric diff based on earlier-current catalogue (INTRODUCED
    TERMS).

  * Create new catalogue (current-later) containing all files in later
    labels under one label, and current label as is, with earlier
    labels removed. Any user-specified labels are first moved to the
    end of the catalogue.

  * Asymmetric diff based on current-later catalogue (END OF LIFE
    TERMS).

  * Intersect based on current-later catalogue (FULL CONTINUED USE TERMS;
    interim only).

  * Supplied intersect of INTRODUCED TERMS with FULL CONTINUED USE
    (CONTINUED USE TERMS).

Concatenate into single results file the individual results INTRODUCED
TERMS, CONTINUED USE TERMS, and END OF LIFE TERMS.

Replace the labels used in the results file with the proper ones from
the original catalogue.

Generate HTML report with orderable columns: "introduced",
"continued", "end of life", "only appeared".

Change to have two catalogues supplied.

Display by n-gram, by text.

"""

import argparse
import os

import tacl.cli.utils as utils
from taclextra import lifetime

DESCRIPTION = '''\
    Generates results data and a report showing the lifetime of
    n-grams that come into or fall out of use in a group of
    corpora.'''
HELP_OUTPUT = 'Directory to output to.'


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    utils.add_db_arguments(parser)
    utils.add_tokenizer_argument(parser)
    utils.add_query_arguments(parser)
    parser.add_argument('output', help=HELP_OUTPUT, metavar='DIRECTORY')
    args = parser.parse_args()
    data_store = utils.get_data_store(args)
    catalogue = utils.get_catalogue(args)
    tokenizer = utils.get_tokenizer(args)
    output_dir = os.path.abspath(args.output)
    reporter = lifetime.LifetimeReporter(data_store, catalogue, tokenizer,
                                         output_dir)
    reporter.process()
