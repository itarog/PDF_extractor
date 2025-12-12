import copy
import os
from .ls_setup import ls_login, get_annot_value_from_task

def load_label_studio_data(api_key, project_id, ls_url=None):
    ls = ls_login(api_key, ls_url)
    exported_data = ls.projects.exports.as_json(project_id)
    return exported_data

def get_bbox_from_annot(annot):
    inner_dict = annot.get('value')
    bbox = [inner_dict.get('x'),
            inner_dict.get('y'),
            inner_dict.get('width'),
            inner_dict.get('height')]
    return bbox

def get_value_from_annot(annot):
    annot_id = annot.get('id')
    inner_dict = annot.get('value')
    if 'rectanglelabels' in inner_dict.keys():
        inner_values = inner_dict.get('rectanglelabels')
    elif 'text' in inner_dict.keys():
        inner_values = inner_dict.get('text')
    return annot_id, inner_values[0]

def process_task(task):
    annot_list = get_annot_value_from_task(task)
    annot_dict = dict()
    current_id = None
    for temp_idx in range(len(annot_list)//2):
        key_annot = annot_list[2*temp_idx]
        key_id, key = get_value_from_annot(key_annot)
        value_annot = annot_list[2*temp_idx + 1]
        _, text = get_value_from_annot(value_annot)
        bbox = get_bbox_from_annot(value_annot)
        if current_id is None:
            current_id = key_id
            annot_dict[key] = (text, [bbox])
        elif current_id == key_id:
            o_text, o_bbox = annot_dict.get(key)
            annot_dict[key] = (o_text, [o_bbox[0], bbox]) 
        else:
            current_id = key_id
            annot_dict[key] = (text, [bbox])
    return annot_dict

def update_changes(molecule_segment, annot_dict):
    new_molecule_segment = copy.deepcopy(molecule_segment)
    annot_keys = annot_dict.keys()
    for line_idx, test_text_line in enumerate(molecule_segment.test_text_sequence.test_text_lines):
        test_type = test_text_line.test_type
        if test_type in annot_keys:
            new_text, new_bbox_list = annot_dict.get(test_type)
            new_molecule_segment.test_text_sequence.test_text_lines[line_idx].text = new_text
            # new_bbox_list_pn = []
            # for n_bbox, (page_num, o_bbox) in zip(new_bbox_list, molecule_segment.test_text_sequence.test_text_lines[line_idx].bbox_list):
            #     new_bbox_list_pn.append((page_num, n_bbox))
            # new_molecule_segment.test_text_sequence.test_text_lines[line_idx].bbox_list = new_bbox_list_pn
    if 'Molecule' in annot_keys:

        mol_pic = copy.deepcopy(molecule_segment.mol_pics[0])
        
        _, new_bbox_list = annot_dict.get('Molecule')
        new_bbox = tuple(new_bbox_list[0])

        if mol_pic.bbox != new_bbox:
            mol_pic.bbox = tuple(new_bbox)
            print(f"Image in page {mol_pic.page_num} was updated following label_studio")

        new_molecule_segment.mol_pics = [mol_pic]
    return new_molecule_segment

def process_changes(api_key, project_id, molecule_segments, ls_url=None):
    updated_tasks = load_label_studio_data(api_key, project_id, ls_url)
    new_molecule_segments = []
    for molecule_segment, segment_task in zip(molecule_segments, updated_tasks):
        annot_dict = process_task(segment_task)
        new_molecule_segment = update_changes(molecule_segment, annot_dict)
        new_molecule_segments.append(new_molecule_segment)
    return new_molecule_segments