from .base_tokenize import tokenize

def load_default_molecule_name_tokens(molecule_name_token_patterns=None):
    if molecule_name_token_patterns is None:
        func_name_options = ['carboxylate', 'phosphate', 'isopropyl', 'azetidin', 'methoxy', 'benzene', 'methane', 'propane', 'uronium',
                            'ethane', 'phenyl', 'chloro', 'fluoro', 'methyl', 'propan', 'benzyl', 'hydryl', 'thione', 'sodium',
                            'butan', 'butyl', 'hydro', 'carbo', 'tetra', 'allyl', 'sulfo', 'azete', 'amido', 'pival', 'olate',
                            'thio', 'tert', 'benz', 'nate', 'piva', 'late', 'loyl', 'azin', 'hexa',
                            'ace', 'tri', 'oxy', 'oxo', 'one', 'hyl', 'ane', 'ate', 'tol', 'tyl', 'bis', 'nyl',
                            'ol', 'di', 'en', 'yl']
        lower_case_patterns = r'|'.join(func_name_options)
        upper_case_patterns = r'|'.join([func_name.capitalize() for func_name in func_name_options])

# 2-(4,6-Dimethoxy-1,3,5-triazin-2-yl)-1,1,3,3-tetramethyluronium hexafluorophosphate

        token_patterns = [
                        ('FUNC_GROUP_NAMES', lower_case_patterns+r'|'+upper_case_patterns),
                        ('NUM', r'\-\d+,\d+,\d+\-|\-\d+,\d+\-|\-\d+\-|\d+\-|\-\d+'),
                        ('STERIC_CENTERS', r'\(\d*S\)|\(\d*R\)|\(\d*E\)|\(\d*Z\)'),
                        ('WHITESPACE', r'\s+'),
                        ]
    else:
        token_patterns = molecule_name_token_patterns
    return token_patterns

def get_molecule_name_probability(word, molecule_name_token_patterns=None, debugging=False):
    if word:
        molecule_name_token_patterns = load_default_molecule_name_tokens(molecule_name_token_patterns)
        word_tokens = tokenize(word, molecule_name_token_patterns, debugging)
        len_tokens = sum(map(len, word_tokens))
        word_prob = 100*len_tokens/len(word)
    else:
        word_prob = 0
    return word_prob