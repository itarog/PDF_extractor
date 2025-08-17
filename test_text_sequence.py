from .general import get_actual_idx_from_multi_idx

class TestTextSequence:
    def __init__(self, test_text_lines):
        self.test_text_lines = test_text_lines
        self.start_multi_idx = test_text_lines[0].start_multi_idx
        self.end_multi_idx = test_text_lines[-1].end_multi_idx
        self.start_page, self.start_line = test_text_lines[0].start_page, test_text_lines[0].start_line
        self.end_page, self.end_line = test_text_lines[-1].end_page, test_text_lines[-1].end_line
        self.test_type_list = [test_line.test_type for test_line in test_text_lines]
 
    def __repr__(self):
        return f'Starting page: {self.start_page}, Starting line: {self.start_line}, Ending page: {self.end_page}, Ending line: {self.end_line},  Tests: {self.test_type_list}' # , Nuclei: {self.nucleis}

    def __str__(self):
        return f'Starting page: {self.start_page}, Starting line: {self.start_line}, Ending page: {self.end_page}, Ending line: {self.end_line},  Tests: {self.test_type_list}' # , Nuclei: {self.nucleis}

def check_matching_of_lines(multi_idx_1, multi_idx_2, multi_idx_list, allowed_diff=4):
    actual_idx_1 = get_actual_idx_from_multi_idx(multi_idx_list, multi_idx_1)
    actual_idx_2 = get_actual_idx_from_multi_idx(multi_idx_list, multi_idx_2)
    return abs(actual_idx_1-actual_idx_2)<=allowed_diff

def sort_test_lines_to_sequences(test_lines, multi_idx_list, allowed_diff=4):
    sequences = []
    current_sequence = []   
    for idx, line in enumerate(test_lines):
        if idx==0:
            current_sequence = [line]
        else:
            match_flag = check_matching_of_lines(current_sequence[-1].end_multi_idx, line.start_multi_idx, multi_idx_list, allowed_diff)
            if match_flag:
                current_sequence.append(line)
            else:
                sequences.append(TestTextSequence(current_sequence))
                current_sequence = [line]
    sequences.append(TestTextSequence(current_sequence))
    return sequences