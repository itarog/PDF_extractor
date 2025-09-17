import os
from collections import defaultdict
from .metadata import extract_metadata_from_raw_pdf
from .full_process import process_doc_text_first, process_doc_pics_first
from .storeage_obj import ProccessedPdf, ProccessedPdfPictures, ProccessedMoleculeSegments, save_object, load_mol_pic_clusters_dict, load_molecule_segments_dict
from .post_processing import get_filled_matched_molecule_segments

from .label_studio_wrappers.ls_setup import get_label_config, setup_label_studio_project, get_annot_value_from_task
from .label_studio_wrappers.molecule_segment_to_ls import molecule_segments_to_label_studio_dir

def store_in_pkl(target_dir, part='full', pdf_file=None, metadata=None, molecule_segments=None, mol_pic_clusters=None):
    pkl_filename = pdf_file.replace('pdf', 'pkl')
    if part=='full':
        final_obj = ProccessedPdf(pdf_file, metadata, molecule_segments, mol_pic_clusters)
    elif part=='pics':
        pkl_filename = 'pics_'+pkl_filename
        final_obj = ProccessedPdfPictures(pdf_file, metadata, mol_pic_clusters)
    elif part=='text':
        pkl_filename = 'text_'+pkl_filename
        final_obj = ProccessedMoleculeSegments(pdf_file, metadata, molecule_segments)
    else:
        print('Exit')
        return None
    save_object(final_obj, target_dir, pkl_filename)

def process_doc_list_text_first(input_dir, save_dir=None, verbose=True, **kawrgs):
    pdf_files = [f for f in os.listdir(input_dir) if f.endswith('pdf')]
    results_dict = dict()
    for file_idx, pdf_file in enumerate(pdf_files):
        if verbose:
            print(file_idx, pdf_file)
        pdf_path = os.path.join(input_dir, pdf_file)
        try:
            metadata = extract_metadata_from_raw_pdf(pdf_path)
            molecule_segments, mol_pic_clusters = process_doc_text_first(pdf_path, **kawrgs)
            results_dict[pdf_file] = (molecule_segments, mol_pic_clusters)
            if save_dir:
                store_in_pkl(save_dir, 'text', pdf_file, metadata, molecule_segments, mol_pic_clusters)
            if verbose:
                print(f'success with {pdf_file}')
                print(f'num of molecule segments {len(molecule_segments)}')
        except:
            if verbose:
                print(f'failed with {pdf_file}')  
    return results_dict

def process_doc_list_pics_first(input_dir, pre_pics_dict=None, save_dir=None, verbose=True, **kawrgs):
    pdf_files = [f for f in os.listdir(input_dir) if f.endswith('pdf')]
    results_dict = dict()
    if pre_pics_dict is None:
        pre_pics_dict = dict()
    for file_idx, pdf_file in enumerate(pdf_files):
        if verbose:
            print(file_idx, pdf_file)
        pdf_path = os.path.join(input_dir, pdf_file)
        try:
            metadata = extract_metadata_from_raw_pdf(pdf_path)
            molecule_segments, mol_pic_clusters = process_doc_pics_first(pdf_path, pre_taken_pics=pre_pics_dict.get(pdf_file), **kawrgs)
            results_dict[pdf_file] = (molecule_segments, mol_pic_clusters)
            if save_dir:
                store_in_pkl(save_dir, 'full', pdf_file, metadata, molecule_segments, mol_pic_clusters)
            if verbose:
                print(f'success with {pdf_file}')
                print(f'num of molecule segments {len(molecule_segments)}')
        except:
            if verbose:
                print(f'failed with {pdf_file}')  
    return results_dict
     
def load_or_process_data(pdf_dir=None, pkl_pic_dir=None, pkl_text_dir=None, verbose=True):
    if pkl_text_dir:
        results_dict = load_molecule_segments_dict(pkl_text_dir)
        filled_matched_segments_dict = {filename: get_filled_matched_molecule_segments(molecule_segments) for filename, molecule_segments in results_dict.items()}
    elif pdf_dir:
        loaded_pics_dict = load_mol_pic_clusters_dict(pkl_pic_dir) if pkl_pic_dir else None
        results_dict = process_doc_list_pics_first(input_dir=pdf_dir, pre_pics_dict=loaded_pics_dict, verbose=verbose)
        filled_matched_segments_dict = {filename: get_filled_matched_molecule_segments(molecule_segments) for filename, (molecule_segments, *_) in results_dict.items()}
    else:
        raise ValueError('provide pdf dir or loaded data')
    return filled_matched_segments_dict

def pdf_dir_to_label_studio(output_dir, pdf_dir, label_studio_config, pkl_pic_dir=None, pkl_text_dir=None, verbose=True):
    task_id = 1
    filled_matched_segments_dict = load_or_process_data(pdf_dir, pkl_pic_dir, pkl_text_dir, verbose)
    all_database_entries = defaultdict(list)
    original_data_tracker = dict()
    for filename, (f_segments, m_segments) in filled_matched_segments_dict.items():
        clean_filename = filename.rstrip('.pdf')
        segment_dir = os.path.join(output_dir, clean_filename)
        os.makedirs(segment_dir, exist_ok=True)
        label_studio_config['project_name'] = clean_filename
        label_studio_config['storage_config']['path'] = segment_dir
        label_studio_config['label_config'] = get_label_config(f_segments)
        ls, project_id, user_id, tasks_client, annot_client = setup_label_studio_project(**label_studio_config)
        pdf_loc = os.path.join(pdf_dir, filename) # can only be done with pdf_dir
        molecule_segment_labels = molecule_segments_to_label_studio_dir(pdf_loc, f_segments, segment_dir, task_id, project_id, user_id)
        for label_dict in molecule_segment_labels:
            predicted_annot = get_annot_value_from_task(label_dict)
            task_data = label_dict.get('data')
            task = tasks_client.create(project=project_id, data=task_data)
            task_id = task.id
            # Update task id in annot!!
            # predicted_annot
            annot_client.create(id = task_id, result=predicted_annot, task = task_id, project = project_id)
        original_data_tracker[filename] = (project_id, f_segments)
    return all_database_entries, original_data_tracker