from .matching import match_mol_pic_clusters_to_molecule_segments
from .text_processing.init_processing import extract_text_with_multi_idx
from .molecule_segment.segments_creation import locate_molecule_segments
from .molecule_segment.sequences2segments import process_molecule_segment_text
from .molecule_segment.segements_merging import adjust_molecule_segments_by_common_sequence
from .mol_pic import extract_pics_from_pdf
from .mol_pic_cluster import sort_mol_pics_to_clusters
from .storeage_obj import load_pickle_by_filename

def process_text_doc(pdf_path, tokens_mark=80, spaces_mark=35):
    page_lines_with_multi_idx = extract_text_with_multi_idx(pdf_path)
    molecule_segments = locate_molecule_segments(page_lines_with_multi_idx, tokens_mark=tokens_mark, spaces_mark=spaces_mark)
    processed_molecule_segments = process_molecule_segment_text(molecule_segments)
    final_molecule_segments = adjust_molecule_segments_by_common_sequence(processed_molecule_segments)
    return final_molecule_segments

def process_pic_doc(pdf_path, save_pics=False, save_dir='', pages=[]):
    mol_pics = extract_pics_from_pdf(pdf_path, save_pics, save_dir, pages)
    mol_pic_clusters = sort_mol_pics_to_clusters(mol_pics)
    return mol_pic_clusters

def process_doc_text_first(pdf_path, process_pics=False, tokens_mark=80, spaces_mark=35):
    final_molecule_segments = process_text_doc(pdf_path, tokens_mark, spaces_mark)
    pages = [molecule_segment.start_page for molecule_segment in final_molecule_segments]
    if process_pics:
        mol_pic_clusters = process_pic_doc(pdf_path, pages=pages)
        match_mol_pic_clusters_to_molecule_segments(final_molecule_segments, mol_pic_clusters, match_up_to_max_num=False)
        # match_mol_pic_clusters_to_molecule_segments(final_molecule_segments, mol_pic_clusters, match_up_to_max_num=True)
    else:
        mol_pic_clusters = None
    return final_molecule_segments, mol_pic_clusters

def load_default_optimize_options(optimize_options=None):
    if optimize_options is None:
        optimize_options = [{'tokens': 40, 'spaces': 20},
                            {'tokens': 40, 'spaces': 30},
                            {'tokens': 40, 'spaces': 40},
                            {'tokens': 60, 'spaces': 20},
                            {'tokens': 60, 'spaces': 30},
                            {'tokens': 60, 'spaces': 40},
                            {'tokens': 80, 'spaces': 20},
                            {'tokens': 80, 'spaces': 30},
                            {'tokens': 80, 'spaces': 40}]
    return optimize_options

def optimize_text_grab_by_pic_matching(pdf_path, mol_pic_clusters, optimize_options=None):
    optimize_options = load_default_optimize_options(optimize_options)
    best_result, best_condition = 0, None
    for opt_option in optimize_options:
        molecule_segments = process_text_doc(pdf_path, tokens_mark=opt_option.get('tokens'), spaces_mark=opt_option.get('spaces'))
        match_mol_pic_clusters_to_molecule_segments(molecule_segments, mol_pic_clusters, False)
        matched_segments = [molecule_segment for molecule_segment in molecule_segments if molecule_segment.mol_pics]
        current_result = len(matched_segments)
        if current_result>best_result:
            best_result = current_result
            best_condition = opt_option
    molecule_segments = process_text_doc(pdf_path, tokens_mark=best_condition.get('tokens'), spaces_mark=best_condition.get('spaces'))
    match_mol_pic_clusters_to_molecule_segments(molecule_segments, mol_pic_clusters, False)
    return molecule_segments

def process_doc_pics_first(pdf_path, pre_taken_pics=None, save_pics=False, save_dir='', optimize_options=None):
    if pre_taken_pics:
        mol_pic_clusters = pre_taken_pics
    else:
        mol_pic_clusters = process_pic_doc(pdf_path, save_pics, save_dir)
    final_molecule_segments = optimize_text_grab_by_pic_matching(pdf_path, mol_pic_clusters, optimize_options)
    # match_mol_pic_clusters_to_molecule_segments(molecule_segments, mol_pic_clusters, True)
    return final_molecule_segments, mol_pic_clusters