from build.general import get_page_num_and_line_num_from_multi_idx
from build.mol_pic import export_mol_pic
from build.test_text_sequence import export_test_sequence_as_pic

class MoleculeSegment:
    def __init__(self, segment_lines): # segement lines = [(multi_idx, text, bbox = (y0, x0, y1, x1))]
        self.start_multi_idx = segment_lines[0][0]
        self.start_page, self.start_line = get_page_num_and_line_num_from_multi_idx(self.start_multi_idx)
        self.end_multi_idx = segment_lines[-1][0]
        self.end_page, self.end_line = get_page_num_and_line_num_from_multi_idx(self.end_multi_idx)
        self.segment_lines = segment_lines    
        self.upper_y = segment_lines[0][2][0]
        self.lower_y = segment_lines[-1][2][2]
        self.set_default_values()

    def set_default_values(self):
        self.has_test_text_sequence = False
        self.nmr_text_line_list = []
        self.ir_text_line_list = []
        self.rf_text_line_list = []
        self.ms_text_line_list = []
        self.mol_pics = []

    def __repr__(self):
        try:
            text_1 = f'Molecule Segment - Starting page: {self.start_page}, Starting line: {self.start_line}, Ending page: {self.end_page}, Ending line: {self.end_line}\n'
            text_2 = ''
            text_3 = f'Segment_lines:\n'+'\n'.join([line for _, line, _ in self.segment_lines])
            if self.has_test_text_sequence:
                text_2+='Test text sequence'+str(self.test_text_sequence)
                text_3=''
        except:
            text_1, text_2, text_3 = 'molescule segment print failed', '', ''
        return text_1+text_2+text_3

    def __str__(self):
        try:
            text_1 = f'Molecule Segment - Starting page: {self.start_page}, Starting line: {self.start_line}, Ending page: {self.end_page}, Ending line: {self.end_line}\n'
            text_2 = ''
            text_3 = f'Segment_lines:\n'+'\n'.join([line for _, line, _ in self.segment_lines])
            if self.has_test_text_sequence:
                text_2+='Test text sequence - '+str(self.test_text_sequence)
                text_3=''
        except:
            text_1, text_2, text_3 = 'molescule segment print failed', '', ''
        return text_1+text_2+text_3
    
def get_relavent_pages(molecule_segment):
    return list(range(molecule_segment.start_page, molecule_segment.end_page+1))

def export_molecule_segment_results_as_pics(molecule_segment, output_dir):
    molecule_name = molecule_segment.molecule_name
    # segment_text = ' '.join([line [1] for line in molecule_segment.segment_lines])
    saved_filenames, db_entries = export_test_sequence_as_pic(molecule_segment.test_text_sequence, output_dir, molecule_name, font_size=30)
    if molecule_segment.mol_pics:
        mol_pic_path = export_mol_pic(molecule_segment.mol_pics[0], output_dir, molecule_name)
        saved_filenames.append(mol_pic_path) 
    return saved_filenames, db_entries