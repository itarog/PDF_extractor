def load_default_end_tokens(end_token_patterns=None):
    if end_token_patterns is None:
        token_patterns = ['NMR', 'IR', 'Rf', 'HRMS', 'LCMS', 'LRMS', 'HPLC', 'ESI-MS']
        # text_enders +=['Calculated', 'Compound', 'General', 'Synthesis', 'Scheme', 'Procedure', 'Reagents', 'Note:', 'Conjugation', 'Method']
    else:
        token_patterns = end_token_patterns
    return token_patterns

def cut_text_by_enders(text, text_enders):
    edited_text = text
    for text_ender in text_enders:
        end_idx=edited_text.find(text_ender)
        if end_idx>0:
            edited_text=edited_text[:end_idx-1]
    return edited_text