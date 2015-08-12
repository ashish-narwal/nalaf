from nala.features import FeatureGenerator
import re


class TmVarFeatureGenerator(FeatureGenerator):
    """
    Generates tmVar CRF features based on the value of the token itself.
    * w[0] = the value of the words itself
    This FeatureGenerator mainly uses Regular Expressions (which are initialized in the constructor).
    The generate function iterates over the dataset and creates the features which all get separately created in their own function.

    Hints:
    - when a feature is not found (as in: regex don't apply) then the feature gets the value None.

    Implements the abstract class FeatureGenerator.
    """
    def __init__(self):
        """
        Contains all regular expressions.
        """
        self.reg_spec_chars = re.compile('[-;:,.>+_]')
        self.reg_chr_keys = re.compile('(q|p|q[0-9]+|p[0-9]+|qter|pter|XY|t)')
        self.reg_char_simple_bracket = re.compile('[\(\)]')
        self.reg_char_square_bracket = re.compile('[\[\]]')
        self.reg_char_curly_bracket = re.compile('[\{\}]')
        self.reg_char_slashes = re.compile('[\/\\\]')
        self.reg_mutat_type = re.compile('(del|ins|dup|tri|qua|con|delins|indel)')
        self.reg_frameshift_type = re.compile('(fs|fsX|fsx)')
        self.reg_mutat_word = re.compile(
            '(deletion|delta|elta|insertion|repeat|inversion|deletions|insertions|repeats|inversions)')
        self.reg_mutat_article = re.compile(
            '(single|a|one|two|three|four|five|six|seven|eight|nine|ten|[0-9]+|[0-9]+\.[0-9]+)')
        self.reg_mutat_byte = re.compile('(kb|mb)')
        self.reg_mutat_basepair = re.compile(
            '(base|bases|pair|amino|acid|acids|codon|postion|postions|bp|nucleotide|nucleotides)')
        self.reg_type1 = re.compile('[cgrm]$')
        self.reg_type12 = re.compile('(ivs|ex|orf)$')
        self.reg_dna_symbols = re.compile('[ATCGUatcgu]$')
        self.reg_prot_symbols1 = re.compile(
            '(glutamine|glutamic|leucine|valine|isoleucine|lysine|alanine|glycine|aspartate|methionine|threonine|histidine|aspartic|asparticacid|arginine|asparagine|tryptophan|proline|phenylalanine|cysteine|serine|glutamate|tyrosine|stop|frameshift)')
        self.reg_prot_symbols2 = re.compile(
            '(cys|ile|ser|gln|met|asn|pro|lys|asp|thr|phe|ala|gly|his|leu|arg|trp|val|glu|tyr|fs|fsx)$')
        self.reg_prot_symbols3 = re.compile('(ys|le|er|ln|et|sn|ro|ys|sp|hr|he|la|ly|is|eu|rg|rp|al|lu|yr)$')
        self.reg_prot_symbols4 = re.compile('[CISQMNPKDTFAGHLRWVEYX]$')
        self.reg_rs_code1 = re.compile('(rs|RS|Rs)[0-9]')
        self.reg_rs_code2 = re.compile('(rs|RS|Rs)$')

        # patterns
        self.reg_shape_uc = re.compile('[A-Z]')
        self.reg_shape_uc_plus = re.compile('[A-Z]+')

        self.reg_shape_lc = re.compile('[a-z]')
        self.reg_shape_lc_plus = re.compile('[a-z]+')

        self.reg_shape_nr = re.compile('[0-9]')
        self.reg_shape_nr_plus = re.compile('[0-9]+')

        self.reg_shape_chars = re.compile('[A-Za-z]')
        self.reg_shape_chars_plus = re.compile('[A-Za-z]+')

    def generate(self, dataset):
        """
        :type dataset: nala.structures.data.Dataset
        """
        last_token_str = ""
        for token in dataset.tokens():

            token.features['num_nr[0]'] = self.num_digits_chars(token.word)

            token.features['num_up[0]'] = self.num_capital_chars(token.word)

            token.features['num_lo[0]'] = self.num_lower_chars(token.word)

            token.features['num_alpha[0]'] = self.num_chars(token.word)

            token.features['num_spec_chars[0]'] = self.num_spec_chars(token.word)

            token.features['num_has_chr_key[0]'] = self.has_chromosomal_keytokens(token.word)

            token.features['mutat_type[0]'] = self.mutation_type(token.word)

            token.features['mutat_word[0]'] = self.mutation_word(token.word)

            token.features['mutat_article_bp[0]'] = self.mutation_article_bp(token.word)

            token.features['type1[0]'] = self.is_special_type_1(token.word)

            token.features['type2[0]'] = self.is_special_type_2(token.word)

            token.features['dna_symbols[0]'] = self.has_dna_symbols(token.word)

            token.features['protein_symbols[0]'] = self.has_protein_symbols(token.word, last_token_str)

            token.features['rs_code[0]'] = self.has_rscode(token.word)

            token.features['shape1[0]'] = self.word_shape_1(token.word)
            token.features['shape2[0]'] = self.word_shape_2(token.word)
            token.features['shape3[0]'] = self.word_shape_3(token.word)
            token.features['shape4[0]'] = self.word_shape_4(token.word)

            # prefix patterns
            for index, value in enumerate(self.prefix_pattern(token.word)):
                token.features['prefix{}[0]'.format(index+1)] = value

            # suffix patterns
            for index, value in enumerate(self.suffix_pattern(token.word)):
                token.features['suffix{}[0]'.format(index+1)] = value

            # last token
            last_token_str = token.word

    def num_lower_chars(self, str):
        result = sum(1 for c in str if c.islower())
        return "L4+" if result > 4 else result

    def num_capital_chars(self, str):
        result = sum(1 for c in str if c.isupper())
        return "U4+" if result > 4 else result

    def num_digits_chars(self, str):
        result = sum(1 for c in str if c.isnumeric())
        return "N4+" if result > 4 else result

    def num_chars(self, str):
        result = sum(1 for c in str if c.isalpha())
        return "A4+" if result > 4 else result

    def num_spec_chars(self, str):
        if self.reg_spec_chars.search(str):
            return "SpecC1"
        elif self.reg_char_simple_bracket.search(str):
            return "SpecC2"
        elif self.reg_char_curly_bracket.search(str):
            return "SpecC3"
        elif self.reg_char_square_bracket.search(str):
            return "SpecC4"
        elif self.reg_char_slashes.search(str):
            return "SpecC5"
        else:
            return None

    def has_chromosomal_keytokens(self, str):
        return "ChroKey" if self.reg_chr_keys.search(str) else None

    def mutation_type(self, str):
        lc_tmp = str.lower()

        if self.reg_frameshift_type.search(lc_tmp):
            return "FrameShiftType"
        elif self.reg_mutat_type.search(lc_tmp):
            return "MutatType"
        else:
            return None

    def mutation_word(self, str):
        lc_tmp = str.lower()
        return "MutatWord" if self.reg_mutat_word.match(lc_tmp) else None

    def mutation_article_bp(self, str):
        mutat_article = ""  # NOTE is this programming ok?
        lc_tmp = str.lower()

        # NOTE was if -> base | if -> byte | elif -> bp | else -> None
        if self.reg_mutat_article.match(lc_tmp):
            mutat_article = "Base"
        elif self.reg_mutat_byte.search(lc_tmp):
            mutat_article = "Byte"
        elif self.reg_mutat_basepair.search(lc_tmp):
            mutat_article = "bp"
        else:
            mutat_article = None

        return mutat_article

    def is_special_type_1(self, str):
        if self.reg_type1.match(str):
            return "Type1"
        elif self.reg_type12.match(str):
            return "Type1_2"
        else:
            return None

    def is_special_type_2(self, str):
        return "Type2" if str == "p" else None

    def has_dna_symbols(self, str):
        return "DNASym" if self.reg_dna_symbols.match(str) else None

    def has_protein_symbols(self, str, last_str):
        uc_tmp = str  # upper case
        lc_tmp = str.lower()  # lower case

        if self.reg_prot_symbols1.search(lc_tmp):
            return "ProteinSymFull"
        elif self.reg_prot_symbols2.match(lc_tmp):
            return "ProteinSymTri"
        elif self.reg_prot_symbols3.match(lc_tmp) and self.reg_prot_symbols4.match(last_str):
            return "ProteinSymTriSub"
        elif self.reg_prot_symbols4.match(uc_tmp):
            return "ProteinSymChar"
        else:
            return None

    def has_rscode(self, str):
        if self.reg_rs_code1.match(str):
            return "RSCode"
        elif self.reg_rs_code2.match(str):
            return "RSCode"
        else:
            return None

    def word_shape_1(self, str):
        if not self.reg_spec_chars.match(str):
            pattern = self.reg_shape_uc.sub('A', str)
            pattern = self.reg_shape_lc.sub('a', pattern)
            pattern = self.reg_shape_nr.sub('0', pattern)
            return pattern
        return None

    def word_shape_2(self, str):
        if not self.reg_spec_chars.match(str):
            pattern = self.reg_shape_chars.sub('a', str)
            pattern = self.reg_shape_nr.sub('0', pattern)
            return pattern
        return None

    def word_shape_3(self, str):
        if not self.reg_spec_chars.match(str):
            pattern = self.reg_shape_uc_plus.sub('A', str)
            pattern = self.reg_shape_lc_plus.sub('a', pattern)
            pattern = self.reg_shape_nr_plus.sub('0', pattern)
            return pattern
        return None

    def word_shape_4(self, str):
        if not self.reg_spec_chars.match(str):
            pattern = self.reg_shape_chars_plus.sub('a', str)
            pattern = self.reg_shape_nr_plus.sub('0', pattern)
            return pattern
        return None

    def prefix_pattern(self, str):
        prefix_array = []
        for x in range(1, 6):
            if len(str) >= x:
                prefix_array.append(str[:x])
            else:
                prefix_array.append(None)
        return prefix_array


    def suffix_pattern(self, str):
        suffix_array = []
        for x in range(1, 6):
            if len(str) >= x:
                suffix_array.append(str[-x:])
            else:
                suffix_array.append(None)
        return suffix_array

    # NOTE as array
    # NOTE discussion: should it be visible? P1:[pattern] or just [pattern] --> i would prefer visibility to actually be able to debug the results (but more data) --> still not decided but unimportant right now


