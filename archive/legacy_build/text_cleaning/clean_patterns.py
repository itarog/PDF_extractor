import re

def load_default_clean_tokens(clean_token_patterns=None):
    if clean_token_patterns is None:
        token_patterns = [
            ('CHAPTER', r'\s*CHAPTER\s*\d\s*\d+|\s*Chapter\s*\d\s*\d+|\s*CHAPTER\s*\d\s*:\s*EXPERIMENTAL\s*\d+|\s*Chapter\s*\d\s*:\s*Experimental\s*\d+|'+ # Chapter Five – Experimental Section    209
                        r'\s*Experimental\s*\d+|Chapter\s*Five\s*[\u2013\u2014\-]\s*Experimental\s*Section\s*\d+|Experimental\-\d+\-|' +
                        r' 3. Development of flow methodolgies using organoboron reagents and diazo compounds  131|' +
                        r'                                                  5 Ethylene oxide is very toxic and great care should be taken when using it. The tank should be secured inside a fumehood with the appropriate regulator. The set-up involved connecting the regulator with a tube, equipped with a needle. This needle was inserted into a 25 mL flask with a septum. The flask was also equipped with needle connected to a bubbler, which vented to the fumehood. The ethylene oxide gas was then passed through the flask at −30 °C. Once a small amount of ethylene oxide was condensed, a known amount of solvent \(MTBE\) was added and the solution was brought up in a syringe to determine the total volume. The concentration was then calculated and the appropriate amount was added to the reaction mixture.     32  32  = 13, 13,'
                        ), 
            ('STEROMER', r'\(R\)|\(S\)|\(cis\)|\(trans\)' #+ 
                        ),
            ('NOTES', r' \(obscured by CDCl3\)|combined,| \(Nitro or boronic acid carbon not visible in 13|'+
                    r', almost overlaps with CDCl3 peak|1415EXPERIMENTAL5.4Experimental procedures and datadt|'+
                    r', one diastereomer 102    shown|, after D2O wash'),
            ]
    else:
        token_patterns = clean_token_patterns
    return token_patterns

def clean_text_by_tokens(text, token_patterns):
    regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_patterns)
    cleaned_text = text
    for match in re.finditer(regex, text):
        cleaned_text = cleaned_text.replace(match.group(), '')
    return cleaned_text