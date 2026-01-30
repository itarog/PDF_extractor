from typing import List, Tuple
from src.chemsie.utils.general import get_page_num_and_line_num_from_multi_idx
from src.chemsie.internal.mol_pic import export_mol_pic, MolPic
from src.chemsie.internal.test_text_sequence import export_test_sequence_as_pic, TestTextSequence
import re
from .molname_to_SMILES import opsin_query, pubchem_name_to_smiles
from DECIMER import predict_SMILES
import logging

logger = logging.getLogger(__name__)


class Spectra:
    def __init__(self, type: str, text_lines: List[str]):
        self.type = type
        self.text_lines = text_lines

    def __repr__(self):
        return f"Spectra(type='{self.type}', lines={len(self.text_lines)})"


class MoleculeSegment:
    def __init__(self, segment_lines: List[Tuple[int, str, Tuple[float, float, float, float]]]):
        self.segment_lines: List[Tuple[int, str, Tuple[float, float, float, float]]] = segment_lines
        self.start_multi_idx: int = segment_lines[0][0]
        self.start_page, self.start_line = get_page_num_and_line_num_from_multi_idx(self.start_multi_idx)
        self.end_multi_idx: int = segment_lines[-1][0]
        self.end_page, self.end_line = get_page_num_and_line_num_from_multi_idx(self.end_multi_idx)
        self.upper_y: float = segment_lines[0][2][0]
        self.lower_y: float = segment_lines[-1][2][2]

        self.molecule_name: str = ""
        self.molecule_name_smiles: str = ""
        self.mol_pic_smiles: str = ""
        self.has_test_text_sequence: bool = False
        self.test_text_sequence: TestTextSequence = None
        self.spectra: List[Spectra] = []
        self.mol_pics: List[MolPic] = []

    def __repr__(self):
        return f'Molecule Segment - {self.molecule_name} ({self.start_page}:{self.start_line} to {self.end_page}:{self.end_line})'

    def __str__(self):
        text_1 = f'Molecule Segment - Starting page: {self.start_page}, Starting line: {self.start_line}, Ending page: {self.end_page}, Ending line: {self.end_line}\n'
        text_2 = ''
        text_3 = f'Segment_lines:\n' + '\n'.join([line for _, line, _ in self.segment_lines])
        if self.has_test_text_sequence:
            text_2 += 'Test text sequence - ' + str(self.test_text_sequence)
            text_3 = ''
        return text_1 + text_2 + text_3

    def extract_molecule_name(self, num_lines_to_check: int = 3):
        """Extracts molecule name from the segment text."""
        logger.debug(f"Extracting molecule name from segment: {self}")
        for num_lines in range(1, num_lines_to_check + 1):
            if num_lines <= len(self.segment_lines):
                text = ''.join(line for _, line, _ in self.segment_lines[:num_lines])
                name = self._search_molecule_name(text)
                if name:
                    self.molecule_name = self._clean_molecule_name(name)
                    logger.debug(f"Found molecule name: {self.molecule_name}")
                    return

        # Fallback to first line
        self.molecule_name = self._clean_molecule_name(self.segment_lines[0][1])
        logger.debug(f"No specific name found, using first line: {self.molecule_name}")

    def _search_molecule_name(self, text: str) -> str:
        mol_tag = self._find_mol_tag(text)
        if mol_tag:
            full_tag = '(' + mol_tag + ')'
            end_idx = text.find(full_tag)
            return text[:end_idx].strip()
        return ""

    def _find_mol_tag(self, text: str) -> str:
        pattern = r'\((\d+[a-zA-Z]?)\)'
        matches = re.findall(pattern, text)
        return matches[0] if matches else ""

    def _clean_molecule_name(self, molecule_name: str, replacement=' ') -> str:
        invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
        cleaned_molecule_name = re.sub(invalid_chars, replacement, molecule_name)
        return cleaned_molecule_name.strip(" .")

    def extract_smiles(self, smiles_cache: dict = {}):
        """Extracts SMILES from molecule name and picture."""
        logger.debug(f"Extracting SMILES for: {self.molecule_name}")
        if self.molecule_name in smiles_cache:
            self.molecule_name_smiles = smiles_cache[self.molecule_name]
            logger.debug(f"Found SMILES in cache: {self.molecule_name_smiles}")
            return

        # From name
        smiles = ''
        try:
            info = opsin_query(self.molecule_name)
            smiles = info.get('smiles', '')
            logger.debug(f"Opsin query for '{self.molecule_name}' returned: {smiles}")
        except Exception as e:
            logger.warning(f"Opsin query failed for '{self.molecule_name}': {e}")

        if not smiles:
            try:
                smiles = pubchem_name_to_smiles(self.molecule_name)
                logger.debug(f"PubChem query for '{self.molecule_name}' returned: {smiles}")
            except Exception as e:
                logger.warning(f"PubChem query failed for '{self.molecule_name}': {e}")

        self.molecule_name_smiles = smiles
        smiles_cache[self.molecule_name] = smiles

        # From picture
        if self.mol_pics:
            mol_pic = self.mol_pics[0]
            try:
                self.mol_pic_smiles = predict_SMILES(mol_pic.pic)
                logger.debug(f"SMILES from picture: {self.mol_pic_smiles}")
            except Exception as e:
                logger.warning(f"SMILES prediction from picture failed: {e}")


def get_relavent_pages(molecule_segment: MoleculeSegment) -> List[int]:
    return list(range(molecule_segment.start_page, molecule_segment.end_page + 1))


def export_molecule_segment_results_as_pics(molecule_segment: MoleculeSegment, output_dir: str):
    molecule_name = molecule_segment.molecule_name
    saved_filenames, db_entries = export_test_sequence_as_pic(molecule_segment.test_text_sequence, output_dir,
                                                              molecule_name, font_size=30)
    if molecule_segment.mol_pics:
        mol_pic_path = export_mol_pic(molecule_segment.mol_pics[0], output_dir, molecule_name)
        saved_filenames.append(mol_pic_path)
    return saved_filenames, db_entries