class TmVarDictionaryFeatureGenerator(FeatureGenerator):
    """
    Implementation of the so called Dictionary Features from tmVar.

    Following the HGVS mutation nomenclature, tmVar developed 11 (7 for genomic and 4 for protein mutations)
    regular expressions patterns. For each part in our dataset we perform matching on the part.text field
    with each of the 11 regular expression patterns.

    When there is a match, each token in the corresponding matched text will be assigned to one of the three values
    (B/I/E) for that feature (B for the beginning token; E for the last token and I for any other tokens in
    between B and E). Any token that is not matched against these patterns will have the value of 'O' for this feature.

    The names of dictionary features are pattern0[0], pattern1[0], ..., pattern10[0]
    corresponding to the 11 regex patterns.

    Implements the abstract class FeatureGenerator.
    """
    def __init__(self):
        self.patterns = [
            re.compile('([cgrm]\.[ATCGatcgu \/\>\<\?\(\)\[\]\;\:\*\_\-\+0-9]+(inv|del|ins|dup|tri|qua|con|delins|indel)[ATCGatcgu0-9\_\.\:]*)'),
            re.compile('(IVS[ATCGatcgu \/\>\<\?\(\)\[\]\;\:\*\_\-\+0-9]+(del|ins|dup|tri|qua|con|delins|indel)[ATCGatcgu0-9\_\.\:]*)'),
            re.compile('([cgrm]\.[ATCGatcgu \/\>\?\(\)\[\]\;\:\*\_\-\+0-9]+)'),
            re.compile('(IVS[ATCGatcgu \/\>\?\(\)\[\]\;\:\*\_\-\+0-9]+)'),
            re.compile('([cgrm]\.[ATCGatcgu][0-9]+[ATCGatcgu])'),
            re.compile('([ATCGatcgu][0-9]+[ATCGatcgu])'),
            re.compile('([0-9]+(del|ins|dup|tri|qua|con|delins|indel)[ATCGatcgu]*)'),
            re.compile('([p]\.[CISQMNPKDTFAGHLRWVEYX \/\>\<\?\(\)\[\]\;\:\*\_\-\+0-9]+(inv|del|ins|dup|tri|qua|con|delins|indel|fsX|fsx|fsx|fs)[CISQMNPKDTFAGHLRWVEYX \/\>\<\?\(\)\[\]\;\:\*\_\-\+0-9]*)'),
            re.compile('([p]\.[CISQMNPKDTFAGHLRWVEYX \/\>\?\(\)\[\]\;\:\*\_\-\+0-9]+)'),
            re.compile('([p]\.[A-Z][a-z]{0,2}[\W\-]{0,1}[0-9]+[\W\-]{0,1}[A-Z][a-z]{0,2})'),
            re.compile('([p]\.[A-Z][a-z]{0,2}[\W\-]{0,1}[0-9]+[\W\-]{0,1}(fs|fsx|fsX))')]

    def generate(self, dataset):
        """
        :type dataset: nala.structures.data.Dataset
        """
        for part in dataset.parts():
            so_far = 0
            matches = {}

            for index, pattern in enumerate(self.patterns):
                matches[index] = []
                for match in pattern.finditer(part.text):
                    matches[index].append((match.start(), match.end()))

            for sentence in part.sentences:
                for token in sentence:
                    so_far = part.text.find(token.word, so_far)  # so_far = token_start
                    token_end = so_far + len(token.word)

                    for match_index, match in matches.items():
                        token.features['pattern{}[0]'.format(match_index)] = 'O'
                        for start, end in match:
                            if start == so_far:
                                name = 'pattern{}[0]'.format(match_index)
                                token.features.pop(name)
                                token.features[name] = 'B'
                                break
                            elif start < so_far < token_end < end:
                                name = 'pattern{}[0]'.format(match_index)
                                token.features.pop(name)
                                token.features[name] = 'I'
                                break
                            elif token_end == end:
                                name = 'pattern{}[0]'.format(match_index)
                                token.features.pop(name)
                                token.features[name] = 'E'
                                break

