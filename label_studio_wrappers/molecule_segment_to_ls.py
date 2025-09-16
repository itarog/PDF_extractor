import uuid
import os
import json
from datetime import datetime

from .create_labels import test_text_line_to_annot_dict, mol_pic_to_annot_dict
from ..molecule_segment.molecule_segment_obj import get_relavent_pages
from .image_transformers import pdf_to_np_images
from ..general import minimize_pdf_to_relavent_pages

def get_local_storage_prefix():
    return '/data/local-files/?d='

def molecule_segment_to_annotation_dict(molecule_segment, task_id=1, project_id=1, user_id=1):
    results = []
    for test_text_line in molecule_segment.test_text_sequence.test_text_lines:
        annot_dict_list = test_text_line_to_annot_dict(test_text_line, molecule_segment.start_page)
        results.extend(annot_dict_list)
    if molecule_segment.mol_pics:
        annot_dict_list = mol_pic_to_annot_dict(molecule_segment.mol_pics[0], annot_type='Molecule')
        results.extend(annot_dict_list)
    annotation_dict = {
                        "id": task_id,
                        "completed_by": user_id,
                        "result": results,
                        "was_cancelled": False,
                        "ground_truth": False,
                        "created_at": datetime.utcnow().isoformat() + "Z",
                        "updated_at": datetime.utcnow().isoformat() + "Z",
                        "lead_time": 24.175,
                        "prediction": {},
                        "result_count": len(results),
                        "unique_id": str(uuid.uuid4()),
                        "task": task_id,
                        "project": project_id,
                        "updated_by": user_id
                        }
    return annotation_dict

def adjust_loc(loc_str):
    new_loc_str = loc_str.replace("C:\\", "").replace("\\", "%5C")
    return new_loc_str

def molecule_segment_to_label_studio_json(molecule_segment, image_path, task_id=1, project_id=1, user_id=1):
    annotation_dict = molecule_segment_to_annotation_dict(molecule_segment, task_id=task_id, project_id=project_id, user_id=user_id)
    pages = []
    local_storage_prefix = get_local_storage_prefix()
    base_loc = local_storage_prefix + adjust_loc(image_path)
    for page_num in get_relavent_pages(molecule_segment):
        page = base_loc + "%5C" + f"page_{page_num}.png"
        pages.append(page)
    label_studio_entry = {
                        "id": task_id,
                        "annotations": [annotation_dict],
                        "data": {"pages": pages},
                        "meta": {},
                        "created_at": datetime.utcnow().isoformat() + "Z",
                        "updated_at": datetime.utcnow().isoformat() + "Z",
                        "project": project_id,
                        "updated_by": user_id
                        }
    return [label_studio_entry]

def molecule_segments_to_label_studio_dir(pdf_loc, molecule_segments, label_studio_storage_dir, task_id=1, project_id=1, user_id=1):
    os.makedirs(label_studio_storage_dir, exist_ok=True)
    all_relavent_pages = []
    all_labels = []
    for segment_idx, molecule_segment in enumerate(molecule_segments):
        all_relavent_pages.extend(get_relavent_pages(molecule_segment))
        label_studio_data = molecule_segment_to_label_studio_json(molecule_segment, label_studio_storage_dir,
                                                                  task_id, project_id, user_id)
        all_labels.append(label_studio_data[0])
        final_path = os.path.join(label_studio_storage_dir, f"molecule_segment_{segment_idx}.json")
        with open(final_path, "w") as f:
            json.dump(label_studio_data, f, indent=4)
    temp_pdf_filename = 'my_small_pdf.pdf'
    minimize_pdf_to_relavent_pages(input_pdf_path=pdf_loc,
                                    output_pdf_path=temp_pdf_filename,
                                    page_numbers=all_relavent_pages)
    pdf_to_np_images(temp_pdf_filename, all_relavent_pages, label_studio_storage_dir)
    return all_labels #, all_database_entries, all_saved_filenames 
