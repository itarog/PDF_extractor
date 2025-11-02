import numpy as np
import re
from scipy.optimize import linear_sum_assignment
from difflib import SequenceMatcher

def molecule_segment_to_dict_list(molecule_segment):
    dict_list = []
    mol_name = molecule_segment.molecule_name
    test_text_sequence = molecule_segment.test_text_sequence
    for test_text_line in test_text_sequence.test_text_lines:
        test_type = test_text_line.test_type
        test_text = test_text_line.text
        entry = {'molecule_name': mol_name, 'test_type': test_type, 'test_text': test_text}
        if molecule_segment.mol_pics:
            pic = molecule_segment.mol_pics[0].pic
            entry.update({'mol_pic': pic})
        mol_pic_smiles = getattr(molecule_segment, 'mol_pic_smiles', None)
        if mol_pic_smiles:
            entry.update({'mol_pic_smiles': mol_pic_smiles})
        dict_list.append(entry)
    return dict_list

def string_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def compare_values(gt_value, e_value):
    if gt_value in e_value:
        return 1
    else:
        return round(string_similarity(gt_value, e_value), 2)
    

# ----------------- Parentheses removal -----------------
def remove_parentheses(text: str) -> str:
    """Remove text inside parentheses () and brackets []"""
    PAREN_PATTERN = re.compile(r"\([^()]*\)")
    BRACKET_PATTERN = re.compile(r"\[[^\[\]]*\]")
    text = PAREN_PATTERN.sub("", text)
    return BRACKET_PATTERN.sub("", text)

# ----------------- Peak extraction from string -----------------
def get_single_peak_from_str(text: str) -> str:
    """Extract the first numeric value (float-like) from a string."""
    if not text:
        return "0"
    
    NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")
    match = NUMBER_PATTERN.search(text)
    if not match:
        return "-999.0"

    peak = match.group(0).rstrip(".")
    if peak.count(".") > 1:
        peak = peak[:peak.rfind(".")]
    return peak

def _clean_nmr_text(text: str) -> str:
    """Normalize text for NMR peak extraction."""
    text = remove_parentheses(text)
    text = text.replace('\n', ' ').replace('cm-1', '').replace('–', '-')
    text = text.replace(', ', ',').replace(',', ', ')
    text = text.strip().rstrip('.')

    if text.endswith('13C'):
        text = text[:-3]

    if 'NMR' in text[:-10]:
        text = text[text.find('NMR') + 3:]
    return text.strip()

def get_peaks_from_text(test_text: str):
    """Extract all peaks (as strings) from an NMR description text."""
    edited_text = _clean_nmr_text(test_text)
    peaks = []

    parts = edited_text.split(',') if ',' in edited_text else [edited_text]
    for part in parts:
        subparts = part.split('-') if '-' in part else [part]
        for sub in subparts:
            peak = get_single_peak_from_str(sub)
            peaks.append(peak)
    return peaks

def _clean_shift_text(shift: str) -> str:
    """Normalize individual NMR shift text."""
    return (
        shift.replace('\n', ' ')
        .replace('cm-1', '')
        .replace('–', '-')
        .replace(', ', ',')
        .replace(',', ', ')
        .strip()
    )

def get_peaks_from_nmrspectrum_dict(nmr_dict, verbose=False):
    """Extract float peaks from a nested NMR spectrum dictionary."""
    peaks = []
    inner_dict = nmr_dict.get('peaks')
    if verbose:
        print('nmr dict', nmr_dict)

    if not inner_dict:
        return peaks

    for shift_dict in inner_dict:
        shift = shift_dict.get('NmrPeak', {}).get('shift', '')
        shift = _clean_shift_text(shift)
        if verbose:
            print('shift', shift)

        if not shift:
            continue

        subparts = shift.split('-') if '-' in shift else [shift]
        for sub in subparts:
            if not sub:
                continue
            try:
                peaks.append(float(sub))
            except ValueError:
                # handle cases like "-0.85" safely
                sub = sub.strip()
                if sub.startswith('-') and sub[1:].replace('.', '', 1).isdigit():
                    peaks.append(float(sub))
                else:
                    peaks.append(-999.0)

    if verbose:
        print('peaks', peaks)
    return peaks

def peak_confusion_matrix(true_peaks, pred_peaks, tol=0.01):
    if len(true_peaks) == 0:
        return 0, 0, 0
    true_peaks = np.array(true_peaks)
    pred_peaks = np.array(pred_peaks)
    matched_true = set()
    matched_pred = set()
    for i, p in enumerate(pred_peaks):
        # Find closest true peak
        diffs = np.abs(true_peaks - p)
        j = np.argmin(diffs)
        if diffs[j] <= tol and j not in matched_true:
            matched_true.add(j)
            matched_pred.add(i)

    TP = len(matched_pred)
    FP = len(pred_peaks) - TP
    FN = len(true_peaks) - TP

    return TP, FP, FN

def hrms_peak_patch(test_text, test_type):
    float_shifts = []
    # if 'HRMS' in test_text or 'ESI' in test_text or 'APCI' in test_text:
    if test_type == 'MS':
        # print('yes HRMS')
        if 'found' in test_text:
            start_idx = test_text.find('found') + 5 
            edited_text = test_text[start_idx:]
            f_peaks = get_peaks_from_text(edited_text)
            if f_peaks:
                float_shifts = [float(peak) for peak in f_peaks]
        else:       
            float_shifts = list(map(float, get_peaks_from_text(test_text)))
    else:
        float_shifts = list(map(float, get_peaks_from_text(test_text)))
    return float_shifts 

def get_peak_score(gt_test_text, test_type, method = 'in_house', sus_test_text='', chemdata_dict=None):
    if gt_test_text in sus_test_text:
        return 1.0, 1.0, 1.0
     
    float_gt_shifts = hrms_peak_patch(gt_test_text, test_type)

    if method == 'in_house':
        float_sus_shifts = hrms_peak_patch(sus_test_text, test_type)
    elif method == 'chemdata':
        float_sus_shifts = get_peaks_from_nmrspectrum_dict(chemdata_dict)
    
    TP, FP, FN = peak_confusion_matrix(float_gt_shifts, float_sus_shifts)

    precision = round(TP / (TP + FP) if (TP + FP) > 0 else 0.0, 2)
    recall = round(TP / (TP + FN) if (TP + FN) > 0 else 0.0, 2)
    f1 = round(2 * precision*recall /(precision + recall) if (precision + recall) > 0 else 0.0, 2)
    # return f1
    return precision, recall, f1

def compare_test_types(gt_test_type, sus_test_type):
    if gt_test_type == '13C NMR':
        if '13C' and 'NMR' in sus_test_type:
            comparison = True
        else:
            comparison = False
    else:
        comparison = gt_test_type == sus_test_type
    return comparison

