import numpy as np
import pandas as pd
import os
import subprocess

from PIL import Image
from scipy.optimize import linear_sum_assignment

from build.demo_data.inner_validation import compare_values, string_similarity, peak_confusion_matrix
from build.streamlit_wrappers import gen_database_from_ms_list

def get_smiles_score(gt_molecule, extracted_molecule):
    smiles_sim, gt_smiles, sus_smiles = None, None, None
    if hasattr(extracted_molecule, 'molecule_image'): 
        gt_smiles = gt_molecule.opsin_smiles
        sus_smiles = extracted_molecule.molecule_smiles_by_images
        if gt_smiles and sus_smiles:
            try:
                # gt_smiles is sometimes np.nan for some reason..
                smiles_sim = string_similarity(gt_smiles, sus_smiles)
            except:
                smiles_sim = None
        else:
            smiles_sim = None
    return smiles_sim

def get_molecule_name_score(gt_molecule, extracted_molecule):
    molecule_name_score = 0
    mol_name = gt_molecule.molecule_name 
    sus_mol_name = extracted_molecule.molecule_name 
    molecule_name_score = compare_values(mol_name, sus_mol_name)
    return molecule_name_score

def get_test_text_score(gt_test, extracted_molecule):
    gt_test_type = gt_test.test_type
    for extracted_test in extracted_molecule.molecule_tests:
        extracted_test_type = extracted_test.test_type
        if extracted_test_type == gt_test_type:
            try:
                # TEXT SIM
                gt_test_text = gt_test.test_text
                extracted_test_text = extracted_test.test_text
                test_sim_score = compare_values(gt_test_text, extracted_test_text)
            except:
                test_sim_score = None

            # Confusion Matrix
            TP, FP, FN = peak_confusion_matrix(gt_test.peak_list, extracted_test.peak_list)
            precision = round(TP / (TP + FP) if (TP + FP) > 0 else 0.0, 2)
            recall = round(TP / (TP + FN) if (TP + FN) > 0 else 0.0, 2)
            f1 = round(2 * precision*recall /(precision + recall) if (precision + recall) > 0 else 0.0, 2)

            return TP, FP, FN, precision, recall, f1, test_sim_score

    return [None]*7 
    
def get_similarity_score(gt_molecule, extracted_molecule):
    running_score, number_of_factors = 0, 0
    scores_dict = dict()

    # SMILES SCORE
    smiles_sim = get_smiles_score(gt_molecule, extracted_molecule)
    if smiles_sim:
        running_score += smiles_sim
        number_of_factors += 1
    scores_dict['smiles sim'] = smiles_sim

    # NAME SCORE
    molecule_name_score = get_molecule_name_score(gt_molecule, extracted_molecule)
    if molecule_name_score>0:
        running_score += molecule_name_score
        number_of_factors += 1
    scores_dict['molecule_name_score'] = molecule_name_score
    
    # TEST SCORES
    for gt_test in gt_molecule.gt_tests:
        TP, FP, FN, precision, recall, f1, test_sim_score = get_test_text_score(gt_test, extracted_molecule)
        if TP:
            gt_test_type = gt_test.test_type
            if test_sim_score:
                scores_dict[gt_test_type+'_text_sim_score'] = test_sim_score
                running_score += test_sim_score
                number_of_factors +=1
            scores_dict[gt_test_type+'_TP'] = TP
            scores_dict[gt_test_type+'_FP'] = FP
            scores_dict[gt_test_type+'_FN'] = FN
            scores_dict[gt_test_type+'_precision'] = precision
            scores_dict[gt_test_type+'_recall'] = recall
            scores_dict[gt_test_type+'_F1'] = f1
            if f1>0:
                running_score+=f1
                number_of_factors+=1

    if number_of_factors>0:
        final_score = round(running_score/number_of_factors, 2)
    else:
        final_score = 0.0
    return final_score, scores_dict

def score_extracted_gt_data(gt_molecules, extracted_molecules, scores_thers=0.75, allow_unmatched=True):
    n_extracted = len(extracted_molecules)
    n_gt = len(gt_molecules)
    if n_extracted>0 and n_gt>0:
        # Step 1: build score matrix (segments x gt entries)
        score_matrix = np.zeros((n_extracted, n_gt))
        extra_data = {}            

        for i, extracted_molecule in enumerate(extracted_molecules):
            for j, gt_molecule in enumerate(gt_molecules):
                score, scores_dict = get_similarity_score(gt_molecule, extracted_molecule)
                score_matrix[i, j] = score
                extra_data[(i, j)] = scores_dict

        # Step 2: add dummy GT columns if allowing unmatched
        if allow_unmatched:
            dummy_cols = np.zeros((n_extracted, n_extracted))  # each segment can match to "no GT"
            score_matrix = np.hstack([score_matrix, dummy_cols])

        # Step 3: Hungarian algorithm (maximize score -> minimize -score)
        row_ind, col_ind = linear_sum_assignment(-score_matrix)

        # Step 4: collect results
        all_scores, scores_dict_list, pairwise_molecules = [], [], []
        for i, j in zip(row_ind, col_ind):
            if j >= n_gt:  # matched to dummy -> no GT assigned
                continue  

            score = score_matrix[i, j]
            scores_dict = extra_data[(i, j)]
            
            if score > scores_thers:
                all_scores.append(score)
                scores_dict_list.append(scores_dict)
                pairwise_molecules.append({'gt_molecule': gt_molecules[j], 'extracted_molecule': extracted_molecules[i]}) 
    return all_scores, scores_dict_list, pairwise_molecules

