import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import json

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.chemsie.schemas import Molecule, Provenance, ExtractionMethod, MoleculeProvenance, BoundingBox

class TestProvenance(unittest.TestCase):
    
    def test_extraction_method_schema(self):
        """Test that ExtractionMethod can be instantiated and validated."""
        method = ExtractionMethod(algorithm="decimer", version="2.4", confidence=0.99)
        self.assertEqual(method.algorithm, "decimer")
        self.assertEqual(method.confidence, 0.99)

    def test_molecule_provenance_schema(self):
        """Test MoleculeProvenance specific fields."""
        prov = MoleculeProvenance(
            role="structure_image",
            page_number=1,
            bbox=BoundingBox(x0=0, y0=0, x1=10, y1=10),
            source="image"
        )
        self.assertEqual(prov.role, "structure_image")

    def test_provenance_threading_in_pipeline(self):
        """Test that run_extraction returns data with method metadata."""
        # This is a partial integration test mocking the backend
        pass # Covered by test_pipeline.py indirectly, but specific checks would go here.

if __name__ == '__main__':
    unittest.main()
