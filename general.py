def get_page_num_and_line_num_from_multi_idx(multi_idx):
    return map(int, multi_idx.split('_'))

def get_actual_idx_from_multi_idx(multi_idx_list, requested_multi_idx):
    for actual_idx, multi_idx in enumerate(multi_idx_list):
        if requested_multi_idx == multi_idx:
            return actual_idx
    return False
