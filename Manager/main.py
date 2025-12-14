from collections import defaultdict
import numpy as np
import pandas as pd

from wrappers import get_filled_matched_molecule_segments, process_doc_list_pics_first
from scoring import score_extracted_gt_data, setup_database, process_gt_extracted_scoring
from molecules_tests import TestLogger, GTMolecule, ExtractedMolecule, ChemDataMolecule
class CHEMSIDB():
    def __init__(self):
        self.all_extracted_molecules = []
        self.all_gt_molecules = []

    def process_gt_data(self, gt_csv_fpath):
        self.gt_data_logger = TestLogger(['1H NMR', '13C NMR', 'MS', 'IR'])
        gt_df = pd.read_csv(gt_csv_fpath)
        fname_groupby = gt_df.groupby('f_name')

        self.all_gt_molecules = []
        self.all_gt_fnames = []
        self.gt_molecules_by_fname = defaultdict(list)
        for f_name, fname_df in fname_groupby:
            f_name = f_name+'.pdf'
            self.all_gt_fnames.append(f_name)
            names_groupby = fname_df.groupby('molecule_name')
            for mol_name, mol_df in names_groupby:
                new_molecule = GTMolecule(f_name, mol_name, mol_df)
                self.gt_data_logger.log_gt_molecule(new_molecule)
                self.gt_molecules_by_fname[f_name].append(new_molecule)
                self.all_gt_molecules.append(new_molecule)

    def process_extracted_data(self, pdf_fpath=None, molecule_segments_dict=None, verbose=False, backend='yode'):
        if molecule_segments_dict:
            self.molecule_segments_dict = molecule_segments_dict
            self.all_extracted_fnames = list(molecule_segments_dict.keys())
            self.extracted_data_logger = TestLogger(['1H NMR', '13C NMR', 'MS', 'IR'])
            self.all_extracted_molecules = []
            self.extracted_molecules_by_fname = defaultdict(list)
            for f_name, (f_segments, m_segments) in molecule_segments_dict.items():
                for molecule_segment in f_segments:
                    new_molecule = ExtractedMolecule(f_name, molecule_segment)
                    self.all_extracted_molecules.append(new_molecule)
                    self.extracted_molecules_by_fname[f_name].append(new_molecule)
                    self.extracted_data_logger.log_extracted_molecule(new_molecule)                    
        if not molecule_segments_dict and pdf_fpath:
            results_dict = process_doc_list_pics_first(input_dir=pdf_fpath, verbose=verbose, backend=backend) # pre_pics_dict=loaded_pics_dict,
            filled_matched_segments_dict = {filename: get_filled_matched_molecule_segments(molecule_segments) for filename, (molecule_segments, *_) in results_dict.items()}
            self.process_extracted_data(filled_matched_segments_dict)

    def setup_database(self, database_name='my_database', graph_sketch=False):
        if hasattr(self, 'molecule_segments_dict'):
            setup_database(self.molecule_segments_dict, database_name=database_name, graph_sketch=graph_sketch)

    def score_extracted_gt_data(self, scores_thers=0.75, allow_unmatched=True, verbose=False):
        self.extracted_gt_scoring = dict() # defaultdict(list)
        # add Number of molecules extracted and efficency
        for gt_fname, gt_molecules in self.gt_molecules_by_fname.items():
            if verbose:
                print(gt_fname)
            extracted_molecules = self.extracted_molecules_by_fname.get(gt_fname)
            if extracted_molecules:
                scores, scores_dict_list, pairwise_molecules = score_extracted_gt_data(gt_molecules, extracted_molecules, scores_thers, allow_unmatched)
                self.extracted_gt_scoring[gt_fname] = {'scores_dist': scores, 'detailed_scores_dist': scores_dict_list, 'paried_molecules': pairwise_molecules}
                if verbose:
                    print('mean score:', np.mean(scores))
                    print('scores_dict_list (len):', len(scores_dict_list))

        summary_details, all_scores_df = process_gt_extracted_scoring(self.extracted_gt_scoring)
        self.gt_extracted_summary_results = summary_details
        self.gt_extracted_scores_df = all_scores_df

    def process_chemdataextractor_data(self, pdf_fpath=None, saved_chemdata_dict=None):
        if saved_chemdata_dict:
            self.saved_chemdata_dict = saved_chemdata_dict
            self.all_chemdata_fnames = list(saved_chemdata_dict.keys())
            self.all_chemdata_molecules = []
            self.chemdata_molecules_by_fname = defaultdict(list)  
            for pdf_fname, indiv_results in saved_chemdata_dict.items():
                for inner_dict in indiv_results:
                    chemdata_molecule = ChemDataMolecule(pdf_fname)
                    records = inner_dict.get('records', [])
                    if records:
                        for inner_record_dict in records:
                            for key in inner_record_dict.keys():              
                                if 'Spectrum' in key:
                                    if key.startswith('Nmr'):
                                        spectrum_dict = inner_record_dict.get('NmrSpectrum')
                                        chemdata_molecule.save_test(spectrum_dict)
                                    elif key.startswith('Ir'):
                                        spectrum_dict = inner_record_dict.get('IrSpectrum')
                                        chemdata_molecule.save_test(spectrum_dict, 'IR')
                    self.all_chemdata_molecules.append(chemdata_molecule)
                    self.chemdata_molecules_by_fname[pdf_fname].append(chemdata_molecule)
        
        elif pdf_fpath:
            pass # requires diff env

    def score_chemdataextractor_gt_data(self, scores_thers=0.75, allow_unmatched=True, verbose=False):
        self.chemdata_gt_scoring = dict() # defaultdict(list)
        # add Number of molecules extracted and efficency
        for gt_fname, gt_molecules in self.gt_molecules_by_fname.items():
            if verbose:
                print(gt_fname)
            chemdata_molecules = self.chemdata_molecules_by_fname.get(gt_fname)
            if chemdata_molecules:
                scores, scores_dict_list, pairwise_molecules = score_extracted_gt_data(gt_molecules, chemdata_molecules, scores_thers, allow_unmatched)
                self.chemdata_gt_scoring[gt_fname] = {'scores_dist': scores, 'detailed_scores_dist': scores_dict_list, 'paried_molecules': pairwise_molecules}
                if verbose:
                    print('mean score:', np.mean(scores))
                    print('scores_dict_list (len):', len(scores_dict_list))

        summary_details, all_scores_df = process_gt_extracted_scoring(self.chemdata_gt_scoring)
        self.gt_chemdata_summary_results = summary_details
        self.gt_chemdata_scores_df = all_scores_df

