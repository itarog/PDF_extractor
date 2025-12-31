def load_default_nmr_tokens(nmr_token_patterns=None):
    if nmr_token_patterns is None:
        sentence_breakers = r'[\u2013\u2014\u2212\-\_\u0336]'
        sp_h_sp=r'\s*-*\s*' # space hyfen space
        comstp=r'[,.]'
        token_patterns = [ # 1H\s*NMR|
            ('NUCLEUS', r'1\s*H'+sp_h_sp+r'NMR|2\s*H'+sp_h_sp+r'NMR|H'+sp_h_sp+r'NMR|2\s*D'+sp_h_sp+r'NMR|D'+sp_h_sp+r'NMR|' + # 1H-NMR|2H-NMR|H-NMR|2D-NMR|D-NMR
                        r'13\s*C'+sp_h_sp+r'NMR|C'+sp_h_sp+r'NMR|13C19F'+sp_h_sp+r'NMR|13C\{1H\}'+sp_h_sp+r'NMR|' + # 13C-NMR|C-NMR|13C19F-NMR
                        r'19F'+sp_h_sp+r'NMR|19F\{1H\}'+sp_h_sp+r'NMR|' + # 19F
                        r'29Si'+sp_h_sp+r'NMR|' + # 29Si
                        r'31P'+sp_h_sp+r'NMR|31P19F'+sp_h_sp+r'NMR|' + # 31P
                        r'11B'+sp_h_sp+r'NMR|11B19F'+sp_h_sp+r'NMR|' + # 11B
                        r'77Se19F'+sp_h_sp+r'NMR|' + # 77Se
                        r'\{1H\} NMR|\}1H\} NMR|NMR' # unknown - C or F #
                        ),
            ('SOLVENT', r'(CHCl3/CDCl3|CDCl3 over K2CO3|CHCl3 with 5% CDCl3|d8-toluene/CD3CN mixture|' + # solvent mixtures
                        r'CDCl3 d1|CDCl3|CD2Cl2|Chloroform-d|CDCL3|CHLOROFORM-D|cdcl3|' +  # chloroform
                        r'DMSO-d6|d6DMSO|d6-DMSO|\(CD3\)2SO)|DMSO d6|DMSO|dmso|' + # dmso
                        r'toluene-D8|tol-D8|d8-toluene|' + # toluene 
                        r'CD3OD|MeOH-d4|MeOD|methanol-d4|d4-methanol|Methanol-d4|' + # methanol
                        r'Et2O|acetone-d6|ACETONE-D6|' + # acetone
                        r'THF-d8|d8-thf|' + # thf
                        r'DMF-d7|Acetic acid-d4|C6D6|CD3CN|Methylene Chloride-d2|D2O' # misc
                        ),
            ('TEMPRATURE', r'T\s*=\s*\d+\s*K|T\s*=\s*\d+\s*°K|T\s*=\s*\d+\s*C|T\s*=\s*\d+\s*°C|' + #T=X K|T=X °K|T=X C|T=X °C| 
                          r'\d+\s*°K|\d+\s*°C|T\s*=\s*\d+'),  # X °K|X °C|T=X|
            ('FREQUENCY', r'\d+\.?\d*,*\s*MHz'),
            ('MIXTURE', r'\(as a mixture of diastereomers\)|\bmixture of rotamers\b|mixture of diastereomers|rotameric|rel. Me2Se'),
            ('ROTAMER', r'Rotameric mixtures|major isomer|minor isomer|' +
                        r'\bMajor rotamer\b|Major diastereomer|\(major diastereomer\)|major diastereomer, |major diastereomer,|major diastereomer|' +
                        r'\bMinor rotamer\b|Minor diastereomer|\(minor diastereomer\)|minor diastereomer, |minor diastereomer,|minor diastereomer|' +
                        r'Signals correspond to keto-tautomer:|Signals correspond to E-isomer:|Signals correspond to Z-isomer:|Signals correspond to enol-tautomer:' 
                        ),
            ('ASSIGNMENT', r'ArCH3|Ar|C\(CH3\)2|CH\(CH3\)CH3|CH\(OH\)CH2\(CH2\)6CH3|CH2C\(CH3\)=CH2|C\(O\)OCH2CH3' + 
                          r'CH2CH2CH2CH3|CH\(CH3\)2 & CH\(CH2OTs\)2|CH\(CH2OTs\)2|C\(S\)C\(CH3\)3|C\(CH3\)3|C\(O\)C\(CH3\)3|' +
                          r'C\(S\)C\(CH3\)3\)|C=O|C=S|CHOC\(O\)|CH\(CH3\)3|CH\(CH3\)2|CH\(CH2OH\)2|CH\(CH3\)2|CH\(CHHOTs\)2|' +
                          r'CHOH|CHO|CF3|COH|C\(OH\)C\(CH3\)3|C\(O\)OCH2CH3|C=CHcisHtrans|CH2C\(Br\)=CH2|CH\(Ph\)CH3|' +
                          r'NC=CH|NCH=CH|NCHH|NCH2|NCHD|NCHPh2|NCHcisHtrans and NCDcisHtrans|NCHcisHtrans and NCHcisDtrans|NCHtransHcis|NCHcisHtrans|NCH and CHOH|NCHC\(O\)|NCH|' +
                          r'OC\(O\)CH3|OC\(O\)CH3|OC\(CH3\)3|OCH|OCHH|OCH2|' + 
                          r'Si\-*\(CH2CH3\)3|Si\-*\(CH3\)2C\(CH3\)3|Si\-*\(CH3\)3|Si\(CH3\)2|Si\-*\(CH3\)|Si\-*\(CHa3\)\(CHb3\)|Si\-*\(CHa3\)\(CHb\)|' +
                          r'C\(\d+\)H\d*|C\(\d+\)|\(\d+\)HAHB|C\(\d+\/\d+\)H\d*|C\(\d+\/\d+\)|C\(\d+\/\d+\/\d+\/\d+\)|\(\d+\)H|' +
                          r'C\(\d+\/\d+\/\d+\/\d+\/\d+\/\d+\/\d+\)|Cx\(\d+\)|Cy\(\d+\)|' +
                          r'Sn\(CH3\)3|Ph2CH\(OH\)|P\(OCH2CH3\)2'
                          ), 
            ('INTEGRATION', r'(?!\})\d+\s*H(?!z)|(?!\})\d+\.\d+\s*H(?!z)' + # H integration 
                            r'\d\s*F|\d\s*C'
                            ), # X H|X.X H
                            # r'\d+\s*F|\d+\.\d+\s*F|'), # X F|X.X F  
            ('MULTIPLICITY', r't with further splitting|octet|' +
                            # assignment_str +
                            r'ddddd|dddd|dddt|dddq|dddsept|ddtd|ddqd|ddseptd|' + 
                            r'ddd|dtd|dqd|ddt|ddq|dseptd|dseptq|ddsept|' +
                            r'ttt|tdt|tqt|ttd|ttq|tseptt|tseptq|ttsept|' +
                            r'dd|dt|dquin|dq|dsept|tt|td|tquin|tq|tsept|qd|qt|qq|qsept|' +
                            r'\(br\)|br|'+
                            r'sxt|septet|quintet|quin|sept|'+
                            r'q\s*,|d\s*,|t\s*,|m\s*,|p\s*,|s\s*,'), 
            ('COUPLING_CONSTANT', r'\dJ\s*^.*'+sentence_breakers+r'^.*\s*=\s*\d+\.\d+\s*Hz|1J\s*\(C'+sentence_breakers+r'F\)\s*=\s*\d+\.\d+\s*Hz|' +
                                  r'J\s*\(C'+sentence_breakers+r'F\)\s*=\s*\d+\.\d+\s*Hz|' + #J(C-F)=2.3 Hz
                                  r'J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+'+comstp+r'\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X,X.X,X.X,X.X Hz
                                  r'J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X,X.X,X.X Hz 
                                  r'J\s*=\s*\d+\.\d+\s*Hz\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+|' + # J=X.X Hz,X.X,X.X,X.X  
                                  r'J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*Hz\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+|' + # J=X.X,X.X Hz,X.X,X.X 
                                  r'J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*Hz\s*'+comstp+r'\s*\d+\.\d+|' + # J=X.X,X.X,X.X Hz,X.X 
                                  r'J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*Hz|J\s*=\s*\d+\.\d+\s\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X,X.X Hz|J=X.X X.X,X.X Hz|
                                  r'J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s\d+\.\d+\s*Hz|J\s*=\s*\d+\.\d+\s*.\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X X.X Hz|J=X.X.X.X,X.X Hz|
                                  r'J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*.\s*\d+\.\d+\s*Hz|J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+|' + # J=X.X,X.X.X.X Hz|J=X.X,X.X,X.X|
                                  r'\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*Hz|' + # X.X, X.X, X.X Hz
                                  r'\d+\.\d+\s*Hz\s*'+comstp+r'\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+|' + # X.X Hz, X.X, X.X Hz
                                  r'\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*Hz\s*'+comstp+r'\s*\d+\.\d+|' + # X.X, X.X Hz, X.X Hz 
                                  r'J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*Hz|J\s*=\s*\d+'+comstp+r'\d+\s*'+comstp+r'\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X Hz|J=X,X,X.X Hz|
                                  r'J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+'+comstp+r'\d+\s*Hz|J\s*=\s*\d+\.\d+\s*.\s*\d+\.\d+\s*Hz|' + # J=X.X,X,X Hz|J=X.X.X.X Hz|
                                  r'J\s*=\s*\d+\.\d+\s\d+\.\d+\s*Hz|J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*.\s*Hz|' + # J=X.X X.X Hz|J=X.X,X.X. Hz|
                                  r'J\s*=\s*\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+|\d+\.\d+\s*'+comstp+r'\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X|X.X,X.X Hz|
                                  r'J\s*=\s*\d+\.\d+\s*Hz|J\s*=\s*\d+'+comstp+r'\d+\s*Hz|J\s*=\s*\d+\.\d+|\d+\.\d+\s*Hz|' + # J=X.X Hz|J=X,X Hz|J=X.X Hz|X.X Hz|
                                  r'J\s*=\s*\d+\s*Hz|J\s*=\s*\d+|\d+\s*Hz|' + # J=X Hz|J=X|X Hz 
                                  r'J\s*\d+.\d+'+comstp+r'\s*\d+.\d+'+comstp+r'\s*\d+.\d+'+comstp+r'\s*\d+.\d+|J\s*\d+.\d+'+comstp+r'\s*\d+.\d+'+comstp+r'\s*\d+.\d+|J\s*\d+.\d+'+comstp+r'\s*\d+.\d+|J\s*\d+.\d+' # J 4.6, 1.9
                                #   r'J\s*=\s*\d+\.\d+\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+,\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X,X.X,X.X,X.X Hz
                                #   r'J\s*=\s*\d+\.\d+\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X,X.X,X.X Hz 
                                #   r'J\s*=\s*\d+\.\d+\s*Hz\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+|' + # J=X.X Hz,X.X,X.X,X.X  
                                #   r'J\s*=\s*\d+\.\d+\s*,\s*\d+\.\d+\s*Hz\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+|' + # J=X.X,X.X Hz,X.X,X.X 
                                #   r'J\s*=\s*\d+\.\d+\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+\s*Hz\s*,\s*\d+\.\d+|' + # J=X.X,X.X,X.X Hz,X.X 
                                #   r'J\s*=\s*\d+\.\d+\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+\s*Hz|J\s*=\s*\d+\.\d+\s\d+\.\d+\s*,\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X,X.X Hz|J=X.X X.X,X.X Hz|
                                #   r'J\s*=\s*\d+\.\d+\s*,\s*\d+\.\d+\s\d+\.\d+\s*Hz|J\s*=\s*\d+\.\d+\s*.\s*\d+\.\d+\s*,\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X X.X Hz|J=X.X.X.X,X.X Hz|
                                #   r'J\s*=\s*\d+\.\d+\s*,\s*\d+\.\d+\s*.\s*\d+\.\d+\s*Hz|J\s*=\s*\d+\.\d+\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+|' + # J=X.X,X.X.X.X Hz|J=X.X,X.X,X.X|
                                #   r'\d+\.\d+\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+\s*Hz|' + # X.X, X.X, X.X Hz
                                #   r'\d+\.\d+\s*Hz\s*,\s*\d+\.\d+\s*,\s*\d+\.\d+|' + # X.X Hz, X.X, X.X Hz
                                #   r'\d+\.\d+\s*,\s*\d+\.\d+\s*Hz\s*,\s*\d+\.\d+|' + # X.X, X.X Hz, X.X Hz 
                                #   r'J\s*=\s*\d+\.\d+\s*,\s*\d+\.\d+\s*Hz|J\s*=\s*\d+\,\d+\s*,\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X Hz|J=X,X,X.X Hz|
                                #   r'J\s*=\s*\d+\.\d+\s*,\s*\d+\,\d+\s*Hz|J\s*=\s*\d+\.\d+\s*.\s*\d+\.\d+\s*Hz|' + # J=X.X,X,X Hz|J=X.X.X.X Hz|
                                #   r'J\s*=\s*\d+\.\d+\s\d+\.\d+\s*Hz|J\s*=\s*\d+\.\d+\s*,\s*\d+\.\d+\s*.\s*Hz|' + # J=X.X X.X Hz|J=X.X,X.X. Hz|
                                #   r'J\s*=\s*\d+\.\d+\s*,\s*\d+\.\d+|\d+\.\d+\s*,\s*\d+\.\d+\s*Hz|' + # J=X.X,X.X|X.X,X.X Hz|
                                #   r'J\s*=\s*\d+\.\d+\s*Hz|J\s*=\s*\d+\,\d+\s*Hz|J\s*=\s*\d+\.\d+|\d+\.\d+\s*Hz|' + # J=X.X Hz|J=X,X Hz|J=X.X Hz|X.X Hz|
                                #   r'J\s*=\s*\d+\s*Hz|J\s*=\s*\d+|\d+\s*Hz|' + # J=X Hz|J=X|X Hz 
                                #   r'J\s*\d+.\d+,\s*\d+.\d+,\s*\d+.\d+,\s*\d+.\d+|J\s*\d+.\d+,\s*\d+.\d+,\s*\d+.\d+|J\s*\d+.\d+,\s*\d+.\d+|J\s*\d+.\d+' # J 4.6, 1.9
                                  ),  
            # ('INTEGRATION', r'\d+\s*H|\d+\.\d+\s*H'), # X H|X.X H    
            ('CHEMICAL_SHIFT_RANGE', r'\d+\.\d+\s*'+sentence_breakers+r'\s*\d+\.\d+'), # X.X-X.X
            ('CHEMICAL_SHIFT', sentence_breakers+r'\s*\d+\.\d+|\d+\.\d+'), #-X.X|X.X # take *
            ('DELIMITER', r'$ \(ppm\)|$|δF|δH|δC||δ \(ppm\)|δ\s*\/ppm\s*|δ'),
            ('COMMA', r','),
            ('LINE_ENDER', r'\;'),
            ('PARENTHESIS_OPEN', r'\('),
            ('PARENTHESIS_CLOSE', r'\)'),
            ('WHITESPACE', r'\s+'),
        ]
    else:
        token_patterns = nmr_token_patterns
    return token_patterns