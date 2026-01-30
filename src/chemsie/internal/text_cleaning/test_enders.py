# def load_default_end_tokens(end_token_patterns=None):
#     if end_token_patterns is None:
#         token_patterns = ['NMR', 'IR', 'Rf', 'HRMS', 'LCMS', 'LRMS', 'HPLC', 'ESI-MS']
# # line_stoppers = ['was synthesized', 'was synthesized', 'To a solution', 'The title compound']
#         # text_enders +=['Calculated', 'Compound', 'General', 'Synthesis', 'Scheme', 'Procedure', 'Reagents', 'Note:', 'Conjugation', 'Method']
#     else:
#         token_patterns = end_token_patterns
#     return token_patterns

# def cut_text_by_enders(text, text_enders):
#     edited_text = text
#     for text_ender in text_enders:
#         end_idx=edited_text.find(text_ender)
#         if end_idx>0:
#             edited_text=edited_text[:end_idx-1]
#     return edited_text

import re

def load_default_end_tokens(end_token_patterns=None):
    if end_token_patterns is None:
        # use regex patterns instead of plain strings
        token_patterns = [
            r'NMR',           # general fallback
            # r'\d+[A-Za-z] NMR',      # e.g. 1H NMR, 13C NMR
            # r'\d+F NMR',      # e.g. 19F NMR
            r'IR',
            r'Rf',
            r'HRMS',
            # r'LCMS',
            # r'LRMS',
            r'HPLC',
            r'ESI-MS'
        ]
    else:
        token_patterns = end_token_patterns
    return token_patterns

def cut_text_by_enders(text, text_enders):
    edited_text = text
    for pattern in text_enders:
        match = re.search(pattern, edited_text)
        if match:
            end_idx = match.start()
            edited_text = edited_text[:end_idx].rstrip()
            break  # stop after the first match
    return edited_text
