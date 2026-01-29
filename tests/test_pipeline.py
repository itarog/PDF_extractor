import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import types

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Mock missing dependencies BEFORE imports
module_names = [
    'yolov5', 
    'yolov5.utils', 
    'yolov5.utils.augmentations', 
    'yolov5.utils.general',
    'yolov5.utils.torch_utils',
    'yolov5.models',
    'yolov5.models.common',
    'yolov5.models.yolo',
    'decimer_segmentation',
    'imantics',
    'DECIMER', # Mock to avoid model download
    # 'tensorflow', # Installed but not mocked to allow other things if needed, but if DECIMER is mocked we are good
    # 'cv2'         # Installed
]

for name in module_names:
    sys.modules[name] = MagicMock()

# Ensure we can import from them
sys.modules['yolov5.utils.augmentations'].letterbox = MagicMock()
sys.modules['yolov5.utils.general'].non_max_suppression = MagicMock()
sys.modules['yolov5.utils.general'].scale_coords = MagicMock()
sys.modules['yolov5.utils.torch_utils'].select_device = MagicMock()
sys.modules['yolov5.models.common'].DetectMultiBackend = MagicMock()
sys.modules['yolov5.models.yolo'].Model = MagicMock()
sys.modules['DECIMER'].predict_SMILES = MagicMock()

from src.chemsie.schemas import Molecule, ExtractedData, Spectrum
from src.chemsie.pipeline import run_extraction, _map_old_to_new

class TestPipeline(unittest.TestCase):
    
    def test_schema_instantiation(self):
        """Test that schemas can be instantiated correctly."""
        mol = Molecule(
            id="test-id",
            smiles="C",
            provenance=[]
        )
        self.assertEqual(mol.id, "test-id")
        self.assertEqual(mol.smiles, "C")
        
    @patch('src.chemsie.pipeline.process_doc_pics_first')
    @patch('src.chemsie.pipeline.ExtractedMolecule')
    def test_run_extraction_mock(self, MockExtractedMolecule, mock_process):
        """Test run_extraction with mocked backend."""
        # Setup mocks
        mock_process.return_value = (["mock_segment"], "mock_clusters")
        
        # Mock the legacy object
        mock_legacy_mol = MagicMock()
        mock_legacy_mol.molecule_smiles_by_images = "C1=CC=CC=C1"
        mock_legacy_mol.molecule_name = "Benzene"
        mock_test = MagicMock()
        mock_test.test_type = "1H NMR"
        mock_test.test_text = "7.2 ppm"
        mock_test.peak_list = [7.2]
        mock_legacy_mol.molecule_tests = [mock_test]
        mock_legacy_mol.provenance_segment = None
        
        MockExtractedMolecule.return_value = mock_legacy_mol
        
        # Create a dummy PDF file path
        dummy_pdf = Path("test.pdf")
        with patch('pathlib.Path.exists', return_value=True):
            result = run_extraction(dummy_pdf)
            
        self.assertIsInstance(result, ExtractedData)
        self.assertEqual(len(result.molecules), 1)
        self.assertEqual(result.molecules[0].smiles, "C1=CC=CC=C1")
        self.assertEqual(result.molecules[0].label, "Benzene")
        self.assertEqual(result.source_filename, "test.pdf")
        self.assertEqual(len(result.spectra), 1)
        self.assertEqual(result.spectra[0].type, "1H NMR")

if __name__ == '__main__':
    unittest.main()
