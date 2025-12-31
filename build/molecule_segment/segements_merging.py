from math import floor, ceil
from .sequences2segments import count_occurences, search_molecule_segment_for_text_lines, process_all_test_list, get_molecule_segments_statsitics, assign_molecule_segment_name, assign_molecule_segment_size
from .molecule_segment_obj import MoleculeSegment

def get_problematic_molecule_segment_idx_list(molecule_segments):
    incomplete_molecule_segments_idx_list, zero_size_molecule_segments_idx_list = [], []
    for segment_idx, molecule_segment in enumerate(molecule_segments):
        if molecule_segment.size == 0:
            zero_size_molecule_segments_idx_list.append(segment_idx)
        elif molecule_segment.size < 1.0:
            incomplete_molecule_segments_idx_list.append(segment_idx)
    return incomplete_molecule_segments_idx_list, zero_size_molecule_segments_idx_list

def merge_overlapping_tuples(lst):
    merged = []
    current = list(lst[0])
    for a, b in lst[1:]:
        if a in current or b in current:
            current.extend([a, b])
            current = sorted(set(current))
        else:
            merged.append(tuple(current))
            current = [a, b]
    merged.append(tuple(current))
    return merged

def merge_adjcent_numbers(lst):
    merged = []
    current = [lst[0]]
    for num in lst[1:]:
        if num-1==current[-1]:
            current.append(num)
        else:
            merged.append(current)
            current=[num]
    merged.append(current)
    return merged

def sum_common_tests_molecule_sugment_tests(molecule_segments, segments_idx_list, common_sequence):
    overall_tests = []
    for molecule_segment_idx in segments_idx_list:
        if molecule_segments[molecule_segment_idx].has_test_text_sequence:
            overall_tests += molecule_segments[molecule_segment_idx].test_text_sequence.test_type_list
    overall_tests = tuple(overall_tests)
    count_common_sequence = count_occurences(overall_tests, common_sequence)
    return count_common_sequence

def locate_molecule_segment_to_be_merged(molecule_segments, common_sequence, iregualr_molecule_segments_indices):
    common_sequence_len = len(common_sequence)
    to_be_merged_indices = []
    for prob_idx in iregualr_molecule_segments_indices:
        molecule_segment_1_test_list = molecule_segments[prob_idx].test_text_sequence.test_type_list
        if len(molecule_segment_1_test_list)<common_sequence_len and prob_idx<len(molecule_segments)-1:
            count_common_sequence = sum_common_tests_molecule_sugment_tests(molecule_segments, [prob_idx, prob_idx+1], common_sequence)
            if count_common_sequence>0:
                to_be_merged_indices.append((prob_idx, prob_idx+1))
    if to_be_merged_indices:
        final_indices = merge_overlapping_tuples(to_be_merged_indices)
        final_dict = {tple: sum_common_tests_molecule_sugment_tests(molecule_segments, tple, common_sequence) for tple in final_indices}
    else:
        final_dict = dict()
    return final_dict

def merge_segments(molecule_segments, idx_tuple):
    new_segment_lines = []
    for inner_idx in idx_tuple:
        new_segment_lines += molecule_segments[inner_idx].segment_lines
    new_molecule_segment = MoleculeSegment(new_segment_lines)
    search_molecule_segment_for_text_lines(new_molecule_segment)
    process_all_test_list(new_molecule_segment)   
    return new_molecule_segment

def sort_molecule_segments(molecule_segments):
    sort_1 = sorted(molecule_segments, key = lambda x: x.start_line)
    sort_2 = sorted(sort_1, key = lambda x: x.start_page)
    return sort_2

def handle_incomplete_molecule_segments(incomplete_molecule_segments_dict, molecule_segments):
    new_molecule_segments = []
    if incomplete_molecule_segments_dict:
        for idx_tuple, common_count in incomplete_molecule_segments_dict.items():
            if common_count==1.0:
                new_segment = merge_segments(molecule_segments, idx_tuple)
                new_molecule_segments.append(new_segment)
    return new_molecule_segments    

def handle_size_molecule_segments(zero_size_molecule_segments_idx_list, molecule_segments):
    new_molecule_segments = []
    zero_size_molecule_segments_indices_list = merge_adjcent_numbers(zero_size_molecule_segments_idx_list)
    for idx_list in zero_size_molecule_segments_indices_list:
        if idx_list[-1]<len(molecule_segments)-1:
            full_idx_list = idx_list + [idx_list[-1]+1]
            new_segment = merge_segments(molecule_segments, full_idx_list)
            new_molecule_segments.append(new_segment)
        elif len(idx_list)>1:
            new_segment = merge_segments(molecule_segments, idx_list)
            new_molecule_segments.append(new_segment)
        else:
            new_molecule_segments.append(molecule_segments[full_idx_list[0]])
    return new_molecule_segments

def adjust_molecule_segments_by_common_sequence(molecule_segments):
    mean_number_of_tests, sequence_counter = get_molecule_segments_statsitics(molecule_segments)
    if sequence_counter:
        most_common_sequence = sequence_counter.most_common(1)[0][0]
        if floor(mean_number_of_tests) == len(most_common_sequence) or ceil(mean_number_of_tests) == len(most_common_sequence):
            incomplete_molecule_segments_idx_list, zero_size_molecule_segments_idx_list = get_problematic_molecule_segment_idx_list(molecule_segments)
            incomplete_molecule_segments_dict = locate_molecule_segment_to_be_merged(molecule_segments, most_common_sequence, incomplete_molecule_segments_idx_list)
            all_problematic_idx = zero_size_molecule_segments_idx_list
            for idx_tuple in incomplete_molecule_segments_dict.keys():
                all_problematic_idx+=list(idx_tuple)
            new_molecule_segments = [molecule_segments[segment_idx] for segment_idx in range(len(molecule_segments)) if segment_idx not in all_problematic_idx]
            new_molecule_segments.extend(handle_incomplete_molecule_segments(incomplete_molecule_segments_dict, molecule_segments))
            if zero_size_molecule_segments_idx_list:
                new_molecule_segments.extend(handle_size_molecule_segments(zero_size_molecule_segments_idx_list, molecule_segments))
            new_molecule_segments = sort_molecule_segments(new_molecule_segments)
        else:
            new_molecule_segments = molecule_segments
        assign_molecule_segment_name(new_molecule_segments)
        assign_molecule_segment_size(new_molecule_segments, most_common_sequence)
    else:
        new_molecule_segments = molecule_segments
    final_molecule_segments = [molecule_segment for molecule_segment in new_molecule_segments if molecule_segment.has_test_text_sequence]
    return final_molecule_segments