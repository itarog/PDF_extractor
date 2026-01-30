import numpy as np
from collections import Counter
from math import ceil
from src.chemsie.internal.test_text_line import extract_test_text_lines
from src.chemsie.utils.general import get_actual_idx_from_multi_idx
from src.chemsie.internal.test_text_sequence import sort_test_lines_to_sequences
from .molecule_segment_obj import MoleculeSegment, Spectra
from .segments_creation import locate_molecule_segments

def sort_test_list(test_list):
    first_sort = sorted(test_list, key=lambda x: x.start_line)
    second_sort = sorted(first_sort, key=lambda x: x.start_page)
    return second_sort

def search_molecule_segment_for_text_lines(molecule_segment):
    test_names = {'NMR': [r'NMR'], 'IR': [r'IR'], 'Rf': [r'Rf'], 'HRMS': [r'HRMS']}
    for test_type, test_patterns in test_names.items():
        text_lines = extract_test_text_lines(molecule_segment.segment_lines, test_names=test_patterns)
        if text_lines:
            molecule_segment.spectra.append(Spectra(test_type, text_lines))

def get_all_test_list(molecule_segment):
    all_tests = []
    for spectrum in molecule_segment.spectra:
        all_tests.extend(spectrum.text_lines)
    return all_tests
    #+ extract_test_text_lines(molecule_segment.segment_lines, test_names=[r'LCMS']) + extract_test_text_lines(molecule_segment.segment_lines, test_names=[r'LRMS']) 

def get_molecule_segments_statsitics(molecule_segments):
    num_of_tests_list = []
    test_types_list = []
    for molecule_segment in molecule_segments:
        if molecule_segment.has_test_text_sequence:
            num_of_tests_list.append(len(molecule_segment.test_text_sequence.test_text_lines))
            test_types_list.append(tuple(molecule_segment.test_text_sequence.test_type_list))
    mean_number_of_tests = np.mean(num_of_tests_list)
    sequence_counter = Counter(test_types_list)
    return mean_number_of_tests, sequence_counter

def count_occurences(source, target):
    count = 0
    for i in range(len(source) - len(target) + 1):
        if source[i:i+len(target)] == target:
            count += 1
    return count

def assign_molecule_segment_size(molecule_segments, common_sequence):
    common_sequence_len = len(common_sequence)
    for molecule_segment in molecule_segments:
        if molecule_segment.has_test_text_sequence:
            num_of_test_lines = len(molecule_segment.test_text_sequence.test_type_list)
            molecule_segment.size = num_of_test_lines/common_sequence_len
            molecule_segment.max_molecule_count = max(ceil(molecule_segment.size), count_occurences(molecule_segment.test_text_sequence.test_type_list, list(common_sequence)))
            molecule_segment.min_molecule_count = min(ceil(molecule_segment.size), count_occurences(molecule_segment.test_text_sequence.test_type_list, list(common_sequence)))
        else:
            molecule_segment.size = 0.0
            molecule_segment.max_molecule_count = 0
            molecule_segment.min_molecule_count = 0

def process_all_test_list(molecule_segment):
    search_molecule_segment_for_text_lines(molecule_segment)
    all_test_list = get_all_test_list(molecule_segment)
    sorted_test_list = sort_test_list(all_test_list)
    if sorted_test_list:
        multi_idx_list = [item[0] for item in molecule_segment.segment_lines] 
        test_text_sequence_list = sort_test_lines_to_sequences(sorted_test_list, multi_idx_list)
    else:
        test_text_sequence_list = []
    return test_text_sequence_list

def spilt_molecule_segment_by_test_sequences(molecule_segment, test_text_sequences):
    segment_lines = molecule_segment.segment_lines
    last_idx = False
    new_molecule_segments = []
    for test_text_sequence in test_text_sequences:
        end_multi_idx = test_text_sequence.end_multi_idx
        actual_end_idx = get_actual_idx_from_multi_idx(segment_lines, end_multi_idx)
        if last_idx:
            reducted_lines = segment_lines[last_idx:actual_end_idx]
        else:
            reducted_lines = segment_lines[:actual_end_idx]
        last_idx = actual_end_idx
        if reducted_lines:
            new_molecule_segment = MoleculeSegment(reducted_lines)
            search_molecule_segment_for_text_lines(new_molecule_segment)
            new_molecule_segment.has_test_text_sequence = True
            new_molecule_segment.test_text_sequence = test_text_sequence
            new_molecule_segments.append(new_molecule_segment)
    # process_molecule_segment_text(new_molecule_segments)
    return new_molecule_segments

def spilt_molecule_segment_by_page_difference(molecule_segment, max_page_diff=1):
    if molecule_segment.end_page-molecule_segment.start_page<=max_page_diff:
        new_molecule_segments = [molecule_segment]
    else:
        new_molecule_segments = []
        temp_molecule_segments = locate_molecule_segments(molecule_segment.segment_lines, locate_by='percentile', tokens_mark=50, spaces_mark=25)

        # new_molecule_segments = [temp_molecule_segments[0]]
        # attempt_num = 0
        # while temp_molecule_segments[-1].end_page-temp_molecule_segments[-1].start_page>max_page_diff:
            # temp_molecule_segments = locate_molecule_segments(temp_molecule_segments[-1].segment_lines, locate_by='first_over', over_mark=50-attempt_num)
            # new_molecule_segments.append(temp_molecule_segments[0])
        new_molecule_segments.append(temp_molecule_segments[-1])
    return new_molecule_segments

