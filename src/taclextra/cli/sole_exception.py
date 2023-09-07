import argparse
from pathlib import Path

import colorlog

import pandas as pd

from tacl.cli import utils
from tacl.cli.formatters import ParagraphFormatter
from taclextra.sole_exception import SEProcessor


DESCRIPTION = "Generate sole exception data and reports for unclassified works against benchmark corpora."
EPILOG = """The catalogue must have at least two labels, one of which that specified by the --label option.

If the supplied output directory already contains base data files (ie, not the reports), these will not be regenerated.

The --work-data option allows for extra columns of data to be added to the report tables, immediately following the "work" column. A CSV file referenced by this option must have a header row, with one of the fields called "work" with values matching the names of the unclassified works in the catalogue. The other labelled fields will be added as columns with the same name in the report tables.

The data this command generates are kept in the specified output directory, and will be reused if the command is run again with the same output directory. The reports are output into the \"reports\" subdirectory of the output directory."""
LABEL_HELP = "Label for unclassified works to analyse"
LABEL_NOT_IN_CATALOGUE_ERROR = "Label for unclassified works does not exist in the supplied catalogue"
OUTPUT_DIR_HELP = "Path to directory where results will be written"
WORK_COLUMN_NOT_IN_CSV_ERROR = 'There must be a "work" field in the supplied CSV file'
WORK_DATA_HELP = "Path to CSV file containing additional data for each unclassified work"


logger = colorlog.getLogger("tacl")


def main():
    parser = generate_parser()
    args = parser.parse_args()
    data_store = utils.get_data_store(args)
    corpus = utils.get_corpus(args)
    catalogue = utils.get_catalogue(args)
    tokenizer = utils.get_tokenizer(args)
    grey_label = args.label
    if grey_label not in catalogue.labels:
        parser.error(LABEL_NOT_IN_CATALOGUE_ERROR)
    output_dir = args.output_dir
    output_dir.mkdir(exist_ok=True, parents=True)
    extra_work_df = get_extra_work_data(parser, args.work_data)
    if hasattr(args, "verbose"):
        utils.configure_logging(args.verbose, logger)
    processor = SEProcessor(data_store, corpus, catalogue, tokenizer,
                            grey_label, output_dir, extra_work_df)
    processor.generate_corpora_stats()
    processor.generate_corpora_markers()
    processor.generate_grey_markers()
    processor.filter_markers()
    processor.generate()


def generate_parser():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, epilog=EPILOG,
        formatter_class=ParagraphFormatter)
    parser.add_argument("-l", "--label", default="grey", help=LABEL_HELP)
    parser.add_argument("--work-data", help=WORK_DATA_HELP)
    utils.add_common_arguments(parser)
    utils.add_db_arguments(parser)
    utils.add_corpus_arguments(parser)
    utils.add_query_arguments(parser)
    parser.add_argument("output_dir", help=OUTPUT_DIR_HELP, metavar="OUTPUT",
                        type=Path)
    return parser


def get_extra_work_data(parser, path):
    if path is None:
        return None
    df = pd.read_csv(path)
    if "work" not in df:
        parser.error(WORK_COLUMN_NOT_IN_CSV_ERROR)
    return df


if __name__ == "__main__":
    main()
