import abc
from nalaf.structures.data import *
from nltk.stem.lancaster import LancasterStemmer
from nltk.corpus import stopwords
from progress.bar import Bar
from spacy.en import English


class Parser:
    """
    Abstract class for generating parse tree for each sentence.
    Subclasses that inherit this class should:
    * Be named [Name]ParseTree
    * Implement the abstract method parse
    * Append new items to the list field "edges" of each Part in the dataset
    """

    @abc.abstractmethod
    def parse(self, dataset):
        """
        :type dataset: nalaf.structures.data.Dataset
        """
        return


class SpacyParser(Parser):
    """
    Implementation of the SpaCy English for parsing the each sentence in each
    part separately, finding dependencies, parts of speech tags, lemmas and
    head words for each entity.

    :param nlp: an instance of spacy.en.English
    :type nlp: spacy.en.English
    :param constituency_parser: the constituency parser to use to generate
        syntactic (constituency) parse trees. Currently, supports only 'bllip'.
    :type constituency_parser: str
    """

    def __init__(self, nlp, constituency_parser=False):
        self.nlp = nlp
        """an instance of spacy.en.English"""
        self.constituency_parser = constituency_parser
        """the type of constituency parser to use, current supports only bllip"""
        # NOTE: SpaCy may soon have its own constituency parser: https://github.com/explosion/spaCy/issues/59

        if (not isinstance(self.nlp, English)):
            raise TypeError('Not an instance of spacy.en.English')

        if self.constituency_parser is True:
            self.parser = BllipParser(only_parse=True)


    def parse(self, dataset):
        """
        :type dataset: nalaf.structures.data.Dataset
        """
        outer_bar = Bar('Processing [SpaCy]', max=len(list(dataset.parts())))
        for part in dataset.parts():

            for sent_index, sentence in enumerate(part.sentences):

                sentence_tokens = [nalaf_token.word for nalaf_token in sentence]
                nlp_spacy_doc = self.nlp.tokenizer.tokens_from_list(sentence_tokens)

                for spacy_token in nlp_spacy_doc:
                    nalaf_token = part.sentences[sent_index][spacy_token.i]
                    nalaf_token.features = {
                        'id': spacy_token.i,
                        'pos': spacy_token.tag_,
                        'dep': spacy_token.dep_,
                        'lemma': spacy_token.lemma_,
                        'prob': spacy_token.prob,
                        'is_punct': spacy_token.is_punct,
                        'is_stop': spacy_token.is_stop,
                        'cluster': spacy_token.cluster,
                        'dependency_from': None,
                        'dependency_to': [],
                        'is_root': False,
                    }

                    part.tokens.append(nalaf_token)

                for spacy_token in nlp_spacy_doc:
                    self._dependency_path(spacy_token, sent_index, part)

            part.percolate_tokens_to_entities()
            part.calculate_token_scores()
            part.set_head_tokens()
            outer_bar.next()

        outer_bar.finish()

        if self.constituency_parser is True:
            self.parser.parse(dataset)


    def _dependency_path(self, spacy_token, sent_index, part):
        nalaf_token = part.sentences[sent_index][spacy_token.i]
        nalaf_token_from = part.sentences[sent_index][spacy_token.head.i]

        nalaf_token.features['dependency_from'] = (nalaf_token_from, spacy_token.dep_)

        if (spacy_token.i == spacy_token.head.i):
            nalaf_token.features['is_root'] = True
        else:
            nalaf_token_from.features['dependency_to'].append((nalaf_token, spacy_token.dep_))


class BllipParser(Parser):
    """
    Implementation of the bllipparser for parsing the each sentence in each
    part separately, finding dependencies, parts of speech tags, lemmas and
    head words for each entity.

    Uses preprocessed text

    :param nbest: the number of parse trees to obtain
    :type nbest: int
    :param overparsing: overparsing determines how much more time the parser
        will spend on a sentence relative to the time it took to find the
        first possible complete parse
    :type overparsing: int
    """
    def __init__(self, nbest=10, overparsing=10, only_parse=False, stop_words=None):
        try:
            from bllipparser import RerankingParser
            # WARNING if only_parse=False, BllipParser depends on PyStanfordDependencies: pip install PyStanfordDependencies
        except ImportError:
            raise ImportError('BllipParser not installed, perhaps it is not supported on OS X yet')

        self.parser = RerankingParser.fetch_and_load('GENIA+PubMed', verbose=True)
        # WARNING this can take a long while. Install manually: `python -mbllipparser.ModelFetcher -i GENIA+PubMed`

        """create a Reranking Parser from BllipParser"""
        self.parser.set_parser_options(nbest=nbest, overparsing=overparsing)
        """set parser options"""
        self.only_parse=only_parse
        """whether features should be used from the BllipParser"""
        self.stemmer = LancasterStemmer()
        """an instance of LancasterStemmer from NLTK"""
        self.stop_words = stop_words
        if self.stop_words is None:
            self.stop_words = stopwords.words('english')


    def parse(self, dataset):
        outer_bar = Bar('Processing [Bllip]', max=len(list(dataset.parts())))
        for part in dataset.parts():
            outer_bar.next()
            if len(part.sentence_parse_trees)>0:
                continue
            for index, sentence in enumerate(part.sentences):
                sentence = [token.word for token in part.sentences[index]]
                parse = self.parser.parse(sentence)
                parsed = parse[0]
                part.sentence_parse_trees.append(str(parsed.ptb_parse))
                if not self.only_parse:
                    tokens = parsed.ptb_parse.sd_tokens()
                    for token in tokens:
                        tok = part.sentences[index][token.index-1]
                        is_stop = False
                        if tok.word.lower() in self.stop_words:
                            is_stop = True
                        tok.features = {
                                        'id': token.index-1,
                                        'pos': token.pos,
                                        'lemma': self.stemmer.stem(tok.word),
                                        'is_punct': self._is_punct(tok.word),
                                        'dep': token.deprel,
                                        'is_stop': is_stop,
                                        'dependency_from': None,
                                        'dependency_to': [],
                                        'is_root': False,
                                        }
                        part.tokens.append(tok)

                    for token in tokens:
                        tok = part.sentences[index][token.index-1]
                        self._dependency_path(token, tok, part, index)

            part.percolate_tokens_to_entities()
            part.calculate_token_scores()
            part.set_head_tokens()

        outer_bar.finish()


    def _dependency_path(self, bllip_token, token, part, index):
        if bllip_token.head-1>=0:
            token.features['dependency_from'] = (part.sentences[index][bllip_token.head-1], bllip_token.deprel)
        else:
            token.features['dependency_from'] = (part.sentences[index][token.features['id']], bllip_token.deprel)
        token_from = part.sentences[index][bllip_token.head-1]
        if (bllip_token.index != bllip_token.head):
            token_from.features['dependency_to'].append((token, bllip_token.deprel))
        else:
            token.features['is_root'] = True


    def _is_punct(self, text):
        if text in ['.', ',', '-']:
            return True
        return False