def get_first_plateau(lst):
    N = 5
    for i in range(len(lst) - N + 1):
        if all(abs(lst[i + j]) <= 1 for j in range(N)):
            return i
    return -1

def adjust_cut_idx(start_pages, cut_idx):
    if cut_idx>0:
        while start_pages[cut_idx]-start_pages[cut_idx-1]<=2:
            cut_idx=cut_idx-1
            if cut_idx==0:
                break
    return cut_idx

def cut_init_molecule_segments(molecule_segments):
    start_pages = [molecule_segment.test_text_sequence.start_page for molecule_segment in molecule_segments if molecule_segment.has_test_text_sequence]
    diff_pages = np.diff(start_pages)
    grad_diff_pages = np.gradient(diff_pages, 1)
    cut_idx = get_first_plateau(grad_diff_pages)
    cut_idx = adjust_cut_idx(start_pages, cut_idx)
    start_page = start_pages[cut_idx]
    new_molecule_segments = [molecule_segment for molecule_segment in molecule_segments if molecule_segment.start_page>=start_page]
    return new_molecule_segments

def smooth_bbox_bbox(page_num_1, bbox_1, page_num_2, bbox_2):
    if page_num_1!=page_num_2:
        return bbox_1, bbox_2
    x_1, y_1, width_1, height_1 = bbox_1
    x_2, y_2, width_2, height_2 = bbox_2
    if y_1 + height_1<y_2:
        return bbox_1, bbox_2
    avg_y = round((y_1 + height_1 + y_2)/2, 2)
    new_height_1 = avg_y - y_1
    new_y_2 = avg_y
    return (x_1, y_1, width_1, new_height_1), (x_2, new_y_2, width_2, height_2)

def smooth_bbox_text_test_line(line_1, line_2):
    if line_1.bbox_list and line_2.bbox_list:
        page_num_1, bbox_1 = line_1.bbox_list[-1]
        page_num_2, bbox_2 = line_2.bbox_list[0] # (page_num, (x, y, width, height))
        new_bbox_1, new_bbox_2 = smooth_bbox_bbox(page_num_1, bbox_1, page_num_2, bbox_2)
        new_bbox_list_1 = line_1.bbox_list[:-1]
        new_bbox_list_1.append((page_num_1, new_bbox_1))
        new_bbox_list_2 = line_2.bbox_list[1:]
        new_bbox_list_2.append((page_num_2, new_bbox_2))
        line_1.bbox_list = new_bbox_list_1
        line_2.bbox_list = new_bbox_list_2
    return line_1, line_2

def smooth_bbox_molecule_segments(molecule_segments):
    for molecule_segment in molecule_segments:
        test_text_lines = molecule_segment.test_text_sequence.test_text_lines
        new_test_text_lines = []
        new_test_line = None
        for line_idx, test_line in enumerate(test_text_lines):
            if line_idx==0:
                continue
            elif line_idx<len(test_text_lines):
                prev_test_line = new_test_line if new_test_line else test_text_lines[line_idx-1]
                new_prev_line, new_test_line = smooth_bbox_text_test_.line(prev_test_line, test_line)
                new_test_text_lines.append(new_prev_line)
            else:
                new_test_text_lines.append(new_test_line)
        molecule_segment.test_text_sequence.test_text_lines = new_test_text_lines

def process_molecule_segment_text(molecule_segments, cut_init_segments=False):
    edited_molecule_segments = molecule_segments
    test_text_sequence_list = [process_all_test_list(molecule_segment) for molecule_segment in edited_molecule_segments]
    final_molecule_segments = []
    for test_text_sequences, molecule_segment in zip(test_text_sequence_list, edited_molecule_segments):
        if len(test_text_sequences)==1:
            molecule_segment.has_test_text_sequence = True
            molecule_segment.test_text_sequence = test_text_sequences[0]
            final_molecule_segments.append(molecule_segment)
        elif len(test_text_sequences)>1:
            new_molecule_segments = spilt_molecule_segment_by_test_sequences(molecule_segment, test_text_sequences)
            final_molecule_segments+=new_molecule_segments
        else:
            final_molecule_segments.append(molecule_segment)
    final_molecule_segments = [molecule_segment for molecule_segment in final_molecule_segments if molecule_segment.has_test_text_sequence]
    # smooth_bbox_molecule_segments(final_molecule_segments)
    if final_molecule_segments:
        if cut_init_segments:
            final_molecule_segments = cut_init_molecule_segments(final_molecule_segments)
        mean_number_of_tests, sequence_counter = get_molecule_segments_statsitics(final_molecule_segments)
        most_common_sequence = sequence_counter.most_common(1)[0][0]
        assign_molecule_segment_size(final_molecule_segments, most_common_sequence)
    return final_molecule_segments