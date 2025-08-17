import os
from .metadata import extract_metadata_from_raw_pdf
from .full_process import process_doc_text_first, process_doc_pics_first
from .storeage_obj import ProccessedPdf, ProccessedPdfPictures, ProccessedMoleculeSegments, save_object

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
    for file_idx, pdf_file in enumerate(pdf_files):
        if verbose:
            print(file_idx, pdf_file)
        pdf_path = os.path.join(input_dir, pdf_file)
        try:
            metadata = extract_metadata_from_raw_pdf(pdf_path)
            molecule_segments, mol_pic_clusters = process_doc_text_first(pdf_path, **kawrgs)
            if save_dir:
                store_in_pkl(save_dir, 'text', pdf_file, metadata, molecule_segments, mol_pic_clusters)
            if verbose:
                print(f'success with {pdf_file}')
                print(f'num of molecule segments {len(molecule_segments)}')
        except:
            if verbose:
                print(f'failed with {pdf_file}')  

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
            results_dict[pdf_file] = [molecule_segments, mol_pic_clusters]
            if save_dir:
                store_in_pkl(save_dir, 'full', pdf_file, metadata, molecule_segments, mol_pic_clusters)
            if verbose:
                print(f'success with {pdf_file}')
                print(f'num of molecule segments {len(molecule_segments)}')
        except:
            if verbose:
                print(f'failed with {pdf_file}')  
    return results_dict
    # save_page_pic_dir = os.path.join(FilePaths.PPIC_DIR.value, pdf_file.replace('.pdf',''))
    # if not os.path.exists(save_page_pic_dir):
    #     os.mkdir(save_page_pic_dir)
    # molecule_segments, mol_pic_clusters = process_doc_pics_first(pdf_path, save_pics=True, save_dir=save_page_pic_dir)