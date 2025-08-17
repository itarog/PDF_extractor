from .token_patterns import load_default_nmr_tokens
from .parser import process_and_parse_single_nmr_text

from chemdataextractor import Document

def get_nmr_parsed_data_chemdataextractor(nmr_line):
    nmr_text = nmr_line.text
    doc = Document(nmr_text)
    records = doc.records.serialize()
    nmr_records = [record for record in records if 'nmr_spectra' in record.keys()]
    if nmr_records:
        result = nmr_records[0].get('nmr_spectra')
    else:
        result = None
    return result

def get_nmr_parsed_data_costum(nmr_line, token_patterns=None):
    token_patterns = load_default_nmr_tokens(token_patterns)
    nmr_text = nmr_line.text
    result = process_and_parse_single_nmr_text(nmr_text, token_patterns)
    return result