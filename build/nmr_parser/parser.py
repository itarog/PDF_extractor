from ..tokenizer.base_tokenize import tokenize
class HeaderDetails:
    pass

class NMRParser:
    def __init__(self, tokens, debugging=False):
        self.tokens = tokens
        self.debugging = debugging
        self.current = 0

    def parse(self):
        if self.debugging:
            print('moving to NUCLEUS token')
        self.move_to_nucleus_token()
        if self.current>=len(self.tokens):
            return {'header': {}, 'shifts': []}
        if self.debugging: 
            print("Parsing header...")
        header = self.parse_header()
        if self.debugging:
            print("Header parsed:", header)
        self.check_line_breakers()
        if self.match('ROTAMER'):
            if self.debugging:
                print("Parsing rotamer shifts...")
            shifts = self.parse_rotamer_shifts()
        else:
            if self.debugging:
                print("Parsing shifts...")
            shifts = self.parse_shifts()
            while self.check_leftover_tokens():
                shifts += self.parse_shifts()
        if self.debugging:
            print("Shifts parsed:", shifts)
        return {'header': header, 'shifts': shifts}
    
    def move_to_nucleus_token(self):
        while self.tokens[self.current][0]!='NUCLEUS':
            self.current+=1
            if self.current>=len(self.tokens):
                break
    
    def check_leftover_tokens(self):
        if len(self.tokens)<=self.current:
            return False
        else:
            leftover_tokens = self.tokens[self.current:]
            for new_current, (kind, token) in enumerate(leftover_tokens):
                if kind == 'CHEMICAL_SHIFT' or kind == 'CHEMICAL_SHIFT_RANGE':
                    self.current+=new_current
                    return True
            return False

    def match_line_breakers(self):
        return self.match('COMMA') or self.match('LINE_ENDER') or self.match('DELIMITER') 

    def match_and_consume(self, token_name, current_token_value=None):
        return self.consume(token_name) if self.match(token_name) else current_token_value
            
    def check_line_breakers(self):
        while self.match_line_breakers():
            self.match_and_consume('COMMA')
            self.match_and_consume('LINE_ENDER')
            self.match_and_consume('DELIMITER')
                         
    def parse_header(self):
        # header_details = HeaderDetails()
        nucleui = self.consume('NUCLEUS')
        frequency, temprature, solvent, mixture = None, None, None, None
        mixture = self.match_and_consume('MIXTURE', mixture) 
        self.match_and_consume('PARENTHESIS_OPEN')
        mixture = self.match_and_consume('MIXTURE', mixture)
        while self.match('FREQUENCY') or self.match('SOLVENT') or self.match('TEMPRATURE') or self.match('MIXTURE'):
            frequency = self.match_and_consume('FREQUENCY', frequency)
            temprature = self.match_and_consume('TEMPRATURE', temprature)
            solvent = self.match_and_consume('SOLVENT', solvent)
            mixture = self.match_and_consume('MIXTURE', mixture)            
            self.check_line_breakers()
        self.match_and_consume('PARENTHESIS_CLOSE')
        mixture = self.match_and_consume('MIXTURE', mixture)
        return {'nucleui': nucleui, 'frequency': frequency, 'solvent': solvent, 'temprature': temprature,} # 'mixture': mixture

    def parse_shifts(self):
        shifts = []
        while self.match('CHEMICAL_SHIFT') or self.match('CHEMICAL_SHIFT_RANGE'):
            shift, multiplicity, coupling, integration, assignment = None, None, None, None, None
            shift = self.match_and_consume('CHEMICAL_SHIFT_RANGE', shift)
            shift = self.match_and_consume('CHEMICAL_SHIFT', shift)
            if shift is None:
                raise ValueError(f"No chemical shift for peak, the current token is {self.tokens[self.current]}")
            self.match_and_consume('PARENTHESIS_OPEN')
            while self.match('MULTIPLICITY') or self.match('COUPLING_CONSTANT') or self.match('INTEGRATION') or self.match('ASSIGNMENT') or self.match_line_breakers():
                self.check_line_breakers()
                if self.match('MULTIPLICITY'): # consider elif for speed
                    if multiplicity:
                        self.consume('MULTIPLICITY')
                    else:
                        multiplicity = self.consume('MULTIPLICITY').rstrip(',')
                coupling = self.match_and_consume('COUPLING_CONSTANT', coupling)
                integration = self.match_and_consume('INTEGRATION', integration)
                assignment = self.match_and_consume('ASSIGNMENT', assignment)
                self.check_line_breakers()
            self.match_and_consume('PARENTHESIS_CLOSE')
            shifts.append({
                'shift': shift,
                'multiplicity': multiplicity,
                'coupling': coupling,
                'integration': integration,
                'assignment': assignment,
            }) 
            self.check_line_breakers()
        return shifts

    def parse_rotamer_shifts(self):
        shifts = {}
        while self.match('ROTAMER'):
            rotamer = self.consume('ROTAMER')
            self.check_line_breakers()
            rotamer_shifts = self.parse_shifts()
            shifts[rotamer] = rotamer_shifts
            self.check_line_breakers()
        return shifts

    def consume(self, kind):
        if self.debugging:
            print(f"Expecting {kind}, current token: {self.tokens[self.current]}")
        if self.current < len(self.tokens) and self.tokens[self.current][0] == kind:
            value = self.tokens[self.current][1]
            self.current += 1
            return value
        raise SyntaxError(f"Expected {kind}, got {self.tokens[self.current][0]}")

    def match(self, kind):
        return self.current < len(self.tokens) and self.tokens[self.current][0] == kind
    
def parse_single_nmr_text(nmr_text, token_patterns, debugging=False):
    tokens = tokenize(nmr_text, token_patterns, debugging)
    parser = NMRParser(tokens, debugging)
    parsed_data = parser.parse()
    return parsed_data, parser

def process_and_parse_single_nmr_text(nmr_text, token_patterns, line_num=9999999):
    parsed_data = None
    try:
        debugging = False
        parsed_data, parser = parse_single_nmr_text(nmr_text, token_patterns, debugging)
        # if len(parser.tokens)>parser.current:
        #     print(f'missed tokens in line {line_num}:')
        #     for token in parser.tokens[parser.current:]:
        #         print(token)
    except Exception as e:
        debugging = True
        print('line num:', line_num)
        print('original text:', nmr_text)
        parsed_data, parser = parse_single_nmr_text(nmr_text, token_patterns, debugging)
    return parsed_data