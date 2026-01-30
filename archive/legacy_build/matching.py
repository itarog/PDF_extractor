# def text_y_to_pic_y(text_y):
#     pic_y = 4.55*text_y - 155
#     return pic_y

def check_mol_pic_proximity(molecule_segment, mol_pic):
    mol_page = mol_pic.page_num
    mol_mean_y = mol_pic.bbox[0] + (mol_pic.bbox[2] / 2)
    if mol_page == molecule_segment.start_page:
        return abs(mol_mean_y-molecule_segment.upper_y)
    # elif mol_page == molecule_segment.end_page:
    #     return abs(mol_mean_y-text_y_to_pic_y(molecule_segment.upper_y))
    else:
        return 10000

def process_pic_by_proximity(molecule_segments, mol_pic):
    mol_pic.suspected_segments = []
    for segment_idx, molecule_segment in enumerate(molecule_segments):
        proximity = check_mol_pic_proximity(molecule_segment, mol_pic)
        if proximity<10000:
            mol_pic.suspected_segments.append((segment_idx, proximity))
    if mol_pic.suspected_segments:
        mol_pic.suspected_segments = sorted(mol_pic.suspected_segments, key=lambda x: x[1])

def get_pic_proximity_list(molecule_segments, mol_pic_clusters):
    full_proximity_list = []
    for pic_idx, mol_pic_cluster in enumerate(mol_pic_clusters):
        process_pic_by_proximity(molecule_segments, mol_pic_cluster.leading_pic)
        possible_segments = mol_pic_cluster.leading_pic.suspected_segments
        if possible_segments:
            pic_proximity_list = [(pic_idx, possible_segment_idx, proximity) for possible_segment_idx, proximity in possible_segments]
            full_proximity_list+=pic_proximity_list
    sorted_proximity_list = sorted(full_proximity_list, key=lambda x: x[2])
    return sorted_proximity_list

def inner_match_mol_pics_to_molecule_segments(molecule_segments, mol_pic_clusters, sorted_proximity_list, cap='min', already_used_mol_pics_indices=[]):
    used_mol_pics_indices = already_used_mol_pics_indices
    for pic_idx, possible_segment_idx, _ in sorted_proximity_list:
        molecule_segment = molecule_segments[possible_segment_idx]
        molecule_count = len(molecule_segment.mol_pics)
        if cap=='min':
            cap_limit = molecule_segment.min_molecule_count
        elif cap=='max':
            cap_limit = molecule_segment.max_molecule_count
        else:
            cap_limit = 0
        if molecule_count<cap_limit and pic_idx not in used_mol_pics_indices:
            # molecule_segment.mol_pics.append(mol_pic_clusters[pic_idx]) # .leading_pic
            molecule_segment.mol_pics.append(mol_pic_clusters[pic_idx].leading_pic)
            used_mol_pics_indices.append(pic_idx)
    return used_mol_pics_indices
        
def match_mol_pic_clusters_to_molecule_segments(molecule_segments, mol_pic_clusters, match_up_to_max_num=False):
    sorted_proximity_list = get_pic_proximity_list(molecule_segments, mol_pic_clusters)
    used_mol_pics_indices = inner_match_mol_pics_to_molecule_segments(molecule_segments, mol_pic_clusters, sorted_proximity_list, cap='min', already_used_mol_pics_indices=[])
    if match_up_to_max_num:
        used_mol_pics_indices = inner_match_mol_pics_to_molecule_segments(molecule_segments, mol_pic_clusters, sorted_proximity_list, cap='max', already_used_mol_pics_indices=used_mol_pics_indices)  