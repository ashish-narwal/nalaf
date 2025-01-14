import argparse
import os

import pkg_resources

from nalaf.utils.readers import TextFilesReader, PMIDReader
from nalaf.utils.readers import StringReader
from nalaf.utils.writers import ConsoleWriter, TagTogFormat, PubTatorFormat
from nalaf.structures.dataset_pipelines import PrepareDatasetPipeline
from nalaf.learning.crfsuite import PyCRFSuite
from nalaf.domain.bio.gnormplus import GNormPlusGeneTagger
from nalaf.learning.taggers import StubSameSentenceRelationExtractor


ENT1_CLASS_ID = 'e_x'
ENT2_CLASS_ID = 'e_y'
REL_ENT1_ENT2_CLASS_ID = 'r_z'
ENTREZ_GENE_ID = 'n_w'
UNIPROT_ID = 'n_v'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple demo for using the nalaf pipeline for prediction')

    parser.add_argument('--color', help='uses color for highlighting predictions if supported '
                                        'otherwise prints them in new line',
                        action='store_true', default=True, dest='color')
    parser.add_argument('--no_color', help='prints predictions in new line',
                        action='store_false', dest='color')

    parser.add_argument('-o', '--output_dir', help='write the output to the provided directory, '
                                                   'the format can be specified with the -f switch, '
                                                   'otherwise the output will be written to the standard console')
    parser.add_argument('-f', '--file_format', help='the format for writing the output to a directory',
                        choices=['ann.json', 'pubtator'], default='ann.json')

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('-s', '--string', help='string you want to predict for')
    group.add_argument('-d', '--dir_or_file', help='directory or file you want to predict for')
    group.add_argument('-p', '--pmids', nargs='+', help='a single PMID or a list of PMIDs separated by space')
    args = parser.parse_args()

    warning = 'Due to a dependence on GNormPlus, running nalaf with -s and -d switches might take a long time.'
    if args.string:
        print(warning)
        dataset = StringReader(args.string).read()
    elif args.pmids:
        dataset = PMIDReader(args.pmids).read()
    elif os.path.exists(args.dir_or_file):
        print(warning)
        dataset = TextFilesReader(args.dir_or_file).read()
    else:
        raise FileNotFoundError('directory or file "{}" does not exist'.format(args.dir_or_file))

    PrepareDatasetPipeline().execute(dataset)

    # get the predictions -- "example_entity_model" is only available in the nalaf src distribution
    crf = PyCRFSuite(model_file=pkg_resources.resource_filename('nalaf.data', 'example_entity_model'))
    crf.annotate(dataset, class_id=ENT2_CLASS_ID)

    GNormPlusGeneTagger(ENT1_CLASS_ID, ENTREZ_GENE_ID, UNIPROT_ID).tag(dataset, uniprot=True)
    StubSameSentenceRelationExtractor(ENT1_CLASS_ID, ENT2_CLASS_ID, REL_ENT1_ENT2_CLASS_ID).annotate(dataset)

    if args.output_dir:
        if not os.path.isdir(args.output_dir):
            raise NotADirectoryError('{} is not a directory'.format(args.output_dir))

        if args.file_format == 'ann.json':
            TagTogFormat(dataset, use_predicted=True, to_save_to=args.output_dir).export(threshold_val=0)
        elif args.file_format == 'pubtator':
            PubTatorFormat(dataset, location=os.path.join(args.output_dir, 'pubtator.txt')).export()
    else:
        ConsoleWriter(ENT1_CLASS_ID, ENT2_CLASS_ID, args.color).write(dataset)
