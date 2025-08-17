import re

def tokenize(text, token_patterns, debugging=False):
    regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_patterns)
    tokens = []
    for match in re.finditer(regex, text):
        kind = match.lastgroup
        value = match.group()
        if kind != 'WHITESPACE':
            tokens.append((kind, value))
    if debugging:
        print("Tokens:", tokens)
    return tokens