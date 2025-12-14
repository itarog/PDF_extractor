import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
import os
import subprocess

from demo_data.inner_validation import compare_values, string_similarity, peak_confusion_matrix
from streamlit_wrappers import gen_database_from_ms_list

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
    mol_name = gt_molecule.molecule_name # gt_dictlist[0].get('molecule_name')
    sus_mol_name = extracted_molecule.molecule_name # e_dictlist[0].get('molecule_name')
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

def setup_database(molecule_segments_dict, database_name='my_database', graph_sketch=False):
    m_ms_list_to_export = []
    f_ms_list_to_export = []
    for f_segments, m_segments in molecule_segments_dict.values():
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
