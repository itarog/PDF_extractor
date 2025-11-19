import os
import pandas as pd
import subprocess

from PIL import Image
from text_spectra_plotter import (
    parse_proton_nmr, parse_carbon_nmr, parse_ir, parse_ms,
    plot_proton_nmr, plot_carbon_nmr, plot_ir, plot_ms
)
from wrappers import process_doc_list_pics_first, get_filled_matched_molecule_segments

def export_ms_list(ms_list, export_dir=None, image_dir_name='images', graph_sketch=False):
    if export_dir is None:
        export_dir = os.getcwd()
    image_dir_path = os.path.join(export_dir, image_dir_name)
    os.makedirs(image_dir_path, exist_ok=True)
    
    ms_dict_list = []
    for segment_idx, molecule_segment in enumerate(ms_list):
        ms_dict = dict()
        images = []
        ms_dict['molecule_name'] = molecule_segment.molecule_name

        if molecule_segment.mol_pics:
            mol_pic = molecule_segment.mol_pics[0]
            img = Image.fromarray(mol_pic.pic)
            img_name = f'image_{segment_idx}.png'
            image_path = os.path.join(image_dir_path, img_name)
            img.save(image_path)
            images.append(image_path)

        test_text_sequence = molecule_segment.test_text_sequence
        for test_text_line in test_text_sequence.test_text_lines:
            test_type = test_text_line.test_type 
            test_text = test_text_line.text
            ms_dict[test_type] = test_text
            if graph_sketch:
                if '1H NMR' in test_type:
                    parser = parse_proton_nmr
                    plot_fname = f'mol_{segment_idx}_1H_NMR.png'
                    plotter = plot_proton_nmr
                elif '13C NMR' in test_type:
                    parser = parse_carbon_nmr
                    plot_fname = f'mol_{segment_idx}_13C_NMR.png'
                    plotter = plot_carbon_nmr
                elif test_type == 'MS':
                    parser = parse_ms
                    plot_fname = f'mol_{segment_idx}_MS.png'
                    plotter = plot_ms
                elif test_type =='IR':
                    parser = parse_ir
                    plot_fname = f'mol_{segment_idx}_IR.png'
                    plotter = plot_ir
                else:
                    parser = None
                    plotter = None
                if parser:
                    parsed_peaks  = parser(test_text)
                    plot_path = os.path.join(image_dir_path, plot_fname)
                    plotter(parsed_peaks, title=f'mol_{segment_idx}', export_fname=plot_path)
                    images.append(plot_path)     

        ms_dict['image_path'] = '; '.join(images)
        ms_dict_list.append(ms_dict)

    results_df = pd.DataFrame(ms_dict_list)
    return results_df, image_dir_path

def gen_database_from_ms_list(ms_list, export_dir=None, image_dir_name='images', database_name='my_database', graph_sketch=False):
    if export_dir is None:
        export_dir = os.getcwd()
    database_dir_path = os.path.join(export_dir, database_name)
    os.makedirs(database_dir_path, exist_ok=True)
    results_df, image_dir_path = export_ms_list(ms_list, export_dir=database_dir_path, image_dir_name=image_dir_name, graph_sketch=graph_sketch)
    csv_fname = f'{database_name}.csv'
    csv_path = os.path.join(database_dir_path, csv_fname)
    results_df.to_csv(csv_path)
    return csv_path, image_dir_path


def process_pdf_dir_end_to_end(input_dir, verbose=True, backend='yode', database_name='my_database', graph_sketch=False):
    results_dict = process_doc_list_pics_first(input_dir=input_dir, verbose=verbose, backend=backend) # pre_pics_dict=loaded_pics_dict,
    filled_matched_segments_dict = {filename: get_filled_matched_molecule_segments(molecule_segments) for filename, (molecule_segments, *_) in results_dict.items()}
    
    m_ms_list_to_export = []
    f_ms_list_to_export = []
    for f_segments, m_segments in filled_matched_segments_dict.values():
        f_ms_list_to_export+=f_segments
        m_ms_list_to_export+=m_segments

    database_csv_path, image_dir_path = gen_database_from_ms_list(m_ms_list_to_export, database_name=database_name, graph_sketch=graph_sketch)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    run_str_command_1 = f'streamlit run {app_path} '
    run_str_command_2 = f'-- --csv_fpath {database_csv_path} --images_fpath {image_dir_path}'
    run_str_command = run_str_command_1 + run_str_command_2

    cmd_process = subprocess.Popen(run_str_command.split(' '))
    # subprocess.run(run_str_command.split(' '))
    return cmd_process

