import argparse

from tacl.cli.formatters import ParagraphFormatter
import tacl.cli.utils as utils
import taclextra.paternity


CHILD_LABEL_HELP = '''\
    Label of corpus whose individual works are to be compared.'''
DESCRIPTION = '''\
    Generates a series of results files giving the n-grams in common
    between one corpus and each work in a second corpus, that are not
    present in a third corpus.'''
EPILOG = '''\
    This script performs a 'paternity test' for each work in a corpus
    by finding n-grams that it shares with a second corpus that are
    not found within a third corpus. In the case of authorship
    attribution, these three corpora may be described as:

      A. A benchmark corpus of works for a given figure.

      B. A group of works suspected of belonging to, or somehow aligning
         with, corpus A.

      C. A contrast corpus of works that count as definitively not related
         to A.

    The algorithm is that for each work in B (Bx), a results file is
    generated giving (A asymmetric diff C) supplied intersect Bx.

    These results are then filtered to include only those n-grams that
    occur in at most the user supplied number of works within the
    child corpus.

    Three CSV results files are created in the specified output directory:

      * parent-minus-unrelated.csv - n-grams from the parent corpus
        that do not occur in the unrelated corpus

      * child.csv - all n-grams from the child corpus

      * parent-child.csv - n-grams shared between the previous two
        results, as filtered by the maximum number of works specified '''
MAX_WORKS_HELP = '''\
    Maximum number of works in the child corpus that each result
    n-gram may be found in.'''
OUTPUT_DIR_HELP = 'Directory to output to. It must not already exist.'
PARENT_LABEL_HELP = '''\
    Label of corpus whose n-grams are being matched with the works in
    the CHILD_LABEL corpus.'''
UNRELATED_LABEL_HELP = '''\
    Label of corpus that provides n-grams to be excluded from the
    matches between CHILD and PARENT corpora.'''


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION,
                                     epilog=EPILOG,
                                     formatter_class=ParagraphFormatter)
    utils.add_db_arguments(parser)
    utils.add_tokenizer_argument(parser)
    utils.add_query_arguments(parser)
    parser.add_argument('parent', help=PARENT_LABEL_HELP,
                        metavar='PARENT_LABEL')
    parser.add_argument('child', help=CHILD_LABEL_HELP, metavar='CHILD_LABEL')
    parser.add_argument('unrelated', help=UNRELATED_LABEL_HELP,
                        metavar='UNRELATED_LABEL')
    parser.add_argument('max_works', help=MAX_WORKS_HELP, metavar='MAXIMUM',
                        type=int)
    parser.add_argument('output_dir', help=OUTPUT_DIR_HELP,
                        metavar='DIRECTORY')
    args = parser.parse_args()
    catalogue = utils.get_catalogue(args)
    data_store = utils.get_data_store(args)
    tokenizer = utils.get_tokenizer(args)
    try:
        test = taclextra.paternity.PaternityTest(
            data_store, catalogue, tokenizer, args.parent, args.child,
            args.unrelated, args.max_works, args.output_dir)
        test.process()
    except Exception as e:
        parser.error(e)
