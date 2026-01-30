# src/chemsie/pipeline.py
import sys
from pathlib import Path
from typing import List, Any, Tuple
import uuid

from src.chemsie.internal.wrappers import process_doc_pics_first
from src.chemsie.legacy.molecules_tests import ExtractedMolecule
from src.chemsie.schemas import Molecule, Spectrum, Provenance, BoundingBox, ExtractedData, MoleculeProvenance, ExtractionMethod


def _map_old_to_new(old_molecule: ExtractedMolecule) -> Tuple[Molecule, List[Spectrum]]:
    """
    Maps a single legacy ExtractedMolecule object to the new Pydantic Molecule schema
    and associated Spectra.
    This is a temporary adapter layer.
    """
    mol_id = f"mol-{uuid.uuid4()}"
    
    # Create Spectra from the old 'molecule_tests'
    spectra = []
    for test in old_molecule.molecule_tests:
        spectra.append(
            Spectrum(
                type=test.test_type,
                molecule_id=mol_id,
                text_representation=test.test_text,
                peaks=test.peak_list,
                provenance=Provenance(
                    page_number=test.start_page if hasattr(test, 'start_page') else 0, # Fallback
                    bbox=BoundingBox(x0=0, y0=0, x1=0, y1=0), # Placeholder bbox
                    source="text",
                    method=ExtractionMethod(algorithm="legacy_parser", version="1.0", confidence=0.8)
                )
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
            
            provenance = MoleculeProvenance(
                role="structure_image",
                page_number=old_molecule.provenance_segment.page_num,
                bbox=p_bbox,
                source="image",
                confidence=0.9, # Placeholder confidence
                method=ExtractionMethod(algorithm="yode", version="1.0", confidence=0.9)
            )
            provenance_list.append(provenance)
        except (AttributeError, IndexError):
            # If provenance structure is not as expected, skip it.
            pass

    molecule = Molecule(
        id=mol_id,
        smiles=old_molecule.molecule_smiles_by_images, # Prioritizing image-based smiles
        label=old_molecule.molecule_name,
        provenance=provenance_list,
        # The following fields from the new schema are not present in the old model:
        inchi=None, 
    )
    
    return molecule, spectra


def run_extraction(pdf_path: Path) -> ExtractedData:
    """
    The canonical entry point for the ChemSIE extraction pipeline.

    This function takes the path to a PDF file, orchestrates the full
    extraction process, and returns a comprehensive `ExtractedData` object.

    Args:
        pdf_path: The absolute path to the source PDF document.

    Returns:
        A `chemsie.schemas.ExtractedData` object containing all extracted information.
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
    all_molecules = []
    all_spectra = []
    
    for old_mol in old_molecules:
        mol, specs = _map_old_to_new(old_mol)
        all_molecules.append(mol)
        all_spectra.extend(specs)

    return ExtractedData(
        source_filename=pdf_path.name,
        molecules=all_molecules,
        reactions=[], # Not yet extracted by legacy pipeline
        spectra=all_spectra,
        errors=[]
    )
