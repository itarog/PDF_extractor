import os
from .storeage_obj import load_pickle_by_dir

def get_loaded_pdf_list_from_dir(pkl_dir):
    loaded_pdf_list = load_pickle_by_dir(pkl_dir)
    return loaded_pdf_list

def unpack_loaded_pdf_list(loaded_pdf_list):
    molecule_segments_dict = {loaded_pdf.file_name: loaded_pdf.molecule_segments for loaded_pdf in loaded_pdf_list}
    pic_clusters_dict = {loaded_pdf.file_name: loaded_pdf.mol_pic_clusters for loaded_pdf in loaded_pdf_list}
    return molecule_segments_dict, pic_clusters_dict

def get_filled_matched_molecule_segments(molecule_segments):
    filled_segments, matched_segments = [], []
    for molecule_segment in molecule_segments:
        if molecule_segment.has_test_text_sequence:
            filled_segments.append(molecule_segment)
            if molecule_segment.mol_pics:
                matched_segments.append(molecule_segment)
    return filled_segments, matched_segments

def analyze_molecule_segments_dict(molecule_segments_dict):
    filled_matched_segments_dict = {file_name: get_filled_matched_molecule_segments(molecule_segments) for file_name, molecule_segments in molecule_segments_dict.items()}
    success_percentage = {file_name: round(len(m_segment)/len(f_segment), 2) for file_name, (f_segment, m_segment) in filled_matched_segments_dict.items() if f_segment}
    num_of_matches = sum(len(m_segment) for _, m_segment in filled_matched_segments_dict.values())
    return filled_matched_segments_dict, success_percentage, num_of_matches

def analyze_pkl_dir(pkl_dir):
    loaded_pdf_list = get_loaded_pdf_list_from_dir(pkl_dir)
    molecule_segments_dict, pic_clusters_dict = unpack_loaded_pdf_list(loaded_pdf_list)
    filled_matched_segments_dict, success_percentage, num_of_matches = analyze_molecule_segments_dict(molecule_segments_dict)
    return molecule_segments_dict, pic_clusters_dict, filled_matched_segments_dict, success_percentage, num_of_matches