# src/chemsie/pipeline.py
import sys
from pathlib import Path
from typing import List, Any
import uuid

# --- Temporary Bridge to Old Logic ---
# This sys.path modification is a temporary measure to allow the new pipeline
# to call the old, misplaced logic. It will be removed once the logic is
# fully migrated into the 'chemsie' package.
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from chemsie.internal.wrappers import process_doc_pics_first
from build.Manager.molecules_tests import ExtractedMolecule
from src.chemsie.schemas import Molecule, Spectrum, Provenance, BoundingBox
# --- End of Temporary Bridge ---


def _map_old_to_new(old_molecule: ExtractedMolecule) -> Molecule:
    """
    Maps a single legacy ExtractedMolecule object to the new Pydantic Molecule schema.
    This is a temporary adapter layer.
    """
    
    # Create Spectra from the old 'molecule_tests'
    spectra = []
    for test in old_molecule.molecule_tests:
        spectra.append(
            Spectrum(
                type=test.test_type,
                text_representation=test.test_text,
                peaks=test.peak_list
            )
        )

    # Basic provenance from segment if available
    # This is a placeholder; full provenance mapping requires deeper integration.
    provenance_list = []
    if old_molecule.provenance_segment:
        try:
            # Attempt to extract bbox; structure is assumed
            seg_bbox = old_molecule.provenance_segment.bbox 
            p_bbox = BoundingBox(x0=seg_bbox[0], y0=seg_bbox[1], x1=seg_bbox[2], y1=seg_bbox[3])
            
            provenance = Provenance(
                page_number=old_molecule.provenance_segment.page_num,
                bbox=p_bbox,
                source="image" # Assumption
            )
            provenance_list.append(provenance)
        except (AttributeError, IndexError):
            # If provenance structure is not as expected, skip it.
            pass

    return Molecule(
        id=f"mol-{uuid.uuid4()}", # Generate a new unique ID
        smiles=old_molecule.molecule_smiles_by_images, # Prioritizing image-based smiles
        label=old_molecule.molecule_name,
        provenance=provenance_list,
        # The following fields from the new schema are not present in the old model:
        inchi=None, 
    )


def run_extraction(pdf_path: Path) -> List[Molecule]:
    """
    The canonical entry point for the ChemSIE extraction pipeline.

    This function takes the path to a PDF file, orchestrates the full
    extraction process, and returns a list of validated Pydantic `Molecule`
    objects.

    Args:
        pdf_path: The absolute path to the source PDF document.

    Returns:
        A list of `chemsie.schemas.Molecule` objects, each representing a
        chemical entity found in the document.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    # 1. Call the old, core processing logic.
    # This currently lives in `build/wrappers.py`. We are wrapping, not rewriting.
    # It returns `molecule_segments` and `mol_pic_clusters`.
    molecule_segments, _ = process_doc_pics_first(str(pdf_path), backend='yode', get_smiles=True)

    # 2. Convert the old data structures into `ExtractedMolecule` objects.
    # This mimics the logic from `CHEMSIDB.update_molecule_segments`.
    old_molecules = [ExtractedMolecule(file_name=pdf_path.name, molecule_segment=seg) for seg in molecule_segments]
    
    # 3. Map the old objects to the new, validated Pydantic schemas.
    # This is the critical translation step.
    validated_molecules = [_map_old_to_new(mol) for mol in old_molecules]

    return validated_molecules
