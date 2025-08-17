import re

def load_default_replacement_tokens(replacement_token_patterns=None, replacement_dict=None):
    if replacement_token_patterns is None:
        possible_multiplicity = ['s', 'd', 't', 'q']
        uppercase_multiplicity = '|'.join([multiply.upper()+r'\s*,\s*J\s*=' for multiply in possible_multiplicity])
        token_patterns = [
            ('H_NMR', r'\[1H\]\s*NMR|\d+\%*\)\.*1H NMR|\);1H NMR|\d+\.1H NMR|\°\)1H NMR|^.*\)*\.*1H NMR|lH NMR|21H NMR|\(13\):1H NMR'), # [1H] NMR|X{%*}).1H NMR|);1H NMR|X.1H NMR|°)1H NMR|S{)*}{.*}1H NMR 
            ('F_NMR', r'19F\(H\) NMR|^.*\)*\.*19F NMR'), # 19F(H) NMR|{1H} NMR|S{)*}{.*}19F NMR
            ('C_NMR', r'H-\d+\)\;*13C NMR|\d+H\)[\;\.]*13C NMR|H\d+\)\.*13C NMR|^.*\)*\.*13C NMR|13C\}1H\} NMR|141 NMR'), # H-X);13C NMR|XH).13C NMR|HX).13C NMR|S{)*}{.*}13C NMR
            ('NOTES1', r'O10298OOOTBS3142Appendix A:| 43NH 51016OO1112678Me92Me\d+| 1211OO1610NH 53417Me182Me\d+|N OCO2allylCO2MeN|NMeO2CONMeO2CO2N\d+|' +
                    r'OCO2allylCO2MeO\d+|Ph2SiHOPh2SiOPh2SiOH\d+|61    '), #  # 
            ('UPPERCASE_MULTIPLICITY', uppercase_multiplicity)
            ]
    else:
        token_patterns = replacement_token_patterns
    if replacement_dict is None:
        replacement_dict = {'H_NMR' : r'1H NMR',
            'F_NMR': r'19F NMR',
            'C_NMR': r'13C NMR',
            'NOTES1': r'/)',
            }
    return token_patterns, replacement_dict

possible_multiplicity = ['s', 'd', 't', 'q']
uppercase_multiplicity = '|'.join([multiply.upper()+r'\s*,\s*J\s*=' for multiply in possible_multiplicity])

REPLACEMENT_PATTERNS = [
    ('H_NMR', r'\[1H\]\s*NMR|\d+\%*\)\.*1H NMR|\);1H NMR|\d+\.1H NMR|\°\)1H NMR|^.*\)*\.*1H NMR|lH NMR|21H NMR|\(13\):1H NMR'), # [1H] NMR|X{%*}).1H NMR|);1H NMR|X.1H NMR|°)1H NMR|S{)*}{.*}1H NMR 
    ('F_NMR', r'19F\(H\) NMR|^.*\)*\.*19F NMR'), # 19F(H) NMR|{1H} NMR|S{)*}{.*}19F NMR
    ('C_NMR', r'H-\d+\)\;*13C NMR|\d+H\)[\;\.]*13C NMR|H\d+\)\.*13C NMR|^.*\)*\.*13C NMR|13C\}1H\} NMR|141 NMR'), # H-X);13C NMR|XH).13C NMR|HX).13C NMR|S{)*}{.*}13C NMR
    ('NOTES1', r'O10298OOOTBS3142Appendix A:| 43NH 51016OO1112678Me92Me\d+| 1211OO1610NH 53417Me182Me\d+|N OCO2allylCO2MeN|NMeO2CONMeO2CO2N\d+|' +
               r'OCO2allylCO2MeO\d+|Ph2SiHOPh2SiOPh2SiOH\d+|61    '), #  # 
    ('UPPERCASE_MULTIPLICITY', uppercase_multiplicity)
]

REPLACEMENT_DICT = {'H_NMR' : r'1H NMR',
                    'F_NMR': r'19F NMR',
                    'C_NMR': r'13C NMR',
                    'NOTES1': r'/)',
                    }

def replace_text_by_tokens(text, token_patterns, replacement_dict):
    regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_patterns)
    edited_text = text
    for match in re.finditer(regex, text):
        kind = match.lastgroup
        value = match.group()
        if kind == 'UPPERCASE_MULTIPLICITY':
            new_value = value.lower()
            new_value = new_value.replace('j', 'J')
        else:
            new_value = replacement_dict.get(kind)
        edited_text = edited_text.replace(value, new_value)
    return edited_text