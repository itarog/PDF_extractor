import unittest
from .molecule_segment_obj import MoleculeSegment

class TestMoleculeSegment(unittest.TestCase):
    def setUp(self):
        self.segment_lines = [
            (1001, '(1a) Aspirin', (10, 20, 30, 40)),
            (1002, 'This is a test line', (10, 20, 30, 40)),
            (1003, 'Another test line', (10, 20, 30, 40)),
        ]
        self.molecule_segment = MoleculeSegment(self.segment_lines)

    def test_extract_molecule_name(self):
        self.molecule_segment.extract_molecule_name()
        self.assertEqual(self.molecule_segment.molecule_name, 'Aspirin')

    def test_extract_smiles(self):
        self.molecule_segment.molecule_name = 'Aspirin'
        self.molecule_segment.extract_smiles()
        self.assertEqual(self.molecule_segment.molecule_name_smiles, 'CC(=O)OC1=CC=CC=C1C(=O)O')

    def test_repr(self):
        self.molecule_segment.molecule_name = 'Aspirin'
        self.assertEqual(repr(self.molecule_segment), 'Molecule Segment - Aspirin (1:1 to 1:3)')

    def test_str(self):
        self.molecule_segment.molecule_name = 'Aspirin'
        self.assertIn('Molecule Segment - Starting page: 1, Starting line: 1, Ending page: 1, Ending line: 3', str(self.molecule_segment))

if __name__ == '__main__':
    unittest.main()
