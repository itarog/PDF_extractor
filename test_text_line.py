from .general import get_page_num_and_line_num_from_multi_idx, get_actual_idx_from_multi_idx
from .text_cleaning.clean_patterns import clean_text_by_tokens, load_default_clean_tokens
from .text_cleaning.replacement import replace_text_by_tokens, load_default_replacement_tokens
from .text_cleaning.test_enders import cut_text_by_enders, load_default_end_tokens

class TestTextLine:
    def __init__(self, start_multi_idx, end_multi_idx, test_type, text):
        self.start_multi_idx = start_multi_idx
        self.start_page, self.start_line = get_page_num_and_line_num_from_multi_idx(start_multi_idx)
        self.end_multi_idx = end_multi_idx
        self.end_page, self.end_line = get_page_num_and_line_num_from_multi_idx(end_multi_idx)
        self.test_type = test_type
        self.text = text
        
    def __repr__(self):
        return f'Starting page: {self.start_page}, Starting line: {self.start_line}, Ending page: {self.end_page}, Ending line: {self.end_line}, Test type: {self.test_type},  Text: {self.text}'

    def __str__(self):
        return f'Starting page: {self.start_page}, Starting line: {self.start_line}, Ending page: {self.end_page}, Ending line: {self.end_line}, Test type: {self.test_type}, Text: {self.text}'

def get_word_line_idx(enumerated_lines, word):
    word_line_idx = []
    for line_idx, line, _ in enumerated_lines:
        if word in line:
            word_line_idx.append(line_idx)
    return word_line_idx

def segment_text_by_multi_idx(pdf_lines_with_idx, requested_multi_idx, pad_before=-1, pad_after=20):
    segmented_text = []
    multi_idx_list = [multi_idx for multi_idx, *_ in pdf_lines_with_idx]
    requested_actual_idx = get_actual_idx_from_multi_idx(multi_idx_list, requested_multi_idx)
    segmented_text = pdf_lines_with_idx[max(requested_actual_idx+pad_before, 0):min(requested_actual_idx+pad_after, len(pdf_lines_with_idx))]
    return segmented_text

def find_test_start(full_text, segmented_lines, test_name):
    start_multi_idx = segmented_lines[0][0]  # Assumes index of the second line
    text_words = full_text.split(' ')
    for word in text_words:
        if test_name in word:
            start_location = full_text.find(word)
            if 'NMR' in test_name:
                left_text = full_text[:start_location].strip()
                start_location = left_text.rfind(' ')
            return start_multi_idx, start_location
    return start_multi_idx, False

def check_termination_by_another_test(text, test_name):
    text_end = text.find(test_name, 15)
    reducted_text = text[:text_end]
    return reducted_text

def extract_test_text_from_text(text, text_enders, test_names):
    text_enders = load_default_end_tokens(text_enders)
    for test_name in test_names:
        if test_name in text_enders:
            text_enders.remove(test_name)
    edited_text = text
    for test_name in test_names:
        edited_text = check_termination_by_another_test(edited_text, test_name=test_name)
    edited_text = cut_text_by_enders(edited_text, text_enders)
    edited_text = segment_text_by_its_end(edited_text)
    return edited_text    

def segment_text_by_its_end(text):
    if len(text)==0:
        return text
    for position, letter in enumerate(reversed(text)):
        if letter == ')':
            break
    final_text = text[:-position]
    if final_text.find(':')==-1:
        return text
    else:
        return final_text

def concatenate_and_track(segmented_lines):
    full_text = ''
    text_tracker = []
    for multi_idx, line_text, _ in segmented_lines:
        full_text += line_text
        text_tracker.append((multi_idx, full_text))
    return full_text, text_tracker

def find_end_index_in_tracker(reduced_text, text_tracker):
    for multi_idx, text in text_tracker:
        if reduced_text in text:
            return multi_idx
    return None

def extract_test_line_from_segmented_lines(segmented_lines, test_names, text_enders, clean_patterns, replacement_patterns, replacement_dict):
    full_text, text_tracker = concatenate_and_track(segmented_lines) 
    start_multi_idx, start_location = find_test_start(full_text, segmented_lines, test_name=test_names[-1])
    if start_location is False:
        return False
    edited_text = extract_test_text_from_text(full_text[start_location:], text_enders, test_names=test_names)
    end_multi_idx = find_end_index_in_tracker(edited_text, text_tracker)
    edited_text = clean_text_by_tokens(edited_text, clean_patterns)
    edited_text = replace_text_by_tokens(edited_text, replacement_patterns, replacement_dict)
    if 'spectrum' in edited_text or 'Spectra' in edited_text: # figure caption
        return False 
    if 'NMR' in test_names[-1]:
        r_loc = edited_text.find('R')
        test_type = edited_text[:r_loc+1]
    elif 'MS' in test_names[-1]:
        test_type = 'MS'
    else:
        test_type = test_names[-1]
    return (start_multi_idx, end_multi_idx, test_type, edited_text) # 

## BULID MORE False cases

def extract_test_text_lines(pdf_text_with_idx, test_names, text_enders=None, clean_patterns=None, replacement_patterns=None, replacement_dict=None):
    clean_patterns = load_default_clean_tokens(clean_patterns)
    replacement_patterns, replacement_dict = load_default_replacement_tokens(replacement_patterns, replacement_dict)
    test_lines = []
    for test_name in test_names:
        test_lines+=get_word_line_idx(pdf_text_with_idx, word=test_name)
    test_lines = list(set(test_lines))
    segemented_text = [segment_text_by_multi_idx(pdf_text_with_idx, test_line) for test_line in test_lines]
    test_text_lines = []
    for segmented_lines in segemented_text:
        test_line = extract_test_line_from_segmented_lines(segmented_lines, test_names, text_enders, clean_patterns, replacement_patterns, replacement_dict)
        if test_line:
            test_text_lines.append(test_line)
    final_lines = []
    for start_multi_idx, end_multi_idx, test_type, text in test_text_lines:
        final_lines.append(TestTextLine(start_multi_idx, end_multi_idx, test_type, text))
    return final_lines   