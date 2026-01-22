import numpy as np
import re
import logging

from .molname_to_SMILES import opsin_query, pubchem_name_to_smiles
from .molecule_segment_obj import MoleculeSegment
from build.tokenizer.molecule_name import get_molecule_name_probability
from DECIMER import predict_SMILES

logger = logging.getLogger(__name__)

def get_line_statistics(page_lines_with_multi_idx, token_patterns=None, debugging=False):
    tokens_percentages, num_of_spaces_list, suspected_lines = [], [], []
    for actual_idx, (_, line_text, _) in enumerate(page_lines_with_multi_idx):
        edited_line_text = line_text.replace('Experimental','').replace('experimental', '').replace('10.09.08.07.06.05.04.03.02.01.00.0-1.0', '')
        len_line = len(edited_line_text.replace(' ', ''))
        num_of_spaces = edited_line_text.count(' ')
        if len_line>10:
            if not line_text.startswith('Rf') and not line_text.startswith('mp'):
                line_molecule_name_probability = get_molecule_name_probability(edited_line_text, token_patterns)
                tokens_percentages.append(line_molecule_name_probability)
                num_of_spaces_list.append(num_of_spaces)
                suspected_lines.append(actual_idx)
    return tokens_percentages, num_of_spaces_list, suspected_lines

def get_lines_based_on_percentile(tokens_percentages, num_of_spaces_list, suspected_lines, tokens_mark=80, spaces_mark=35):
    selected_lines = []
    tokens_percentile = np.percentile(tokens_percentages, tokens_mark)
    spaces_percentile = np.percentile(num_of_spaces_list, spaces_mark)
    for tokens_percentage, num_of_spaces, actual_idx in zip(tokens_percentages, num_of_spaces_list, suspected_lines):
        if tokens_percentage>tokens_percentile and num_of_spaces<spaces_percentile:
            selected_lines.append(actual_idx)
    return selected_lines

def get_line_based_on_first_over(tokens_percentages, suspected_lines, over_mark=50):
    tokens_percentile = np.percentile(tokens_percentages, over_mark)    
    for tokens_percentage, actual_idx in zip(tokens_percentages, suspected_lines):
        if tokens_percentage>tokens_percentile:
            return [actual_idx]
        
def create_molecule_segments(page_lines_with_multi_idx, selected_lines):
    molecule_segments = []
    if selected_lines:
        for idx in range(len(selected_lines)-1):
            start_actual_idx = selected_lines[idx]
            end_actual_idx = selected_lines[idx+1]
            lines = page_lines_with_multi_idx[start_actual_idx:end_actual_idx]
            molecule_segments.append(MoleculeSegment(lines))
        molecule_segments.append(MoleculeSegment(page_lines_with_multi_idx[selected_lines[-1]:]))
    return molecule_segments

def clean_molecule_name(molecule_name, replacement=' '):
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    cleaned_molecule_name = re.sub(invalid_chars, replacement, molecule_name)
    cleaned_molecule_name = cleaned_molecule_name.strip(" .")
    return cleaned_molecule_name

def find_mol_tag(text):
    pattern = r'\((\d+[a-zA-Z]?)\)' # r'\((\d+)\)'
    matches = re.findall(pattern, text)
    if matches:
        return matches[0]
    else:
        return None

def search_molecule_name(text):
    mol_tag = find_mol_tag(text)
    if mol_tag:
        full_tag = '(' + mol_tag + ')'
        end_idx = text.find(full_tag)
        molecule_name = text[:end_idx].strip()
    else:
        molecule_name = None
    return molecule_name

def get_molecule_segment_name(molecule_segment):
    molecule_name = None
    num_lines = 3
    while num_lines>0 and num_lines<len(molecule_segment.segment_lines) and molecule_name==None:
        text = ''.join(line for multi_idx, line, bbox in molecule_segment.segment_lines[:num_lines])
        molecule_name = search_molecule_name(text)
        num_lines-=1
    if molecule_name:
        return molecule_name
    else:
        molecule_name = molecule_segment.segment_lines[0][1]
        cleaned_molecule_name = clean_molecule_name(molecule_name)
        return cleaned_molecule_name

def assign_molecule_segment_name(molecule_segments):
    for molecule_segment in molecule_segments:
        molecule_segment.molecule_name = get_molecule_segment_name(molecule_segment)

def locate_molecule_segments(page_lines_with_multi_idx, token_patterns=None, debugging=False, locate_by='percentile', tokens_mark=40, spaces_mark=20, over_mark=50):
    tokens_percentages, num_of_spaces_list, suspected_lines = get_line_statistics(page_lines_with_multi_idx, token_patterns, debugging)
    if locate_by=='percentile':
        selected_lines = get_lines_based_on_percentile(tokens_percentages, num_of_spaces_list, suspected_lines, tokens_mark, spaces_mark)
    if locate_by=='first_over':
        selected_lines = get_line_based_on_first_over(tokens_percentages, suspected_lines, over_mark)
    molecule_segments = create_molecule_segments(page_lines_with_multi_idx, selected_lines)
    assign_molecule_segment_name(molecule_segments)
    return molecule_segments

def fill_smiles(molecule_segments):
    new_molecule_segments = []
    for molecule_segment in molecule_segments:
        molecule_name = molecule_segment.molecule_name
        try:
            info = opsin_query(molecule_name)
            smiles = info.get('smiles')
        except Exception as e:
            logger.debug(f"SMILES lookup failed for '{molecule_name}': {e}")
            smiles = ''
        if smiles == '':
            smiles = pubchem_name_to_smiles(molecule_name)
        molecule_segment.molecule_name_smiles = smiles
        if len(molecule_segment.mol_pics)>0:
            mol_pic = molecule_segment.mol_pics[0]
            molecule_segment.mol_pic_smiles = predict_SMILES(mol_pic.pic)
        new_molecule_segments.append(molecule_segment)
    return new_molecule_segments