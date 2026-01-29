"""
schemas.py

This module defines the canonical, Pydantic-based data models for the ChemSIE project.
These models are the single source of truth for the structure of data extracted
by the pipeline.

The schema is designed with the following principles:
1.  **Explicitness:** All data structures are explicitly typed.
2.  **Verifiability:** Pydantic enforces the schema at runtime.
3.  **Interoperability:** The models are easily serializable to JSON, not pickle.
4.  **Provenance:** Every piece of extracted data MUST be traceable to its
    exact location (page and bounding box) in the source document. This is not
    optional; it is fundamental to the credibility of the system.
5.  **Decoupling:** Data types are decoupled. A document is a collection of
    Molecules, Reactions, and Spectra, which can be linked by unique IDs rather
    than being nested in a monolithic object.
"""
from typing import List, Tuple, Optional, Union, Literal, Any
from pydantic import BaseModel, Field

# ==============================================================================
# 1. Core Foundational Models
# ==============================================================================

class BoundingBox(BaseModel):
    """
    Defines a bounding box on a page.
    Coordinates are in standard PDF coordinate space (origin at bottom-left).
    """
    x0: float
    y0: float
    x1: float
    y1: float

class Provenance(BaseModel):
    """
    A mandatory record tracking the source of an extracted piece of data.
    This is the key to making the extractor's output verifiable and trustworthy.
    """
    page_number: int = Field(..., description="The page number in the source PDF.")
    bbox: BoundingBox = Field(..., description="The bounding box of the data on the page.")
    source: Literal["text", "image", "table"] = Field(..., description="The modality the data was extracted from.")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="The confidence score of the extractor for this item.")

# ==============================================================================
# 2. Chemical Entity Models
# ==============================================================================

class Molecule(BaseModel):
    """
    Represents a single chemical structure. The core identifier is the InChI,
    as it is more canonical than SMILES.
    """
    id: str = Field(..., description="A unique identifier for this molecule within the document context (e.g., a UUID).")
    smiles: Optional[str] = Field(None, description="The SMILES string for the molecule.")
    inchi: Optional[str] = Field(None, description="The InChI string for the molecule.")
    label: Optional[str] = Field(None, description="The textual label used in the document (e.g., '3a', 'Compound 2').")
    provenance: List[Provenance] = Field(..., description="A list of source locations for this molecule's representation and label.")

# ==============================================================================
# 3. Analytical Data Models
# ==============================================================================

class NMRPeak(BaseModel):
    """Represents a single peak in an NMR spectrum."""
    shift: float = Field(..., description="The chemical shift in ppm.")
    multiplicity: Optional[str] = Field(None, description="e.g., 's', 'd', 't', 'q', 'm'.")
    integration: Optional[float] = Field(None, description="The integration value.")
    coupling_constants: Optional[List[float]] = Field(None, description="List of J-values in Hz.")
    provenance: Provenance

class NMRData(BaseModel):
    """
    Represents extracted Nuclear Magnetic Resonance data.
    """
    id: str = Field(..., description="A unique identifier for this spectral dataset.")
    molecule_id: str = Field(..., description="The ID of the molecule this data characterizes.")
    nucleus: str = Field(..., description="The nucleus, e.g., '1H', '13C'.")
    solvent: Optional[str] = Field(None)
    frequency: Optional[str] = Field(None, description="e.g., '400 MHz'.")
    peaks: List[NMRPeak]
    raw_text: str = Field(..., description="The raw text from which the NMR data was parsed.")
    provenance: Provenance

class Spectrum(BaseModel):
    """
    Generic spectrum model to bridge legacy data.
    """
    type: str = Field(..., description="The type of spectrum (e.g., '1H NMR', 'IR').")
    molecule_id: Optional[str] = Field(None, description="The ID of the molecule this data characterizes.")
    text_representation: Optional[str] = Field(None, description="Raw text representation.")
    peaks: Optional[List[Any]] = Field(None, description="List of peaks.")
    provenance: Optional[Provenance] = None

# Add other spectral data models here as needed (e.g., IRData, MSData) following
# the NMRData pattern.

# ==============================================================================
# 4. Reaction and Experimental Condition Models
# ==============================================================================

class ReactionComponent(BaseModel):
    """A component in a reaction, linking a molecule to its role."""
    molecule_id: str
    role: Literal["reactant", "reagent", "product", "catalyst", "solvent"]

class MeasuredValue(BaseModel):
    """Represents a measured value with units."""
    value: float
    units: str
    provenance: Provenance

class Reaction(BaseModel):
    """
    Represents a chemical reaction, linking components and conditions.
    """
    id: str = Field(..., description="A unique identifier for this reaction.")
    components: List[ReactionComponent]
    yield_value: Optional[MeasuredValue] = None
    temperature: Optional[MeasuredValue] = None
    duration: Optional[MeasuredValue] = None
    provenance: List[Provenance]

# ==============================================================================
# 5. Top-Level Document Model
# ==============================================================================

class ExtractedData(BaseModel):
    """
    The root object for all data extracted from a single source document.
    This is the canonical output of the ChemSIE pipeline. It should be
    serialized to a JSON file.
    """
    source_filename: str
    molecules: List[Molecule]
    reactions: List[Reaction]
    spectra: List[Union[NMRData, Spectrum]] # This can be expanded with IRData, MSData, etc.
    errors: List[str] = Field([], description="A list of errors encountered during processing.")

    class Config:
        title = "ChemSIE Extracted Chemical Data"
        anystr_strip_whitespace = True
        json_schema_extra = {
            "example": {
                "source_filename": "example.pdf",
                "molecules": [
                    {
                        "id": "mol-uuid-1",
                        "smiles": "c1ccccc1",
                        "inchi": "InChI=1S/C6H6/c1-2-4-6-5-3-1/h1-6H",
                        "label": "1",
                        "provenance": [
                            {
                                "page_number": 2,
                                "bbox": {"x0": 100.0, "y0": 200.0, "x1": 150.0, "y1": 250.0},
                                "source": "image",
                                "confidence": 0.98
                            }
                        ]
                    }
                ],
                "reactions": [],
                "spectra": [],
                "errors": []
            }
        }
