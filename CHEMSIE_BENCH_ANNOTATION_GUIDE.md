# ChemSIE-Bench-10 Annotation Guide

## 1. Introduction
This document defines the ground truth specification for **ChemSIE-Bench-10**, a dataset designed to evaluate the extraction of "Experimental Graphs" from chemical PDFs.

## 2. Scope of Annotation
We annotate **Chemical Entities**, **Spectral Data**, and the **Relationships** between them.

### What to Annotate (Required)
*   **Molecules:**
    *   Any distinct chemical structure depicted or described.
    *   **Fields:** `id` (stable), `label` (e.g., "1a"), `smiles` (Canonical), `inchi` (Canonical).
    *   **Provenance:** Page number and BBox of the *structure image*.
*   **NMR Spectra:**
    *   Text blocks describing 1H or 13C NMR data.
    *   **Fields:** `molecule_id` (link to Molecule), `text_representation` (raw string).
    *   **Provenance:** Page number and BBox of the *text block*.

### What to Ignore (Exclusions)
*   Reagents in reaction schemes (unless fully characterized).
*   Solvents (unless relevant to spectral conditions).
*   General body text not containing data.
*   Citations and references.

## 3. Data Format
Annotations must strictly follow the `src/chemsie/schemas.py` `ExtractedData` model.

### JSON Structure
```json
{
  "source_filename": "Benchmark_data_01.pdf",
  "molecules": [
    {
      "id": "mol_1",
      "label": "1",
      "smiles": "C1ccccc1",
      "provenance": [...]
    }
  ],
  "spectra": [
    {
      "type": "1H NMR",
      "molecule_id": "mol_1",
      "text_representation": "1H NMR (400 MHz, CDCl3) ...",
      "provenance": [...]
    }
  ]
}
```

## 4. Quality Control
*   **Chemistry:** Use RDKit to canonicalize SMILES/InChI. Do not guess stereochemistry if ambiguous.
*   **BBoxes:** Tight fit around the visual element.
*   **Linking:** Ensure `molecule_id` in Spectra matches the `id` of the Molecule.

## 5. Candidate Selection Criteria
The 10 documents should represent:
1.  **Diverse Layouts:** Single vs. Double column.
2.  **Diverse Chemistry:** Organic synthesis, Natural products.
3.  **Clean vs. Noisy:** Scanned older PDFs vs. modern born-digital.