def get_all_rel_cols(all_scores_df):
    all_scores_df.columns #.mean()
    id_set = ['smiles sim', 'molecule_name_score']
    hnmr_set, cnmr_set, ir_set, ms_set = [], [], [], []
    for col in all_scores_df.columns:
        if 'precision' in col or 'recall' in col or 'F1' in col:
            if col.startswith('1H NMR'):
                hnmr_set.append(col)
            elif col.startswith('13C NMR'):
                cnmr_set.append(col)
            elif col.startswith('MS'):
                ms_set.append(col)
            elif col.startswith('IR'):
                ir_set.append(col)
    return id_set, hnmr_set, cnmr_set, ms_set, ir_set

def process_gt_extracted_scoring(scoring_dict):
    all_scores = []
    all_scores_dict = []
    
    # flatten results
    for gt_fname, file_scoring_dict in scoring_dict.items():
        all_scores.extend(file_scoring_dict.get('scores_dist'))
        all_scores_dict.extend(file_scoring_dict.get('detailed_scores_dist'))
    
    mean_score = round(np.mean(all_scores), 2)
    std_score = round(np.std(all_scores), 2)

    all_scores_df = pd.DataFrame(all_scores_dict)

    col_sets = get_all_rel_cols(all_scores_df)
    summary_details = dict()
    summary_details['Overall mean score'] = f'{mean_score} ± {std_score}'
    for col_set in col_sets:
        try:
            reduced_df = all_scores_df[col_set]
            mean_col = reduced_df.mean().round(2)
            std_col = reduced_df.std().round(2)
            for col in col_set:
                if 'F1' in col or 'molecule_name' in col or 'smiles' in col:
                    summary_details[col] = f'{mean_col[col]} ± {std_col[col]}'
        except:
            pass

    return summary_details, all_scores_df

def gen_database_from_extracted_molecules(extracted_molecule_list, image_dir=None, graph_sketch=False):
    mol_dict_list = []

    for mol_idx, extracted_mol in enumerate(extracted_molecule_list):
        mol_dict = dict()
        images = []
        mol_dict['molecule_name'] = extracted_mol.molecule_name
        mol_dict['file_name'] = extracted_mol.file_name
        mol_dict['molecule_smiles_by_images'] = extracted_mol.molecule_smiles_by_images
        mol_dict['molecule_smiles_by_name'] = extracted_mol.molecule_smiles_by_name
        mol_dict['molecule_smiles_confidence_score'] = extracted_mol.molecule_smiles_confidence_score

        # --- Add Provenance Information ---
        if extracted_mol.provenance_segment:
            prov_seg = extracted_mol.provenance_segment
            mol_dict['provenance_page'] = prov_seg.start_page
            
            # Calculate the union of all bounding boxes for the segment
            min_x0, min_y0 = float('inf'), float('inf')
            max_x1, max_y1 = 0, 0
            if prov_seg.segment_lines:
                for _, _, bbox in prov_seg.segment_lines:
                    # Bbox is (y0, x0, y1, x1), convert to (x0, y0, x1, y1) for consistency
                    y0, x0, y1, x1 = bbox
                    min_x0 = min(min_x0, x0)
                    min_y0 = min(min_y0, y0)
                    max_x1 = max(max_x1, x1)
                    max_y1 = max(max_y1, y1)
                mol_dict['provenance_bbox'] = f"{min_x0},{min_y0},{max_x1},{max_y1}"
            else:
                mol_dict['provenance_bbox'] = ""
        else:
            mol_dict['provenance_page'] = ""
            mol_dict['provenance_bbox'] = ""
        # ------------------------------------

        img = extracted_mol.molecule_image
        mol_dict['molecule_np_array'] = img
        if not img is None:
            img_name = f'image_{mol_idx}.png'
            image_path = os.path.join(image_dir, img_name)
            
            img = Image.fromarray(img)
            img.save(image_path)

            images.append(img_name)

        normalized_test_names = ['1H NMR', '13C NMR', 'IR', 'MS']
        for extracted_test in extracted_mol.molecule_tests:
            test_type = extracted_test.test_type 
            test_text = extracted_test.test_text
            for norm_test_name in normalized_test_names:
                if norm_test_name in test_type:
                    mol_dict[norm_test_name] = test_text
            # mol_dict[test_type] = test_text
            if graph_sketch:
                pass
        mol_dict['image_path'] = '; '.join(images)
        mol_dict_list.append(mol_dict)

    results_df = pd.DataFrame(mol_dict_list)
    return results_df

def setup_database(extracted_molecule_list, database_name='my_database', export_dir=None, image_dir_name='images', graph_sketch=False):
    if export_dir is None:
        export_dir = os.getcwd()
    database_dir_path = os.path.join(export_dir, database_name)
    os.makedirs(database_dir_path, exist_ok=True)
    image_dir_path = os.path.join(database_dir_path, image_dir_name)
    os.makedirs(image_dir_path, exist_ok=True)
    results_df = gen_database_from_extracted_molecules(extracted_molecule_list, image_dir=image_dir_path, graph_sketch=graph_sketch)
    csv_fname = f'{database_name}.csv'
    csv_path = os.path.join(database_dir_path, csv_fname)
    results_df.to_csv(csv_path, index=False)          
    return csv_path, image_dir_path
