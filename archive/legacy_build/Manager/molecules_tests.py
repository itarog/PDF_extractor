import os
import numpy as np
import pandas as pd
from copy import copy
# from build.demo_data.inner_validation import compare_values, string_similarity
from experiments.demo_data.inner_validation import hrms_peak_patch, molecule_segment_to_dict_list, get_peaks_from_nmrspectrum_dict, string_similarity

# from build.Streamlit_apps.text_spectra_plotter import parse_carbon_nmr, parse_ms, parse_ir
from build.text_spectra_plotter import (
    plot_proton_nmr, plot_carbon_nmr, plot_ir, plot_ms
)
from src.parsing.spectra import parse_peaks


class GTTest():
    def __init__(self, file_name, molecule_serial, line_dict):
        self.file_name = file_name
        self.molecule_serial = molecule_serial
        self.molecule_name = line_dict.get('molecule_name')
        self.test_type = line_dict.get('test_type')
        self.test_text = line_dict.get('test_text')
        self.peak_list = parse_peaks(self.test_text, self.test_type)

class GTMolecule():
    _counter = 0

    def __init__(self, file_name, molecule_name, molecule_df):
        GTMolecule._counter += 1
        self.file_name = file_name
        self.molecule_name = molecule_name
        self.gt_tests = []
        if 'opsin_smiles' in molecule_df.columns:
            self.opsin_smiles = molecule_df['opsin_smiles'].values[0]
        else:
            self.opsin_smiles = None
        self.build_molecule_from_df(molecule_df)
    
    def build_molecule_from_df(self, molecule_df):
        trans_columns = ['molecule_name', 'test_type', 'test_text']
        mol_dict = molecule_df[trans_columns].T.to_dict()
        itv_result = [{**line_dict, 'line_idx': idx} for idx, line_dict in mol_dict.items()]
        self.gt_tests = [GTTest(self.file_name, self._counter, line_dict) for line_dict in itv_result]

class ExtractedTest():
    def __init__(self, file_name, molecule_serial, extracted_dict):
        self.file_name = file_name
        self.molecule_serial = molecule_serial
        self.molecule_name = extracted_dict.get('molecule_name')
        self.test_type = extracted_dict.get('test_type')
        if '13C' in self.test_type and 'NMR' in self.test_type:
            self.test_type = '13C NMR'
        self.test_text = extracted_dict.get('test_text')
        self.peak_list = parse_peaks(self.test_text, self.test_type)

class ExtractedMolecule():
    _counter = 0

    def __init__(self, file_name = None, molecule_segment = None, loaded_dict = None):
        if loaded_dict is None:
            self.file_name = file_name
            self.provenance_segment = molecule_segment
            molecule_segment_dictlist = molecule_segment_to_dict_list(molecule_segment)
            general_dict = molecule_segment_dictlist[0]
            self.molecule_name = general_dict.get('molecule_name')
            self.molecule_image = general_dict.get('mol_pic')
            self.molecule_smiles_by_images = general_dict.get('mol_pic_smiles')
            self.molecule_smiles_by_name = general_dict.get('molecule_name_smiles') # Smiles 2
            self.molecule_smiles_confidence_score = 0 # Smiles score
            self.molecule_tests = [ExtractedTest(self.file_name, self._counter, inner_dict) for inner_dict in molecule_segment_dictlist]
        else:
            self.provenance_segment = None
            self.file_name = loaded_dict.get('file_name')
            self.molecule_name = loaded_dict.get('molecule_name')
            self.molecule_image = loaded_dict.get('molecule_np_array')
            self.molecule_smiles_by_images = loaded_dict.get('molecule_smiles_by_images')
            self.molecule_smiles_by_name = loaded_dict.get('molecule_name_smiles')
            possible_tests = ['1H NMR', '13C NMR', 'MS', 'IR']
            self.molecule_tests = []
            for test_type in possible_tests:
                test_text = loaded_dict.get(test_type)
                if test_text:
                    try:
                        temp_dict = copy(loaded_dict)
                        temp_dict['test_type'] = test_type
                        temp_dict['test_text'] = test_text
                        self.molecule_tests.append(ExtractedTest(self.file_name, self._counter, temp_dict))
                    except:
                        pass
                        # print('test_text:', test_text)
                        # print('test_type:', test_type)

        if self.molecule_smiles_by_name and self.molecule_smiles_by_images:
            try:
                # gt_smiles is sometimes np.nan for some reason..
                self.molecule_smiles_confidence_score = string_similarity(self.molecule_smiles_by_name, self.molecule_smiles_by_images)
            except:
                self.molecule_smiles_confidence_score = None
        else:
            self.molecule_smiles_confidence_score = None

class ChemDataTest():
    def __init__(self, file_name, molecule_serial, spectrum_dict, test_type=None):
        self.file_name = file_name
        self.molecule_serial = molecule_serial
        self.get_molecule_name(spectrum_dict)
        self.test_type = test_type if test_type else spectrum_dict.get('nucleus') + ' NMR'
        if 'NMR' in self.test_type:
            self.peak_list = get_peaks_from_nmrspectrum_dict(spectrum_dict)
        else:
            self.peak_list = []

    def get_molecule_name(self, spectrum_dict):
        compound_dict = spectrum_dict.get('compound').get('Compound')
        self.molecule_name = ' '.join(compound_dict.get('names', []))
        self.compound_labels = ' '.join(compound_dict.get('labels', []))


class ChemDataMolecule():
    _counter = 0

    def __init__(self, file_name):
        self.file_name = file_name
        self.molecule_name = ''
        self.molecule_names = []
        self.molecule_tests = []

    def save_test(self, spectrum_dict, test_type=None):
        new_test = ChemDataTest(self.file_name, self._counter, spectrum_dict, test_type)
        self.molecule_tests.append(new_test)
        self.molecule_names.append(new_test.molecule_name)
        if len(self.molecule_names)>0:
            self.molecule_name = self.molecule_names[-1]

class TestLogger():
    def __init__(self, test_types):
        self.test_types = test_types
        self.logged_tests = {test_type: [] for test_type in test_types}

    def log_gt_molecule(self, gt_molecule):
        if len(gt_molecule.gt_tests)>0:
            for gt_test in gt_molecule.gt_tests:
                if gt_test.test_type in self.test_types:
                    self.logged_tests[gt_test.test_type].append(gt_test)

    def log_extracted_molecule(self, extracted_molecule):
        if len(extracted_molecule.molecule_tests)>0:
            for extracted_test in extracted_molecule.molecule_tests:
                if extracted_test.test_type in self.test_types:
                    self.logged_tests[extracted_test.test_type].append(extracted_test)

    def sort_log_by_mol_name(self, test_type):
        if test_type in self.test_types:
            test_list = self.logged_tests.get(test_type)
            sorted_test_list = sorted(test_list, key=lambda x: x.molecule_name)
            self.logged_tests[test_type] = sorted_test_list

    def filter_log_by_fname(self, test_type, f_name):
        if test_type in self.test_types:
            test_list = self.logged_tests.get(test_type)
            filtered_molecules = list(filter(lambda x: x.file_name == f_name, test_list))
        else:
            filtered_molecules = []
        return filtered_molecules

    def filter_log_by_peak_range(self, test_type, min_value=None, max_value=None):
        if test_type in self.test_types:
            pass

